# Integration Plan: Frontend ↔ Backend ↔ Agent

## Problem
Three services run independently with no communication:
- **Frontend** → talks to **Backend** (works)
- **Backend** → has a stub `AiProcessingPublisher` that only logs (broken link)
- **Agent** → uses its own SQLite DB, never talks to Backend (isolated)

## Design Decisions (confirmed with user)
1. **Drop SQLite** — agent becomes stateless, uses backend API for all data
2. **New `POST /process/{complaint_id}`** — backend sends only complaint ID, agent fetches details from backend
3. **Agent downloads files** from backend attachment API for PDF processing
4. **Agent calls `PATCH /api/complaints/{id}/status`** and new endpoints to push results back

## Target Data Flow
```
Frontend ──POST /api/complaints──► Backend (PostgreSQL)
                                      │
                                      ▼
                              POST /process/{id} ──► Agent (stateless)
                                                       │
                              ┌─────────────────────────┤
                              │  GET /api/complaints/{id}/agent-detail
                              │  GET /api/attachments/{id}/file
                              ▼
                           Extract → Categorize → Recommend
                              │         │            │
                              ▼         ▼            ▼
                     PATCH /api/complaints/{id}/agent-update
                     (status + extracted_data / category / recommendation)
                              │
                              ▼
                         Backend (PostgreSQL updated)
                              │
                              ▼
                    Dashboard shows "Recommendation Ready"
                              │
                    Operator triggers draft generation
                              │
Frontend ──POST /api/complaints/{id}/generate-draft──► Backend
                                                          │
                                              POST /draft-response ──► Agent
                                                                         │
                                              PATCH /api/complaints/{id}/agent-update
                                              (draft_email_subject + draft_email_body + status=Draft Created)
                                                          │
                                                  Dashboard shows draft
                                                          │
                                        Operator approves → POST /{id}/approve
```

---

## Phase 1: Database Schema Changes

Add columns to PostgreSQL `complaint` table:
```sql
ALTER TABLE complaint ADD COLUMN extracted_data TEXT;
ALTER TABLE complaint ADD COLUMN category VARCHAR(512);
ALTER TABLE complaint ADD COLUMN recommendation VARCHAR(50);
ALTER TABLE complaint ADD COLUMN recommendation_reasoning TEXT;
```

Add `agent_log` table:
```sql
CREATE TABLE agent_log (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER NOT NULL REFERENCES complaint(id),
    agent_name VARCHAR(100) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    input_context TEXT,
    reasoning_process TEXT,
    output_context TEXT,
    created_dttm TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Files:** `database/03_agent_columns.sql`

---

## Phase 2: Backend — New Entity Fields & Endpoints

### 2a. Update Complaint Entity + DTO
Add new fields to `Complaint.java` entity and `ComplaintDto.java`:
- `extractedData` (TEXT)
- `category` (VARCHAR)
- `recommendation` (VARCHAR)
- `recommendationReasoning` (TEXT)

Update `ComplaintMapper` accordingly.

### 2b. New Endpoint: Agent Data Update
`PATCH /api/complaints/{id}/agent-update`

Request body (JSON):
```json
{
  "statusId": 2,
  "extractedData": "...",
  "category": "Loan Complaints > Mortgage Application Rejection",
  "recommendation": "POSITIVE",
  "recommendationReasoning": "...",
  "draftEmailSubject": "...",
  "draftEmailBody": "..."
}
```
All fields optional — agent sends only what changed at each step.

### 2c. New Endpoint: Agent Detail View
`GET /api/complaints/{id}/agent-detail`

Returns enriched DTO with:
- All complaint fields (including new ones)
- Customer first_name, last_name separately
- Attachments list with download URLs
- Refusal reason name (not just ID)

This gives the agent everything it needs in one call.

### 2d. New Endpoint: Generate Draft
`POST /api/complaints/{id}/generate-draft`

Request body:
```json
{
  "decision": "POSITIVE",
  "refusalReason": null,
  "clarificationMessage": null
}
```
Backend calls agent's `POST /draft-response` asynchronously.

### 2e. Agent Log Endpoints
- `POST /api/complaints/{id}/agent-logs` — agent pushes log entries
- `GET /api/complaints/{id}/agent-logs` — dashboard reads logs

### 2f. Replace StubAiProcessingPublisher
Create `AgentHttpPublisher` that calls `POST http://agent:8000/process/{complaintId}` asynchronously using `RestTemplate`/`WebClient`.

**Config:** Add `app.agent.base-url=http://localhost:8000` to `application.properties`.

**Files:**
- `backend/src/main/java/com/bcag6/entity/Complaint.java`
- `backend/src/main/java/com/bcag6/entity/AgentLog.java` (new)
- `backend/src/main/java/com/bcag6/dto/ComplaintDto.java`
- `backend/src/main/java/com/bcag6/dto/AgentUpdateRequest.java` (new)
- `backend/src/main/java/com/bcag6/dto/AgentDetailDto.java` (new)
- `backend/src/main/java/com/bcag6/dto/GenerateDraftRequest.java` (new)
- `backend/src/main/java/com/bcag6/dto/AgentLogDto.java` (new)
- `backend/src/main/java/com/bcag6/mapper/ComplaintMapper.java`
- `backend/src/main/java/com/bcag6/repository/AgentLogRepository.java` (new)
- `backend/src/main/java/com/bcag6/service/ComplaintService.java`
- `backend/src/main/java/com/bcag6/service/AgentLogService.java` (new)
- `backend/src/main/java/com/bcag6/service/AgentClient.java` (new)
- `backend/src/main/java/com/bcag6/controller/ComplaintController.java`
- `backend/src/main/java/com/bcag6/event/AgentHttpPublisher.java` (new)
- `backend/src/main/resources/application.properties`

---

## Phase 3: Agent — Replace SQLite with Backend API Client

### 3a. Create `backend_client.py`
HTTP client module that replaces all `database.py` functions:

| Old (database.py) | New (backend_client.py) |
|---|---|
| `get_complaint_by_id(id)` | `GET /api/complaints/{id}/agent-detail` → dict |
| `update_complaint_status(id, status)` | `PATCH /api/complaints/{id}/agent-update` with statusId |
| `save_extracted_data(id, data)` | `PATCH /api/complaints/{id}/agent-update` with extractedData + statusId=2 |
| `save_categorization(id, cat)` | `PATCH /api/complaints/{id}/agent-update` with category + statusId=3 |
| `save_recommendation(id, cat, rec, reasoning)` | `PATCH /api/complaints/{id}/agent-update` with recommendation fields + statusId=4 |
| `save_draft_response(id, draft)` | `PATCH /api/complaints/{id}/agent-update` with draftEmailSubject/Body + statusId=5 |
| `create_agent_log(...)` | `POST /api/complaints/{id}/agent-logs` |

Status name → ID mapping:
```python
STATUS_MAP = {
    "submitted": 1,
    "data_extracted": 2,
    "categorised": 3,
    "recommendation_ready": 4,
    "draft_created": 5,
    "completed": 6,
}
```

File download: `download_attachment(attachment_id) → GET /api/attachments/{id}/file` → save to temp dir.

### 3b. New Endpoint: `POST /process/{complaint_id}`
Replaces the old `POST /complaint-form`. Receives only complaint_id, fetches data from backend, triggers extraction pipeline.

### 3c. Update Agent Sub-modules
Replace all `from database import ...` with `from backend_client import ...` in:
- `extracting_agent/agent.py`
- `categorization_agent/agent.py`
- `data_retrieval_agent/agent.py`
- `drafting_agent/agent.py`
- `pipeline.py`
- `main.py`

The categorization agent's direct SQL (`get_db()`) must be replaced with `backend_client.save_categorization()`.

### 3d. File Handling
Agent downloads attachments from backend API into a temp directory, processes them, then cleans up. The extracting agent reads `complaint["files"]` with `stored_path` — we change this to download from backend attachment URLs.

### 3e. Update `main.py`
- Remove `create_complaint`, `create_file_record` imports
- Remove `POST /complaint-form` endpoint (replaced by `/process/{id}`)
- Update `POST /draft-response` to use backend_client
- Remove `GET /complaints/{id}` (data lives in backend now)
- Remove SQLite init from lifespan
- Add config for `BACKEND_URL` env var

### 3f. Adapt `get_complaint_by_id` return format
The backend returns different field names than SQLite. `backend_client.get_complaint_by_id()` maps backend response to the dict format agents expect:
```python
{
    "id": ...,
    "first_name": agent_detail.firstName,
    "last_name": agent_detail.lastName,
    "subject": ...,
    "message": agent_detail.text,
    "refusal_reason": agent_detail.refusalReason,
    "status": ...,
    "category": ...,
    "recommendation": ...,
    "recommendation_reasoning": ...,
    "draft_response": agent_detail.draftEmailBody,
    "extracted_data": ...,
    "files": [{"original_filename": ..., "stored_path": ..., "content_type": ..., "id": ...}],
    "logs": [...]
}
```

**Files:**
- `agent/backend_client.py` (new)
- `agent/main.py`
- `agent/pipeline.py`
- `agent/extracting_agent/agent.py`
- `agent/categorization_agent/agent.py`
- `agent/data_retrieval_agent/agent.py`
- `agent/drafting_agent/agent.py`
- `agent/schemas.py`
- `agent/.env.example` (add BACKEND_URL)

---

## Phase 4: Frontend — Dashboard Enhancements

### 4a. Add "Generate Draft" Button
In the Dashboard's "Submitted/In Process" tab, when a complaint reaches "Decision Recommendation Created" status, show a "Generate Draft" button. Add `generateDraft` API function. Show decision options (POSITIVE/NEGATIVE).

### 4b. Display Agent Processing Data
In the complaint detail modal, show:
- Category (when available)
- Recommendation + reasoning (when available)
- Extracted data summary (when available)
- Agent logs timeline (optional, nice-to-have)

### 4c. Add API Functions
```javascript
export const generateDraft = (id, decision, refusalReason, clarificationMessage) =>
  api.post(`/api/complaints/${id}/generate-draft`, { decision, refusalReason, clarificationMessage })

export const getAgentLogs = (id) =>
  api.get(`/api/complaints/${id}/agent-logs`)
```

**Files:**
- `frontend/src/api/index.js`
- `frontend/src/components/ComplaintModal.jsx`
- `frontend/src/pages/Dashboard.jsx`

---

## Phase 5: Docker & Config

### 5a. Update `docker-compose.dev.yml`
- Add `BACKEND_URL=http://backend:8080` to agent service environment
- Add `APP_AGENT_BASE_URL=http://agent:8000` to backend service environment
- Remove `agent_db` volume (no more SQLite)
- Keep `agent_uploads` for temp file storage during processing
- Add `database/03_agent_columns.sql` to db init volumes

### 5b. Update `.env.example` files
- `agent/.env.example`: add `BACKEND_URL=http://localhost:8080`
- `backend/src/main/resources/application.properties`: add `app.agent.base-url`

---

## Phase 6: Verification

1. Start all services via docker-compose
2. Submit complaint via frontend customer page
3. Verify backend creates complaint in PostgreSQL
4. Verify backend triggers agent processing
5. Verify agent fetches complaint from backend API
6. Verify agent updates status at each pipeline step
7. Verify dashboard shows status progression
8. Trigger draft generation from dashboard
9. Verify draft appears in complaint detail
10. Approve draft and verify status becomes Completed

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Agent processing fails silently | Agent catches errors and pushes error status/log to backend |
| Backend down when agent tries to push | Agent retries with backoff (simple retry loop) |
| Status ID mapping drift | Single source of truth: `STATUS_MAP` in agent, matching DB seed |
| File download slow for large PDFs | Agent caches downloaded files in temp dir for session |
| Breaking existing agent tests | Update tests to mock `backend_client` instead of `database` |