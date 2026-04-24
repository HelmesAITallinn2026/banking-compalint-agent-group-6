#!/usr/bin/env python3
"""
End-to-end smoke test for the banking complaint agent pipeline.

Runs three scenarios (one per mortgage refusal reason) against a live server.
Set BASE_URL env var if the server isn't on http://localhost:8000.

Usage:
    cd agent
    uv run python run_e2e_test.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
MOCK_DOCS = Path(__file__).resolve().parent.parent / "mock_docs"

SALARY_PDF = MOCK_DOCS / "helmes_bank_salary_statement.pdf"
TRANSACTION_PDF = MOCK_DOCS / "helmes_bank_transaction_history.pdf"
IRRELEVANT_PDF = MOCK_DOCS / "DEFINITELY-NOT-INCOME-STATEMENT.pdf"

# --- colour / emoji helpers --------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"


def hdr(text: str) -> None:
    width = 72
    print()
    print(BOLD + CYAN + "═" * width + RESET)
    print(BOLD + CYAN + f"  {text}" + RESET)
    print(BOLD + CYAN + "═" * width + RESET)


def section(emoji: str, title: str) -> None:
    print()
    print(BOLD + BLUE + f"{emoji}  {title}" + RESET)
    print(DIM + "─" * 60 + RESET)


def ok(msg: str) -> None:
    print(GREEN + f"  ✅  {msg}" + RESET)


def info(msg: str) -> None:
    print(CYAN + f"  ℹ️   {msg}" + RESET)


def warn(msg: str) -> None:
    print(YELLOW + f"  ⚠️   {msg}" + RESET)


def err(msg: str) -> None:
    print(RED + f"  ❌  {msg}" + RESET)


def kv(key: str, value: str) -> None:
    print(f"  {BOLD}{key}:{RESET} {value}")


def box(label: str, content: str, colour: str = DIM) -> None:
    print(f"  {BOLD}{label}:{RESET}")
    for line in content.strip().splitlines():
        print(colour + "    │ " + line + RESET)


def separator() -> None:
    print(DIM + "  " + "·" * 58 + RESET)


# --- HTTP helpers ------------------------------------------------------------

def check_server() -> None:
    section("🔌", "Checking server health")
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=5)
        r.raise_for_status()
        data = r.json()
        ok(f"Server is UP at {BASE_URL}")
        kv("DB path", data.get("database_path", "?"))
    except Exception as exc:
        err(f"Cannot reach server: {exc}")
        print()
        print(RED + "  Start the server first:" + RESET)
        print("    cd agent && uv run uvicorn main:app --reload")
        sys.exit(1)


def submit_complaint(
    first_name: str,
    last_name: str,
    subject: str,
    message: str,
    refusal_reason: str | None,
    doc_path: Path | None,
) -> str:
    files: list = []
    opened = []
    if doc_path and doc_path.exists():
        fh = open(doc_path, "rb")
        opened.append(fh)
        files = [("files", (doc_path.name, fh, "application/pdf"))]

    data: dict = {
        "first_name": first_name,
        "last_name": last_name,
        "subject": subject,
        "message": message,
    }
    if refusal_reason:
        data["refusal_reason"] = refusal_reason

    try:
        r = httpx.post(
            f"{BASE_URL}/complaint-form",
            data=data,
            files=files if files else None,
            timeout=30,
        )
    finally:
        for fh in opened:
            fh.close()

    if r.status_code != 200:
        err(f"Submit failed: HTTP {r.status_code}")
        box("Response body", r.text, RED)
        raise RuntimeError("Submit failed")

    body = r.json()
    return body["complaint_id"]


def poll_until_ready(complaint_id: str, terminal_statuses: set[str], max_wait: int = 300) -> dict:
    """Poll GET /complaints/{id} until status reaches a terminal value."""
    start = time.time()
    deadline = start + max_wait
    last_status = None
    tick = 0

    while time.time() < deadline:
        elapsed = int(time.time() - start)
        try:
            r = httpx.get(f"{BASE_URL}/complaints/{complaint_id}", timeout=10)
        except httpx.RequestError:
            time.sleep(3)
            continue
        if r.status_code != 200:
            time.sleep(2)
            continue
        data = r.json()
        status = data.get("status", "")

        if status != last_status:
            if tick:
                print()
            last_status = status
            _print_status_transition(status, data)
            tick = 0

        if status in terminal_statuses:
            return data

        tick += 1
        # Show elapsed time every 5 ticks (~15s) so user knows we're alive
        if tick % 5 == 0:
            print(DIM + f"\r  ⏳ Still waiting… ({elapsed}s elapsed, max {max_wait}s)" + RESET, end="", flush=True)
        else:
            print(DIM + "." + RESET, end="", flush=True)
        time.sleep(3)

    if tick:
        print()
    elapsed = int(time.time() - start)
    warn(f"Timed out after {elapsed}s (max {max_wait}s) — last status: {last_status}")
    warn("The pipeline may still be running. Try fetching the complaint manually:")
    warn(f"  curl {BASE_URL}/complaints/{complaint_id}")
    return {}


def _print_status_transition(status: str, data: dict) -> None:
    icons = {
        "submitted": "📥",
        "data_extracted": "🔬",
        "categorised": "🗂️",
        "recommendation_ready": "💡",
        "draft_created": "✍️",
        "completed": "🏁",
    }
    icon = icons.get(status, "🔄")
    print(f"\n  {icon} Status → {BOLD}{MAGENTA}{status}{RESET}")

    if status == "data_extracted" and data.get("extracted_data"):
        try:
            extracted = json.loads(data["extracted_data"]) if isinstance(data["extracted_data"], str) else data["extracted_data"]
            separator()
            print(f"  {BOLD}Extracted fields:{RESET}")
            for key, val in extracted.items():
                if val not in (None, "", [], False):
                    kv(f"    {key}", str(val))
        except Exception:
            pass

    if status == "categorised" and data.get("category"):
        separator()
        kv("  Category", data["category"])

    if status == "recommendation_ready":
        separator()
        kv("  Recommendation", BOLD + (data.get("recommendation") or "—") + RESET)
        if data.get("recommendation_reasoning"):
            box("  Reasoning", data["recommendation_reasoning"], YELLOW)


def print_agent_logs(logs: list[dict], seen_ids: set) -> set:
    new_ids = set()
    for i, log in enumerate(logs):
        uid = (log.get("agent_name"), log.get("action_type"), log.get("created_at"))
        if uid in seen_ids:
            continue
        new_ids.add(uid)
        agent = log.get("agent_name", "?")
        action = log.get("action_type", "?")
        reasoning = log.get("reasoning_process") or ""
        output_raw = log.get("output_context") or "{}"

        agent_icons = {
            "extraction_agent": "🔬",
            "categorization_agent": "🗂️",
            "data_retrieval_agent": "📊",
            "drafting_agent": "✍️",
        }
        icon = agent_icons.get(agent, "🤖")

        print(f"\n  {icon} {BOLD}[{agent}]{RESET} → {CYAN}{action}{RESET}")
        if reasoning and reasoning not in ("Extraction agent started.", "Categorization agent started.",
                                           "Data retrieval agent started.", "Drafting agent started.",
                                           "Extraction agent completed successfully.",
                                           "Categorization agent completed successfully.",
                                           "Data retrieval agent completed successfully.",
                                           "Drafting agent completed successfully."):
            box("  Agent reasoning", reasoning, DIM)

        try:
            output = json.loads(output_raw) if isinstance(output_raw, str) else output_raw
            if output and output != {}:
                # Show meaningful output fields
                for key, val in output.items():
                    if key == "agent_output" and isinstance(val, str) and val.strip():
                        box("  Agent output", val[:600] + ("…" if len(val) > 600 else ""), CYAN)
                    elif key not in ("agent_output",) and val not in (None, "", [], {}):
                        kv(f"    {key}", str(val)[:200])
        except Exception:
            pass

    return seen_ids | new_ids


def trigger_draft(complaint_id: str, decision: str, refusal_reason: str | None) -> None:
    payload = {
        "complaint_id": complaint_id,
        "decision": decision,
        "refusal_reason": refusal_reason,
    }
    r = httpx.post(f"{BASE_URL}/draft-response", json=payload, timeout=15)
    if r.status_code != 200:
        err(f"Draft trigger failed: HTTP {r.status_code} — {r.text}")
        raise RuntimeError("Draft trigger failed")
    ok("Draft triggered — waiting for drafting agent…")


def print_draft(draft: str) -> None:
    section("📬", "Final Draft Response Letter")
    lines = draft.strip().splitlines()
    for line in lines:
        print(GREEN + "  " + line + RESET)


# --- Scenarios ---------------------------------------------------------------

SCENARIOS = [
    {
        "label": "Mortgage rejection — not_enough_income",
        "emoji": "💰",
        "first_name": "Anna",
        "last_name": "Kowalski",
        "subject": "Mortgage application rejected due to income",
        "message": (
            "I recently applied for a mortgage at Helmes Bank and was rejected "
            "because of insufficient income. My monthly salary is 2400 EUR but "
            "the bank requires 3200 EUR. I believe my financial situation is "
            "stable enough and I would like to formally contest this decision."
        ),
        "refusal_reason": "not_enough_income",
        "doc": SALARY_PDF,
        "decision": "NEGATIVE",
    },
    {
        "label": "Mortgage rejection — not_enough_transactions",
        "emoji": "📊",
        "first_name": "Piotr",
        "last_name": "Nowak",
        "subject": "Mortgage denied — transaction history insufficient",
        "message": (
            "My mortgage application was turned down because the bank claims I "
            "don't have enough eligible transactions in my account history. "
            "I have been a customer for two years and regularly receive salary "
            "payments. I am requesting a formal review of this decision."
        ),
        "refusal_reason": "not_enough_transactions",
        "doc": TRANSACTION_PDF,
        "decision": "NEGATIVE",
    },
    {
        "label": "Mortgage rejection — wrong_or_incomplete_documents",
        "emoji": "📄",
        "first_name": "Maria",
        "last_name": "Wisniewska",
        "subject": "Mortgage rejected — document issues",
        "message": (
            "I was told my mortgage application was rejected because of wrong "
            "or incomplete documents. I thought I had submitted everything "
            "required but apparently my salary statement and bank statement "
            "were missing. Please clarify what exactly is needed."
        ),
        "refusal_reason": "wrong_or_incomplete_documents",
        "doc": IRRELEVANT_PDF,
        "decision": "NEGATIVE",
    },
]


def run_scenario(scenario: dict, index: int, total: int) -> bool:
    label = scenario["label"]
    emoji = scenario["emoji"]
    refusal_reason = scenario["refusal_reason"]

    hdr(f"Scenario {index}/{total}: {emoji}  {label}")

    # ── 1. Submit ────────────────────────────────────────────────────────────
    section("📤", "Submitting complaint form")
    kv("Name", f"{scenario['first_name']} {scenario['last_name']}")
    kv("Subject", scenario["subject"])
    kv("Refusal reason", refusal_reason)
    kv("Attached doc", scenario["doc"].name if scenario["doc"] else "none")
    print(DIM + f"\n  Message preview: {scenario['message'][:120]}…" + RESET)

    try:
        complaint_id = submit_complaint(
            first_name=scenario["first_name"],
            last_name=scenario["last_name"],
            subject=scenario["subject"],
            message=scenario["message"],
            refusal_reason=refusal_reason,
            doc_path=scenario["doc"],
        )
    except RuntimeError:
        return False

    ok(f"Complaint submitted!")
    kv("Complaint ID", BOLD + complaint_id + RESET)

    # ── 2. Poll until recommendation_ready (or draft_created for early exit) ─
    section("🔄", "Pipeline running — polling for agent progress")
    info("Agents are working… (polling every 3s, max 300s per stage)")

    seen_log_ids: set = set()

    terminal_for_pipeline = {"recommendation_ready", "draft_created", "completed"}
    data = {}
    start = time.time()
    deadline = time.time() + 300
    last_status = None
    tick = 0

    while time.time() < deadline:
        elapsed = int(time.time() - start)
        try:
            r = httpx.get(f"{BASE_URL}/complaints/{complaint_id}", timeout=10)
        except httpx.RequestError:
            time.sleep(3)
            continue
        if r.status_code != 200:
            time.sleep(2)
            continue

        data = r.json()
        status = data.get("status", "")
        logs = data.get("logs", [])

        # Print new agent log entries as they arrive
        seen_log_ids = print_agent_logs(logs, seen_log_ids)

        if status != last_status:
            last_status = status
            _print_status_transition(status, data)
            tick = 0

        if status in terminal_for_pipeline:
            break

        tick += 1
        if tick % 5 == 0:
            print(DIM + f"\r  ⏳ Still waiting… ({elapsed}s elapsed)" + RESET, end="", flush=True)
        else:
            print(DIM + "." + RESET, end="", flush=True)
        time.sleep(3)
    else:
        elapsed = int(time.time() - start)
        print()
        err(f"Pipeline timed out after {elapsed}s — last status: {last_status}")
        warn(f"The pipeline may still be running. Check manually:")
        warn(f"  curl {BASE_URL}/complaints/{complaint_id}")
        return False

    status = data.get("status", "") if data else ""

    # Early-exit path (wrong_or_incomplete_documents) goes straight to draft_created
    if status == "draft_created":
        section("⚡", "Early-exit path taken (documents incomplete → straight to draft)")
        if data.get("draft_response"):
            print_draft(data["draft_response"])
        return True

    if status != "recommendation_ready":
        warn(f"Expected recommendation_ready but got: {status}")
        return False

    # ── 3. Human review simulation ───────────────────────────────────────────
    section("👤", "Simulating human review")
    recommendation = data.get("recommendation", "NEGATIVE")
    reasoning = data.get("recommendation_reasoning", "")
    kv("System recommendation", BOLD + recommendation + RESET)
    if reasoning:
        box("Reasoning", reasoning[:400] + ("…" if len(reasoning) > 400 else ""), YELLOW)

    decision = scenario["decision"]
    info(f"Human decision: {BOLD}{decision}{RESET} (following system recommendation for demo)")

    # ── 4. Trigger drafting ──────────────────────────────────────────────────
    section("✍️", "Triggering drafting agent")
    try:
        trigger_draft(complaint_id, decision, refusal_reason)
    except RuntimeError:
        return False

    # ── 5. Poll for draft ────────────────────────────────────────────────────
    draft_data = poll_until_ready(complaint_id, {"draft_created", "completed"}, max_wait=90)

    if not draft_data:
        warn("Drafting timed out or returned no data")
        return False

    # Print any new logs from drafting agent
    seen_log_ids = print_agent_logs(draft_data.get("logs", []), seen_log_ids)

    # ── 6. Show the draft ────────────────────────────────────────────────────
    draft = draft_data.get("draft_response") or ""
    if draft:
        print_draft(draft)
    else:
        warn("No draft response found in complaint record")

    section("🏁", "Scenario complete")
    ok(f"Complaint {complaint_id} — final status: {draft_data.get('status', '?')}")
    return True


# --- Main --------------------------------------------------------------------

def main() -> None:
    print()
    print(BOLD + MAGENTA + "╔══════════════════════════════════════════════════════════════╗" + RESET)
    print(BOLD + MAGENTA + "║  🏦  Helmes Bank — Mortgage Complaint Agent  E2E Test Runner  ║" + RESET)
    print(BOLD + MAGENTA + "╚══════════════════════════════════════════════════════════════╝" + RESET)
    print(DIM + f"  Server: {BASE_URL}" + RESET)

    check_server()

    results: list[tuple[str, bool]] = []

    for i, scenario in enumerate(SCENARIOS, start=1):
        success = run_scenario(scenario, i, len(SCENARIOS))
        results.append((scenario["label"], success))
        if i < len(SCENARIOS):
            print()
            input(DIM + "  ↵  Press Enter to run next scenario…" + RESET)

    # ── Summary ───────────────────────────────────────────────────────────────
    hdr("📋  Test Run Summary")
    all_pass = True
    for label, success in results:
        if success:
            ok(label)
        else:
            err(label)
            all_pass = False

    print()
    if all_pass:
        print(BOLD + GREEN + "  🎉  All scenarios passed!" + RESET)
    else:
        print(BOLD + RED + "  💥  Some scenarios failed — check output above." + RESET)
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
