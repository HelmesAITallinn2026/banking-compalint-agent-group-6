from enum import Enum
from pydantic import BaseModel


class ComplaintStatus(str, Enum):
    submitted = "submitted"
    data_extracted = "data_extracted"
    categorised = "categorised"
    recommendation_ready = "recommendation_ready"
    draft_created = "draft_created"
    completed = "completed"


class ComplaintFormResponse(BaseModel):
    complaint_id: str
    status: str


class DraftResponseRequest(BaseModel):
    complaint_id: str
    decision: str
    refusal_reason: str | None = None
    clarification_message: str | None = None


class DraftResponseResponse(BaseModel):
    complaint_id: str
    status: str


class ComplaintFile(BaseModel):
    original_filename: str
    stored_path: str
    content_type: str | None = None
    created_at: str


class AgentLog(BaseModel):
    agent_name: str
    action_type: str
    input_context: str | None = None
    reasoning_process: str
    output_context: str | None = None
    created_at: str


class ComplaintDetail(BaseModel):
    id: str
    first_name: str
    last_name: str
    subject: str
    message: str
    refusal_reason: str | None = None
    status: str
    category: str | None = None
    recommendation: str | None = None
    recommendation_reasoning: str | None = None
    draft_response: str | None = None
    extracted_data: str | None = None
    created_at: str
    updated_at: str
    files: list[ComplaintFile]
    logs: list[AgentLog]
