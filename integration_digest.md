# Integration Changes Digest

## Overview

The frontend, backend, and agent are now wired into a single flow with the **Spring Boot backend as the source of truth**. The backend stores complaint state in PostgreSQL, calls the FastAPI agent to process complaints and draft responses, and exposes enriched complaint data back to the frontend. The agent no longer persists complaint state in SQLite and instead reads from and writes to the backend over HTTP.

## Final Architecture

- **Frontend** talks only to the backend.
- **Backend** stores complaint data, attachments, statuses, agent outputs, and logs in PostgreSQL.
- **Agent** is stateless for complaint persistence and uses backend APIs for reads and updates.

### Processing flow

1. Frontend submits a complaint to the backend.
2. Backend saves the complaint and asynchronously triggers the agent with `POST /process/{complaint_id}`.
3. Agent fetches complaint details and attachments from backend APIs.
4. Agent runs extraction, categorization, and recommendation steps.
5. Agent pushes results and status changes back to backend through agent update endpoints.
6. Frontend reads updated statuses and agent outputs from backend.
7. Operator triggers draft generation through the backend.
8. Backend calls the agent draft endpoint.
9. Agent generates the response draft and pushes it back to the backend.

## Database Changes

### New migration

- `database/04_agent_columns.sql`

### Added complaint columns

- `extracted_data`
- `category`
- `recommendation`
- `recommendation_reasoning`

### Added table

- `agent_log`

This supports storing all agent-produced data directly in PostgreSQL instead of local SQLite.

## Backend Changes

The backend now owns the integration contract between UI and AI processing.

### New DTOs

- `AgentUpdateRequest.java`
- `AgentDetailDto.java`
- `GenerateDraftRequest.java`
- `AgentLogDto.java`

### New persistence and services

- `AgentLog.java`
- `AgentLogRepository.java`
- `AgentLogService.java`
- `AgentClient.java`
- `AgentHttpPublisher.java`

### Replaced old stub

- Deleted `StubAiProcessingPublisher.java`
- Replaced with real HTTP-based publisher calling the agent service

### Updated existing backend files

- `Complaint.java` — added agent result fields
- `ComplaintDto.java` — exposed agent result fields to API consumers
- `ComplaintService.java` — added:
  - `agentUpdate(...)`
  - `getAgentDetail(...)`
- `ComplaintController.java` — added endpoints for:
  - `PATCH /api/complaints/{id}/agent-update`
  - `GET /api/complaints/{id}/agent-detail`
  - `POST /api/complaints/{id}/generate-draft`
  - `POST /api/complaints/{id}/agent-logs`
  - `GET /api/complaints/{id}/agent-logs`
- `BcaApplication.java` — enabled async execution with `@EnableAsync`
- `SecurityConfig.java` — allowed `PATCH` requests
- `application.properties` — added `app.agent.base-url`

### Backend responsibilities after integration

- Save complaints and attachments
- Trigger AI processing asynchronously
- Accept agent field updates
- Store agent logs
- Trigger draft generation
- Serve enriched complaint details to the frontend

## Agent Changes

The agent was refactored from SQLite-backed storage to backend-API-based integration.

### New integration module

- `agent/backend_client.py`

This file replaces the old database access path and now:

- fetches complaint data from backend
- downloads complaint attachments from backend
- maps complaint data into the agent pipeline shape
- sends extraction/categorization/recommendation/draft updates back to backend
- sends agent logs back to backend

### Updated agent entrypoints and modules

- `agent/main.py`
- `agent/pipeline.py`
- `agent/extracting_agent/agent.py`
- `agent/categorization_agent/agent.py`
- `agent/data_retrieval_agent/agent.py`
- `agent/drafting_agent/agent.py`
- `agent/.env.example`

### Key behavior changes

- Removed complaint persistence dependency on SQLite
- Removed old complaint intake/read endpoints from the agent
- Added `POST /process/{complaint_id}` as the main backend-triggered processing entrypoint
- Kept `POST /draft-response` for draft generation
- Switched categorization saving from direct SQL to backend API calls
- Attachments are now downloaded from backend and cached locally in `agent/uploads/`

### Status mapping

Agent status values are mapped to backend complaint status IDs:

- `submitted` -> `1`
- `data_extracted` -> `2`
- `categorised` -> `3`
- `recommendation_ready` -> `4`
- `draft_created` -> `5`
- `completed` -> `6`

These align with backend complaint status seed values:

- `Submitted`
- `Data Extracted`
- `Categorised`
- `Decision Recommendation Created`
- `Draft Created`
- `Completed`

## Frontend Changes

The frontend now reads agent-produced fields from backend complaint payloads and can trigger draft generation from the complaint modal.

### Updated files

- `frontend/src/api/index.js`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/components/ComplaintModal.jsx`

### New frontend behavior

- Added API helpers:
  - `generateDraft()`
  - `getAgentLogs()`
- Dashboard can trigger draft generation for recommendation-ready complaints
- Complaint modal now displays:
  - category
  - recommendation
  - recommendation reasoning
- Complaint modal shows draft generation actions for complaints in the **Decision Recommendation Created** state

## Docker and Environment Changes

### Updated file

- `docker-compose.dev.yml`

### New wiring

- Added `BACKEND_URL` to the agent service
- Added `APP_AGENT_BASE_URL` to the backend service
- Added `04_agent_columns.sql` to DB initialization
- Replaced `database.py` volume usage with `backend_client.py`
- Removed the old `agent_db` volume

### Environment update

- `agent/.env.example` now includes `BACKEND_URL`

## Important Integration Details

### Single source of truth

PostgreSQL in the backend is now the only persistent source of complaint state.

### File handling

The backend keeps uploaded attachments. The agent fetches them through backend attachment APIs and processes local downloaded copies.

### Logging

Agent audit and progress events are persisted via backend log endpoints instead of local storage.

### Async processing

Backend-to-agent processing and draft generation calls are asynchronous.

## Files Added

### Database

- `database/04_agent_columns.sql`

### Backend

- `.../dto/AgentUpdateRequest.java`
- `.../dto/AgentDetailDto.java`
- `.../dto/GenerateDraftRequest.java`
- `.../dto/AgentLogDto.java`
- `.../entity/AgentLog.java`
- `.../repository/AgentLogRepository.java`
- `.../service/AgentLogService.java`
- `.../service/AgentClient.java`
- `.../event/AgentHttpPublisher.java`

### Agent

- `agent/backend_client.py`

## Files Modified

### Backend

- `.../entity/Complaint.java`
- `.../dto/ComplaintDto.java`
- `.../service/ComplaintService.java`
- `.../controller/ComplaintController.java`
- `.../config/SecurityConfig.java`
- `.../BcaApplication.java`
- `backend/src/main/resources/application.properties`

### Agent

- `agent/main.py`
- `agent/pipeline.py`
- `agent/extracting_agent/agent.py`
- `agent/categorization_agent/agent.py`
- `agent/data_retrieval_agent/agent.py`
- `agent/drafting_agent/agent.py`
- `agent/.env.example`

### Frontend

- `frontend/src/api/index.js`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/components/ComplaintModal.jsx`

### Infrastructure

- `docker-compose.dev.yml`

## File Deleted

- `.../event/StubAiProcessingPublisher.java`

## Current Completion State

### Completed

- Database schema integration
- Backend complaint model updates
- Backend agent update endpoints
- Backend complaint detail endpoint for agent reads
- Backend draft generation endpoint
- Backend agent log persistence
- Backend real HTTP publisher
- Agent backend client integration
- Agent process entrypoint
- Agent module migration away from SQLite
- Agent cleanup from active SQLite usage
- Frontend draft generation flow
- Frontend display of agent recommendation fields
- Docker and environment wiring

### Remaining

- Full end-to-end verification of the running stack

## Notes

- `agent/database.py` still exists in the repository but is no longer used by active integration code.
- The backend build may still depend on external Maven repository availability in the environment.
- Recreating the PostgreSQL volume may be required for fresh local initialization so the new SQL migration runs.
