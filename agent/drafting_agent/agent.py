from __future__ import annotations

import asyncio
import json
import os

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from backend_client import create_agent_log, get_complaint_by_id, save_draft_response, update_complaint_status
from mortgage_rules import SUPPORTED_MORTGAGE_REFUSAL_REASONS, get_mortgage_drafting_guidance
from schemas import ComplaintStatus
from tracing import get_langfuse_handler, observe


def _build_chat_model(model_name: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name or os.getenv("DRAFTING_MODEL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0.3,
        model_kwargs={"extra_body": {"usage": {"include": True}}},
    )


@tool
def load_complaint_context(complaint_id: str) -> str:
    """Load the full complaint record from the database for drafting a response."""

    async def _load():
        return await get_complaint_by_id(complaint_id)

    complaint = asyncio.run(_load())
    if not complaint:
        return f"Complaint {complaint_id} not found."

    return (
        f"Customer Name: {complaint.get('first_name', '')} {complaint.get('last_name', '')}\n"
        f"Subject: {complaint.get('subject', '')}\n"
        f"Message: {complaint.get('message', '')}\n"
        f"Refusal Reason: {complaint.get('refusal_reason', 'N/A')}\n"
        f"Extracted Data: {json.dumps(complaint.get('extracted_data', {}))}\n"
        f"Category: {complaint.get('category', 'N/A')}\n"
        f"Recommendation: {complaint.get('recommendation', 'N/A')}\n"
        f"Recommendation Reasoning: {complaint.get('recommendation_reasoning', 'N/A')}\n"
    )


@tool
def save_draft(complaint_id: str, draft_text: str) -> dict:
    """Save the drafted response letter to the complaint record."""

    async def _save():
        await save_draft_response(complaint_id, draft_text)
        await create_agent_log(
            complaint_id,
            "drafting_agent",
            "save_draft",
            {"complaint_id": complaint_id},
            "Saved draft response letter to DB.",
            {"draft_length": len(draft_text)},
        )

    asyncio.run(_save())
    return {"status": "success", "complaint_id": complaint_id}


SYSTEM_PROMPT = """You are a Message Drafting Agent for a bank's complaint processing system.

Your job is to draft a formal, professional response letter to the customer regarding their complaint.

Steps:
1. Load the full complaint context
2. Draft a response letter based on the decision and all available data
3. Save the draft

The letter MUST include:
- Professional greeting with the customer's full name
- Reference to their complaint subject and date
- Clear statement of the decision (complaint accepted/rejected)
- Detailed explanation referencing specific evidence and documents reviewed
- If POSITIVE: what action the bank will take (refund, fee waiver, correction, etc.)
- If NEGATIVE: clear reasoning why, with references to relevant policies
- Next steps for the customer
- Professional closing with bank name

Mortgage-specific instructions:
- For mortgage application rejection complaints, explain the exact refusal reason.
- If refusal reason is not_enough_income, mention the income shortfall and acceptable supporting evidence.
- If refusal reason is not_enough_transactions, mention the insufficient transaction history and what activity evidence is needed.
- If refusal reason is wrong_or_incomplete_documents, list or reference the missing documents and request resubmission.

Tone: Formal, empathetic, clear. Use professional banking language.
Sign as: "Customer Relations Department, Helmes Bank"

If the decision is "NEGATIVE" due to insufficient documents, the letter should:
- Explain what documents are missing
- Request the customer to resubmit with complete documentation
- Provide guidance on what documents are needed

ALWAYS call load_complaint_context first, then draft and save.
"""

TOOLS = [load_complaint_context, save_draft]


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


@observe(name="drafting-agent")
async def run_drafting_agent(
    complaint_id: str,
    decision: str,
    refusal_reason: str | None = None,
    clarification_message: str | None = None,
):
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found")

    await create_agent_log(
        complaint_id,
        "drafting_agent",
        "start_processing",
        {"complaint_id": complaint_id, "decision": decision},
        "Drafting agent started.",
        {},
    )

    input_text = (
        f"Complaint ID: {complaint_id}\n"
        f"Customer: {complaint['first_name']} {complaint['last_name']}\n"
        f"Subject: {complaint['subject']}\n"
        f"Message: {complaint['message']}\n"
        f"Decision: {decision}\n"
    )
    if refusal_reason:
        input_text += f"Refusal Reason: {refusal_reason}\n"
    if refusal_reason in SUPPORTED_MORTGAGE_REFUSAL_REASONS:
        input_text += f"Mortgage Draft Guidance: {get_mortgage_drafting_guidance(refusal_reason)}\n"
    if clarification_message:
        input_text += f"Clarification Message: {clarification_message}\n"

    agent = _build_agent()
    handler = get_langfuse_handler(complaint_id)
    invoke_config = {"callbacks": [handler]} if handler else {}
    result = await asyncio.to_thread(
        agent.invoke,
        {"messages": [{"role": "user", "content": input_text}]},
        invoke_config,
    )

    messages = result.get("messages", [])
    final_output = _stringify_message_content(messages[-1]) if messages else ""
    await create_agent_log(
        complaint_id,
        "drafting_agent",
        "completed",
        {"complaint_id": complaint_id, "decision": decision},
        "Drafting agent completed successfully.",
        {"agent_output": final_output},
    )

    return result
