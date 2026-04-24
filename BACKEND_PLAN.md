# Backend Implementation Plan

## Objective
Build Spring Boot REST API for customer data, complaints workflow, refusal reasons, and operator approval flow integrated with PostgreSQL schema.

## Scope
- Spring Boot project initialization
- Persistence layer (entities and repositories)
- Business services for customer, accounts, reasons, complaints, and email
- REST controllers for all required endpoints
- Error handling and API documentation

## Phase 1: Project Bootstrap
1. Initialize Spring Boot project in backend folder.
2. Add dependencies:
   - Spring Web
   - Spring Data JPA
   - Spring Security
   - PostgreSQL Driver
   - Lombok
   - MapStruct
   - springdoc-openapi
3. Configure Java version and build plugin settings.
4. Set application properties for database connection to bca-g6.

## Phase 2: Domain and Persistence
1. Implement JPA entities:
   - Customer
   - Operator
   - Complaint
   - ComplaintStatus
   - ComplaintStatusLog
   - ComplaintAttachment
   - BankAccount
   - RefusalReason
   - AuditLog
2. Define entity relationships, cascade rules, and fetch strategies.
3. Implement repositories:
   - CustomerRepository
   - OperatorRepository
   - ComplaintRepository
   - ComplaintStatusRepository
   - ComplaintStatusLogRepository
   - ComplaintAttachmentRepository
   - BankAccountRepository
   - RefusalReasonRepository

## Phase 3: Service Layer
1. CustomerService:
   - get customer by ID
2. BankAccountService:
   - get accounts by customer ID
3. RefusalReasonService:
   - get all refusal reasons
4. ComplaintService:
   - create complaint with randomly assigned refusal reason ID
   - update complaint status and insert complaint status log record
   - get complaints with optional status filter
   - get complaint details by ID
5. EmailService:
   - send draft email subject and body on approval action

## Phase 4: API Layer
1. Implement controllers and DTOs for:
   - GET /api/customers/{id}
   - GET /api/customers/{id}/accounts
   - GET /api/refusal-reasons
   - POST /api/complaints
   - GET /api/complaints (optional status filter)
   - GET /api/complaints/{id}
   - POST /api/complaints/{id}/approve
2. Validate request payloads and produce consistent error responses.
3. Add mapping layer (MapStruct) between entities and DTOs.

## Phase 5: Workflow and Integration Rules
1. On complaint creation:
   - persist complaint in Submitted status
   - assign random REFUSAL_REASON_ID
   - trigger async AI processing event placeholder
2. On approve endpoint:
   - validate complaint is in Draft Created status
   - send email using draft subject/body
   - set status to Completed
   - write status log and audit log
3. Ensure status transitions are validated and explicit.

## Phase 6: Cross-Cutting Concerns
1. Configure Swagger via springdoc-openapi at /swagger-ui.html.
2. Implement GlobalExceptionHandler using @ControllerAdvice.
3. Add basic security configuration suitable for development.
4. Add structured logging for key business actions.

## Testing Plan
1. Unit tests:
   - Service logic for complaint creation and approval transition
   - Status transition guards
2. Repository tests:
   - filtering complaints by status
3. Integration tests:
   - customer/accounts read endpoints
   - complaint creation and approval flow
4. API contract tests:
   - error response format from GlobalExceptionHandler

## Deliverables
- Buildable Spring Boot project in backend folder
- OpenAPI-documented endpoints
- Test suite for core workflows
- Configuration notes for local run

## Risks and Mitigations
- Risk: Random refusal reason assignment conflicts with frontend pre-selected value.
  - Mitigation: Backend remains source of truth and returns assigned value in response.
- Risk: AI async integration is not available during development.
  - Mitigation: Add event publisher interface with stub implementation for now.
