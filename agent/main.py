import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend_client import get_complaint_by_id
from model_pricing import register_model_prices
from pipeline import run_drafting_pipeline, run_extraction_pipeline
from schemas import ComplaintStatus, DraftResponseRequest, DraftResponseResponse


@asynccontextmanager
async def lifespan(_):
    register_model_prices()
    yield

app = FastAPI(title="Complaint Agent API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/")
@app.get("/health")
async def healthcheck():
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
    return {"status": "ok", "backend_url": backend_url}


@app.post("/process/{complaint_id}")
async def process_complaint(complaint_id: str, background_tasks: BackgroundTasks):
    """Trigger the AI extraction pipeline for an existing backend complaint."""
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found in backend")
    background_tasks.add_task(run_extraction_pipeline, complaint_id)
    return {"complaint_id": complaint_id, "status": "processing"}


@app.post("/draft-response", response_model=DraftResponseResponse)
async def draft_response(payload: DraftResponseRequest, background_tasks: BackgroundTasks):
    complaint = await get_complaint_by_id(payload.complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    background_tasks.add_task(run_drafting_pipeline, payload.complaint_id, payload.decision, payload.refusal_reason, payload.clarification_message)
    return DraftResponseResponse(complaint_id=payload.complaint_id, status=ComplaintStatus.draft_created)


