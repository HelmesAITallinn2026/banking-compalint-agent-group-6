from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path

from langfuse.openai import openai
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError

from database import create_agent_log, get_complaint_by_id, save_extracted_data, update_complaint_status
from schemas import ComplaintStatus
from tracing import get_langfuse_handler, observe


class ExtractedComplaint(BaseModel):
    customer_name: str | None = None
    email: str | None = None
    issue_type: str | None = None
    description: str | None = None
    date: str | None = None
    order_id: str | None = None
    is_relevant: bool = True


def _build_chat_model(model_name: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name or os.getenv("EXTRACTION_MODEL") or "openai/gpt-4o-mini",
        api_key=os.getenv("OPENROUTER_API_KEY") or "test-key",
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0,
        model_kwargs={"extra_body": {"usage": {"include": True}}},
    )


def _extract_pdf_text_layer(file_path: str) -> str:
    reader = PdfReader(file_path)
    chunks: list[str] = []
    for page in reader.pages:
        page_text = (page.extract_text() or "").strip()
        if page_text:
            chunks.append(page_text)
    return "\n".join(chunks).strip()


def _read_text_file(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="ignore").strip()


def _looks_like_pdf(file_path: str, content_type: str | None = None) -> bool:
    if (content_type or "").lower() == "application/pdf":
        return True
    with open(file_path, "rb") as file_handle:
        return file_handle.read(5) == b"%PDF-"


@tool
def analyze_document_type(file_path: str, content_type: str | None = None) -> dict:
    """Inspect a file and classify it as a readable document or an image."""
    suffix = Path(file_path).suffix.lower()

    if _looks_like_pdf(file_path, content_type):
        try:
            text = _extract_pdf_text_layer(file_path)
        except (PdfReadError, PdfStreamError):
            text = ""
        if text:
            return {
                "document_type": "document",
                "reason": "PDF contains a readable text layer.",
                "file_path": file_path,
                "text": text,
            }
        return {
            "document_type": "image",
            "reason": "PDF has no readable text layer, OCR required.",
            "file_path": file_path,
            "text": "",
        }

    if suffix in {".txt", ".json", ".xml", ".csv", ".md"}:
        text = _read_text_file(file_path)
        return {
            "document_type": "document",
            "reason": "Readable text-based document.",
            "file_path": file_path,
            "text": text,
        }

    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"} or (content_type or "").startswith("image/"):
        return {
            "document_type": "image",
            "reason": "Image file requires OCR.",
            "file_path": file_path,
            "text": "",
        }

    text = _read_text_file(file_path)
    if text:
        return {
            "document_type": "document",
            "reason": "Fallback text read succeeded.",
            "file_path": file_path,
            "text": text,
        }

    return {
        "document_type": "image",
        "reason": "No readable text found, treating as image.",
        "file_path": file_path,
        "text": "",
    }


@tool
def ocr_document(file_path: str) -> dict:
    """Convert an image file to text using a vision-capable model via OpenRouter."""
    client = openai.OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    with open(file_path, "rb") as file_handle:
        image_data = base64.b64encode(file_handle.read()).decode("utf-8")

    suffix = Path(file_path).suffix.lower()
    mime_by_suffix = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_by_suffix.get(suffix, "image/jpeg")

    response = client.chat.completions.create(
        model=os.getenv("OCR_MODEL", "google/gemini-flash-1.5-8b"),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    {"type": "text", "text": "Extract all text from this image. Return only the raw text."},
                ],
            }
        ],
        extra_body={"usage": {"include": True}},
    )

    extracted_text = (response.choices[0].message.content or "").strip()
    return {"text": extracted_text, "file_path": file_path}


@tool
def extract_data(text: str, document_type: str = "document") -> dict:
    """Extract structured complaint data from document or OCR text."""
    llm = _build_chat_model()
    structured_llm = llm.with_structured_output(ExtractedComplaint)
    result = structured_llm.invoke(
        [
            (
                "system",
                "Extract structured banking complaint data. Set is_relevant=false for non-banking or irrelevant content.",
            ),
            (
                "human",
                f"Document type: {document_type}\n\nText:\n{text}",
            ),
        ]
    )
    return result.model_dump()


@tool
def save_complaint_data(complaint_id: str, extracted_data: str) -> dict:
    """Persist extracted complaint data to the complaint record."""

    async def _save() -> None:
        parsed_data = json.loads(extracted_data) if isinstance(extracted_data, str) else extracted_data
        await save_extracted_data(complaint_id, json.dumps(parsed_data))
        await create_agent_log(
            complaint_id,
            "extraction_agent",
            "save_extracted_data",
            {"complaint_id": complaint_id},
            "Saved structured extraction results to DB.",
            parsed_data,
        )

    asyncio.run(_save())
    return {"status": "success", "complaint_id": complaint_id}


SYSTEM_PROMPT = """You are an Extraction Agent responsible for processing complaint submissions.

Your job is to:
1. Determine the document type
2. If needed, perform OCR
3. Extract structured complaint data
4. Decide if the data is relevant
5. Save relevant data

Rules:
- ALWAYS start by calling `analyze_document_type` for each attached file
- If `analyze_document_type` returns `document`, use the returned `text` when calling `extract_data`
- If `analyze_document_type` returns `image`, you MUST call `ocr_document`
- After OCR, ALWAYS call `extract_data`
- If there are no files, call `extract_data` on the complaint message text
- If `extract_data` returns `is_relevant = true`, call `save_complaint_data`
- If `is_relevant = false`, STOP and explain why
- When calling `save_complaint_data`, pass the complaint_id and the full extracted JSON as a string

Do not skip steps.
Do not invent tool results.
Return a final answer only after the workflow is complete.
"""

TOOLS = [analyze_document_type, ocr_document, extract_data, save_complaint_data]


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


@observe(name="extraction-agent")
async def run_extraction_agent(complaint_id: str):
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found")

    await create_agent_log(
        complaint_id,
        "extraction_agent",
        "start_processing",
        {"complaint_id": complaint_id},
        "Extraction agent started.",
        {},
    )

    files = complaint.get("files", [])
    file_descriptions = [
        f"File: {file_info['original_filename']}, path: {file_info['stored_path']}, type: {file_info.get('content_type', 'unknown')}"
        for file_info in files
    ]

    input_text = (
        f"Complaint ID: {complaint_id}\n"
        f"Customer: {complaint['first_name']} {complaint['last_name']}\n"
        f"Subject: {complaint['subject']}\n"
        f"Message: {complaint['message']}\n"
    )
    if file_descriptions:
        input_text += "\nAttached files:\n" + "\n".join(file_descriptions)
    else:
        input_text += "\nNo files attached. Use the complaint message as the source text."

    agent = _build_agent()
    handler = get_langfuse_handler(complaint_id)
    invoke_config = {"callbacks": [handler]} if handler else {}
    result = await asyncio.to_thread(
        agent.invoke,
        {"messages": [{"role": "user", "content": input_text}]},
        invoke_config,
    )

    await update_complaint_status(complaint_id, ComplaintStatus.data_extracted)

    messages = result.get("messages", [])
    final_output = _stringify_message_content(messages[-1]) if messages else ""
    await create_agent_log(
        complaint_id,
        "extraction_agent",
        "completed",
        {"complaint_id": complaint_id},
        "Extraction agent completed successfully.",
        {"agent_output": final_output},
    )

    return result
