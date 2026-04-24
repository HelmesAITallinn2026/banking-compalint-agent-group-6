# Agent Module – Banking Complaint Processing System

## Overview

`agent/` is the active backend for the hackathon demo. It exposes a FastAPI API, stores complaint state in local SQLite, runs a multi-step LLM pipeline, and keeps an audit trail of agent actions.

This is demo code. Keep it simple, readable, and easy to ship.

## Tech Stack

- Python `3.12+`
- `uv` for env/deps
- `FastAPI` + `uvicorn` for HTTP API
- `aiosqlite` for async local persistence
- `LangChain` agents via `create_agent(...)`
- OpenRouter-backed `ChatOpenAI` models
- `Langfuse` for optional tracing
- `pytest` for tests

## Important Paths

- `main.py` — FastAPI app and endpoints
- `database.py` — SQLite init and all DB helpers
- `pipeline.py` — extraction + drafting pipeline entrypoints
- `extracting_agent/` — document classification, OCR, extraction
- `categorization_agent/` — complaint tree classification
- `data_retrieval_agent/` — mock banking data lookup + recommendation
- `drafting_agent/` — response letter generation
- `schemas.py` — request/response/status models
- `.env.example` — required env vars
- `tests/` — current test suite
- `uploads/` — saved complaint files
- `complaints.db` — local SQLite DB

## Local Setup

From repo root:

```bash
cd agent
uv sync
cp .env.example .env
```

## Run Commands

### Start API

```bash
cd agent
uv run uvicorn main:app --reload
```

API base: `http://localhost:8000`

### Run tests

```bash
cd agent
uv run pytest
```

### Health check

```bash
curl http://localhost:8000/health
```

### Sample submit

```bash
curl -X POST http://localhost:8000/complaint-form \
  -F "first_name=Jane" \
  -F "last_name=Doe" \
  -F "subject=Card charge dispute" \
  -F "message=I was charged twice for one purchase." \
  -F "refusal_reason=" \
  -F "files=@../mock_docs/helmes_bank_salary_statement.pdf"
```

### Sample fetch

```bash
curl http://localhost:8000/complaints/<complaint_id>
```

### Sample draft trigger

```bash
curl -X POST http://localhost:8000/draft-response \
  -H "Content-Type: application/json" \
  -d '{
    "complaint_id": "<complaint_id>",
    "decision": "NEGATIVE",
    "refusal_reason": "insufficient_documents",
    "clarification_message": "Please attach a clearer statement copy."
  }'
```

## Environment Variables

Copy `.env.example` to `.env` and set:

```env
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OCR_MODEL=z-ai/glm-4.6v
EXTRACTION_MODEL=z-ai/glm-5.1
CATEGORIZATION_MODEL=z-ai/glm-5.1
DATA_RETRIEVAL_MODEL=z-ai/glm-5.1
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=http://localhost:3000
```

Notes:

- `OPENROUTER_API_KEY` is required for real LLM calls.
- `LANGFUSE_*` is optional. If unset, tracing stays off.
- Drafting agent also supports `DRAFTING_MODEL`; if unset it falls back to `openai/gpt-4o-mini`.

## Optional Observability Setup

From repo root:

```bash
docker compose -f docker-compose.langfuse.yml up -d
```

- Langfuse UI: `http://localhost:3000`
- After first boot, create a project and copy keys into `agent/.env`

## Runtime Flow

```text
Complaint form submit
        |
        v
Extraction agent
        |
        +--> early NEGATIVE draft path if docs irrelevant/incomplete
        |
        v
Categorization agent
        |
        v
Data retrieval agent
        |
        v
recommendation_ready
        |
        v
Human review
        |
        v
POST /draft-response
        |
        v
Drafting agent
```

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | same payload as health |
| `GET` | `/health` | returns `{status, database_path}` |
| `POST` | `/complaint-form` | creates complaint, saves files, starts extraction pipeline |
| `GET` | `/complaints/{complaint_id}` | full complaint view with files and logs |
| `POST` | `/draft-response` | starts drafting pipeline for an existing complaint |

### `/complaint-form` fields

- `first_name`
- `last_name`
- `subject`
- `message`
- `refusal_reason` *(optional)*
- `files` *(0..n multipart uploads)*

Uploaded files are stored in `agent/uploads/` as:

`<first_name>-<last_name>-<complaint_id>-<original_stem>.pdf`

### `/draft-response` JSON body

- `complaint_id`
- `decision`
- `refusal_reason` *(optional)*
- `clarification_message` *(optional)*

## Current Status Values

Defined in `schemas.py`:

- `submitted`
- `data_extracted`
- `categorised`
- `recommendation_ready`
- `draft_created`
- `completed`

## Database

SQLite DB path: `agent/complaints.db`

Tables auto-created by `init_db()`:

### `complaints`

- `id`
- `first_name`
- `last_name`
- `subject`
- `message`
- `refusal_reason`
- `status`
- `category`
- `recommendation`
- `recommendation_reasoning`
- `draft_response`
- `extracted_data`
- `created_at`
- `updated_at`

### `complaint_files`

- `complaint_id`
- `original_filename`
- `stored_path`
- `content_type`
- `created_at`

### `agent_logs`

- `complaint_id`
- `agent_name`
- `action_type`
- `input_context`
- `reasoning_process`
- `output_context`
- `created_at`

Rule: all DB reads/writes go through helpers in `database.py`.

## Agents

### 1. Extraction agent

Files:

- `extracting_agent/agent.py`
- `extraction_agent.py`

Responsibilities:

- Detect readable text vs image-like document
- Extract PDF text layer when present
- OCR image-like inputs through OpenRouter vision model
- Produce structured complaint payload
- Save extraction result and logs

Core tools:

- `analyze_document_type`
- `ocr_document`
- `extract_data`
- `save_complaint_data`

### 2. Categorization agent

Files:

- `categorization_agent/agent.py`
- `categorization_agent/complaint_tree.json`

Responsibilities:

- Load complaint tree
- Choose category + subcategory
- Save `category > subcategory`
- Log reasoning

Core tools:

- `load_complaint_tree`
- `save_categorization`

### 3. Data retrieval agent

Files:

- `data_retrieval_agent/agent.py`
- `data_retrieval_agent/mock_data.py`

Responsibilities:

- Load decision rules
- Pull mock customer/account/transaction data
- Generate `POSITIVE` or `NEGATIVE` recommendation
- Save recommendation + reasoning

Core tools:

- `retrieve_customer_details`
- `retrieve_account_info`
- `retrieve_transaction_history`
- `load_decision_rules`
- `save_recommendation_result`

### 4. Drafting agent

Files:

- `drafting_agent/agent.py`

Responsibilities:

- Load complaint context
- Draft formal customer response
- Save draft to DB
- Support both normal review path and insufficient-docs path

Core tools:

- `load_complaint_context`
- `save_draft`

## Logging and Tracing

Every agent run should create structured DB audit logs with:

- `agent_name`
- `action_type`
- `input_context`
- `reasoning_process`
- `output_context`

Langfuse tracing is wired through `tracing.py`. If keys are absent, callbacks are skipped.

## Testing

Current tests live under `agent/tests/`.

Existing coverage:

- document type detection for text PDFs
- scanned/image-style PDFs
- fake image bytes saved with `.pdf` suffix
- agent builder returning compiled graph object

Run with:

```bash
cd agent
uv run pytest
```

## Repo Notes

- `backend/` is not active.
- `frontend/` is design-only right now.
- Root `database/` SQL scripts are separate from the local SQLite runtime used by `agent/`.
- If docs drift from code, fix docs to match current runtime behavior.
