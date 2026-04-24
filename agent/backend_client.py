"""HTTP client that replaces database.py — all data flows through the Spring Boot backend."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# Maps agent status enum values to backend complaint_status table IDs
STATUS_MAP = {
    "submitted": 1,
    "data_extracted": 2,
    "categorised": 3,
    "recommendation_ready": 4,
    "draft_created": 5,
    "completed": 6,
}

UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(base_url=BACKEND_URL, timeout=30.0)
    return _client


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_complaint_by_id(complaint_id: str | int) -> dict | None:
    """Fetch complaint detail from backend, mapped to the dict shape agents expect."""
    client = _get_client()
    resp = client.get(f"/api/complaints/{complaint_id}/agent-detail")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    d = resp.json()

    # Map backend field names → agent field names
    attachments = d.get("attachments") or []
    files = []
    for a in attachments:
        local_path = _download_attachment(a["id"], a.get("fileName", "file"))
        files.append({
            "id": a["id"],
            "original_filename": a.get("fileName", ""),
            "stored_path": local_path,
            "content_type": a.get("mimeType"),
            "created_at": "",
        })

    return {
        "id": str(d["id"]),
        "first_name": d.get("firstName", ""),
        "last_name": d.get("lastName", ""),
        "subject": d.get("subject", ""),
        "message": d.get("text", ""),
        "refusal_reason": d.get("refusalReason"),
        "status": d.get("status", ""),
        "category": d.get("category"),
        "recommendation": d.get("recommendation"),
        "recommendation_reasoning": d.get("recommendationReasoning"),
        "draft_response": d.get("draftEmailBody"),
        "extracted_data": d.get("extractedData"),
        "created_at": str(d.get("createdDttm", "")),
        "updated_at": str(d.get("updatedDttm", "")),
        "files": files,
        "logs": [],
    }


def _download_attachment(attachment_id: int, file_name: str) -> str:
    """Download an attachment from backend and cache locally. Returns local path."""
    local_path = UPLOADS_DIR / f"{attachment_id}_{file_name}"
    if local_path.exists():
        return str(local_path)
    client = _get_client()
    resp = client.get(f"/api/attachments/{attachment_id}/file")
    resp.raise_for_status()
    local_path.write_bytes(resp.content)
    logger.info("Downloaded attachment %s → %s", attachment_id, local_path)
    return str(local_path)


# ---------------------------------------------------------------------------
# Write — all go through PATCH /api/complaints/{id}/agent-update
# ---------------------------------------------------------------------------

def _agent_update(complaint_id: str | int, payload: dict) -> None:
    client = _get_client()
    resp = client.patch(f"/api/complaints/{complaint_id}/agent-update", json=payload)
    resp.raise_for_status()


async def update_complaint_status(complaint_id: str | int, status: str) -> None:
    status_id = STATUS_MAP.get(status)
    if status_id is None:
        logger.warning("Unknown status '%s', skipping update", status)
        return
    _agent_update(complaint_id, {"statusId": status_id})


async def save_extracted_data(complaint_id: str | int, extracted_data_json: str) -> None:
    _agent_update(complaint_id, {
        "extractedData": extracted_data_json,
        "statusId": STATUS_MAP["data_extracted"],
    })


async def save_categorization(complaint_id: str | int, category: str) -> None:
    _agent_update(complaint_id, {
        "category": category,
        "statusId": STATUS_MAP["categorised"],
    })


async def save_recommendation(
    complaint_id: str | int, category: str, recommendation: str, reasoning: str,
) -> None:
    _agent_update(complaint_id, {
        "category": category,
        "recommendation": recommendation,
        "recommendationReasoning": reasoning,
        "statusId": STATUS_MAP["recommendation_ready"],
    })


async def save_draft_response(complaint_id: str | int, draft_response: str) -> None:
    # Split into subject (first line) and body
    lines = draft_response.strip().split("\n", 1)
    subject = lines[0][:255] if lines else "Complaint Response"
    body = draft_response
    _agent_update(complaint_id, {
        "draftEmailSubject": subject,
        "draftEmailBody": body,
        "statusId": STATUS_MAP["draft_created"],
    })


# ---------------------------------------------------------------------------
# Agent logs
# ---------------------------------------------------------------------------

async def create_agent_log(
    complaint_id: str | int,
    agent_name: str,
    action_type: str,
    input_context,
    reasoning_process: str,
    output_context,
) -> None:
    client = _get_client()
    payload = {
        "agentName": agent_name,
        "actionType": action_type,
        "inputContext": json.dumps(input_context) if not isinstance(input_context, str) else input_context,
        "reasoningProcess": reasoning_process,
        "outputContext": json.dumps(output_context) if not isinstance(output_context, str) else output_context,
    }
    try:
        resp = client.post(f"/api/complaints/{complaint_id}/agent-logs", json=payload)
        resp.raise_for_status()
    except Exception:
        logger.exception("Failed to push agent log for complaint %s", complaint_id)
