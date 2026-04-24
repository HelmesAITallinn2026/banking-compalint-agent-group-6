import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from database import DATABASE_PATH, UPLOADS_DIR, create_complaint, create_file_record, get_complaint_by_id, init_db
from model_pricing import register_model_prices
from pipeline import run_drafting_pipeline, run_extraction_pipeline
from schemas import ComplaintDetail, ComplaintFormResponse, ComplaintStatus, DraftResponseRequest, DraftResponseResponse


@asynccontextmanager
async def lifespan(_):
    await init_db()
    register_model_prices()
    yield

app = FastAPI(title="Complaint Agent API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/")
@app.get("/health")
async def healthcheck():
    return {"status": "ok", "database_path": str(DATABASE_PATH)}


@app.post("/complaint-form", response_model=ComplaintFormResponse)
async def submit_complaint_form(
    background_tasks: BackgroundTasks,
    first_name: str = Form(...),
    last_name: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    refusal_reason: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
):
    complaint_id = await create_complaint(first_name, last_name, subject, message, refusal_reason)

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    for f in files:
        original_name = Path(f.filename or "file").stem  # sanitize, strip ext
        filename = f"{first_name}-{last_name}-{complaint_id}-{original_name}.pdf"
        dest = UPLOADS_DIR / filename
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        await create_file_record(complaint_id, filename, str(dest), f.content_type)
        await f.close()

    background_tasks.add_task(run_extraction_pipeline, complaint_id)
    return ComplaintFormResponse(complaint_id=complaint_id, status=ComplaintStatus.submitted)


@app.post("/draft-response", response_model=DraftResponseResponse)
async def draft_response(payload: DraftResponseRequest, background_tasks: BackgroundTasks):
    complaint = await get_complaint_by_id(payload.complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    background_tasks.add_task(run_drafting_pipeline, payload.complaint_id, payload.decision, payload.refusal_reason, payload.clarification_message)
    return DraftResponseResponse(complaint_id=payload.complaint_id, status=ComplaintStatus.draft_created)


@app.get("/complaints/{complaint_id}", response_model=ComplaintDetail)
async def get_complaint(complaint_id: str):
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    return ComplaintDetail.model_validate(complaint)


