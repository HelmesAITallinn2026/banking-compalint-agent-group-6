from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from backend_client import create_agent_log, get_complaint_by_id, save_categorization as _save_cat, update_complaint_status
from mortgage_rules import SUPPORTED_MORTGAGE_REFUSAL_REASONS
from schemas import ComplaintStatus
from tracing import get_langfuse_handler, observe

COMPLAINT_TREE_PATH = Path(__file__).resolve().parent / "complaint_tree.json"


def _build_chat_model(model_name: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name or os.getenv("CATEGORIZATION_MODEL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0,
        model_kwargs={"extra_body": {"usage": {"include": True}}},
    )


@tool
def load_complaint_tree() -> str:
    """Load the complaint category tree with all categories and subcategories."""
    data = json.loads(COMPLAINT_TREE_PATH.read_text(encoding="utf-8"))
    tree = data["complaint_tree"]
    lines: list[str] = []
    for category, info in tree.items():
        lines.append(f"Category: {category}")
        lines.append(f"  Description: {info['description']}")
        for sub, desc in info["subcategories"].items():
            lines.append(f"  - {sub}: {desc}")
        lines.append("")
    return "\n".join(lines)


@tool
def save_categorization(complaint_id: str, category: str, subcategory: str, reasoning: str) -> dict:
    """Save the categorization result for a complaint. Call this after deciding the category."""

    async def _save() -> None:
        full_category = f"{category} > {subcategory}"
        await _save_cat(complaint_id, full_category)
        await create_agent_log(
            complaint_id,
            "categorization_agent",
            "save_categorization",
            {"complaint_id": complaint_id, "category": category, "subcategory": subcategory},
            reasoning,
            {"full_category": full_category},
        )

    asyncio.run(_save())
    return {"status": "success", "complaint_id": complaint_id, "category": f"{category} > {subcategory}"}


SYSTEM_PROMPT = """You are a Categorization Agent responsible for classifying banking complaints.

Your job is to:
1. Load the complaint category tree using `load_complaint_tree`
2. Analyze the complaint data provided
3. Pick the single best matching category and subcategory from the tree
4. Save the categorization using `save_categorization` with your reasoning

Rules:
- ALWAYS start by calling `load_complaint_tree` to see available categories
- Choose exactly one category and one subcategory
- If no subcategory fits well, use the closest match or fall back to "Other > General Banking Complaint"
- Provide clear reasoning for your choice
- ALWAYS call `save_categorization` before finishing
- Do not skip steps or invent tool results
"""

TOOLS = [load_complaint_tree, save_categorization]


def _build_agent():
    return create_agent(
        model=_build_chat_model(),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def _stringify_message_content(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()
    return str(content)


@observe(name="categorization-agent")
async def run_categorization_agent(complaint_id: str):
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found")

    await create_agent_log(
        complaint_id,
        "categorization_agent",
        "start_processing",
        {"complaint_id": complaint_id},
        "Categorization agent started.",
        {},
    )

    input_text = (
        f"Complaint ID: {complaint_id}\n"
        f"Customer: {complaint['first_name']} {complaint['last_name']}\n"
        f"Subject: {complaint['subject']}\n"
        f"Message: {complaint['message']}\n"
    )

    extracted_data = complaint.get("extracted_data")
    if extracted_data:
        input_text += f"\nExtracted Data:\n{extracted_data}\n"

    if complaint.get("refusal_reason") in SUPPORTED_MORTGAGE_REFUSAL_REASONS:
        input_text += (
            "\nThis complaint is a mortgage-decision complaint. "
            "Prefer Loan Complaints > Mortgage Application Rejection unless the complaint text clearly contradicts that.\n"
        )

    agent = _build_agent()
    handler = get_langfuse_handler(complaint_id)
    invoke_config = {"callbacks": [handler]} if handler else {}
    result = await asyncio.to_thread(
        agent.invoke,
        {"messages": [{"role": "user", "content": input_text}]},
        invoke_config,
    )

    await update_complaint_status(complaint_id, ComplaintStatus.categorised)

    messages = result.get("messages", [])
    final_output = _stringify_message_content(messages[-1]) if messages else ""
    await create_agent_log(
        complaint_id,
        "categorization_agent",
        "completed",
        {"complaint_id": complaint_id},
        "Categorization agent completed successfully.",
        {"agent_output": final_output},
    )

    return result
