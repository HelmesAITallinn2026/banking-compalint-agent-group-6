from __future__ import annotations

import asyncio
import json
import os

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from database import create_agent_log, get_complaint_by_id, save_recommendation
from data_retrieval_agent.mock_data import (
    DECISION_RULES,
    get_account_info,
    get_customer_details,
    get_transaction_history,
)
from tracing import get_langfuse_handler, observe


def _build_chat_model(model_name: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name or os.getenv("DATA_RETRIEVAL_MODEL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0,
        model_kwargs={"extra_body": {"usage": {"include": True}}},
    )


@tool
def retrieve_customer_details(complaint_id: str) -> dict:
    """Retrieve customer details from the banking system for the given complaint."""

    async def _load():
        return await get_complaint_by_id(complaint_id)

    complaint = asyncio.run(_load())
    if not complaint:
        return {"error": f"Complaint {complaint_id} not found"}
    return get_customer_details(
        complaint_id,
        complaint["first_name"],
        complaint["last_name"],
    )


@tool
def retrieve_account_info(complaint_id: str) -> dict:
    """Retrieve account information for the customer linked to this complaint."""
    return {"accounts": get_account_info(complaint_id)}


@tool
def retrieve_transaction_history(complaint_id: str) -> dict:
    """Retrieve recent transaction history for the customer linked to this complaint."""
    return {"transactions": get_transaction_history(complaint_id)}


@tool
def load_decision_rules() -> str:
    """Load the bank's decision rules for complaint resolution."""
    return DECISION_RULES


@tool
def save_recommendation_result(complaint_id: str, recommendation: str, reasoning: str) -> dict:
    """Save the final POSITIVE or NEGATIVE recommendation with reasoning to the complaint record."""

    async def _save():
        complaint = await get_complaint_by_id(complaint_id)
        category = (complaint or {}).get("category", "unknown")
        await save_recommendation(complaint_id, category, recommendation, reasoning)
        await create_agent_log(
            complaint_id,
            "data_retrieval_agent",
            "save_recommendation",
            {"complaint_id": complaint_id, "recommendation": recommendation},
            reasoning,
            {"recommendation": recommendation, "category": category},
        )

    asyncio.run(_save())
    return {"status": "success", "complaint_id": complaint_id, "recommendation": recommendation}


SYSTEM_PROMPT = """You are a Data Retrieval Agent for a bank's complaint processing system.

Your job is to:
1. Load decision rules
2. Retrieve customer details for the complaint
3. Retrieve account information
4. Retrieve transaction history
5. Analyze all data against the decision rules
6. Produce a POSITIVE or NEGATIVE recommendation with detailed reasoning
7. Save the recommendation

Rules:
- ALWAYS load decision rules first
- ALWAYS retrieve ALL data (customer, accounts, transactions) before making a decision
- Log WHY you are retrieving each piece of data
- Your reasoning must reference specific data points
- Call save_recommendation_result at the end

Do not skip steps. Do not invent data.
"""

TOOLS = [
    retrieve_customer_details,
    retrieve_account_info,
    retrieve_transaction_history,
    load_decision_rules,
    save_recommendation_result,
]


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


@observe(name="data-retrieval-agent")
async def run_data_retrieval_agent(complaint_id: str):
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found")

    await create_agent_log(
        complaint_id,
        "data_retrieval_agent",
        "start_processing",
        {"complaint_id": complaint_id},
        "Data retrieval agent started.",
        {},
    )

    extracted_data = complaint.get("extracted_data", "{}")
    category = complaint.get("category", "unknown")

    input_text = (
        f"Complaint ID: {complaint_id}\n"
        f"Customer: {complaint['first_name']} {complaint['last_name']}\n"
        f"Subject: {complaint['subject']}\n"
        f"Message: {complaint['message']}\n"
        f"Category: {category}\n"
        f"Extracted Data: {extracted_data}\n"
    )

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
        "data_retrieval_agent",
        "completed",
        {"complaint_id": complaint_id},
        "Data retrieval agent completed successfully.",
        {"agent_output": final_output},
    )

    return result
