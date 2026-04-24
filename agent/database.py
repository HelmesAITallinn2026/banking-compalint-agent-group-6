import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "complaints.db"
UPLOADS_DIR = BASE_DIR / "uploads"

_db_initialized = False


async def init_db():
    global _db_initialized
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("""CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL, last_name TEXT NOT NULL,
            subject TEXT NOT NULL, message TEXT NOT NULL, refusal_reason TEXT,
            status TEXT NOT NULL DEFAULT 'submitted',
            category TEXT, recommendation TEXT, recommendation_reasoning TEXT, draft_response TEXT, extracted_data TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS complaint_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
            original_filename TEXT NOT NULL, stored_path TEXT NOT NULL, content_type TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
            agent_name TEXT NOT NULL, action_type TEXT NOT NULL,
            input_context TEXT, reasoning_process TEXT, output_context TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.commit()
    _db_initialized = True


@asynccontextmanager
async def get_db():
    if not _db_initialized:
        await init_db()
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        await db.commit()
    finally:
        await db.close()


async def create_complaint(first_name, last_name, subject, message, refusal_reason=None):
    complaint_id = uuid.uuid4().hex[:16]
    async with get_db() as db:
        await db.execute(
            "INSERT INTO complaints (id, first_name, last_name, subject, message, refusal_reason) VALUES (?,?,?,?,?,?)",
            (complaint_id, first_name, last_name, subject, message, refusal_reason),
        )
        return complaint_id


async def create_file_record(complaint_id, original_filename, stored_path, content_type=None):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO complaint_files (complaint_id, original_filename, stored_path, content_type) VALUES (?,?,?,?)",
            (complaint_id, original_filename, stored_path, content_type),
        )


async def update_complaint_status(complaint_id, status):
    async with get_db() as db:
        await db.execute(
            "UPDATE complaints SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, complaint_id),
        )


async def save_recommendation(complaint_id, category, recommendation, reasoning):
    async with get_db() as db:
        await db.execute(
            "UPDATE complaints SET category=?, recommendation=?, recommendation_reasoning=?, status='recommendation_ready', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (category, recommendation, reasoning, complaint_id),
        )


async def save_draft_response(complaint_id, draft_response):
    async with get_db() as db:
        await db.execute(
            "UPDATE complaints SET draft_response=?, status='draft_created', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (draft_response, complaint_id),
        )


async def create_agent_log(complaint_id, agent_name, action_type, input_context, reasoning_process, output_context):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO agent_logs (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context) VALUES (?,?,?,?,?,?)",
            (complaint_id, agent_name, action_type, json.dumps(input_context or {}), reasoning_process, json.dumps(output_context or {})),
        )


async def save_extracted_data(complaint_id, extracted_data_json):
    async with get_db() as db:
        await db.execute(
            "UPDATE complaints SET extracted_data=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (extracted_data_json, complaint_id),
        )


async def get_complaint_by_id(complaint_id):
    async with get_db() as db:
        row = await (await db.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,))).fetchone()
        if not row:
            return None
        files = await (await db.execute(
            "SELECT original_filename, stored_path, content_type, created_at FROM complaint_files WHERE complaint_id=? ORDER BY id", (complaint_id,)
        )).fetchall()
        logs = await (await db.execute(
            "SELECT agent_name, action_type, input_context, reasoning_process, output_context, created_at FROM agent_logs WHERE complaint_id=? ORDER BY id", (complaint_id,)
        )).fetchall()
    result = dict(row)
    result["files"] = [dict(r) for r in files]
    result["logs"] = [dict(r) for r in logs]
    return result
