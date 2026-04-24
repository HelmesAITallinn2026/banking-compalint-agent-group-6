# Database TODOs
- Create new PostgreSQL database called bca-g6
- Create CUSTOMER table with columns ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, DOB, EMAIL
- Populate CUSTOMER table with 1 mocked customer
- Create OPERATOR table with columns ID, USERNAME, EMAIL, ROLE (OPERATOR/ADMIN), CREATED_DTTM
- Populate OPERATOR table with 1 mocked operator
- Create COMPLAINT_STATUS table with columns ID, NAME, COMMENT
- Populate COMPLAINT_STATUS table with values:
    - Submitted
    - Data Extracted (AI outcome)
    - Categorised (AI outcome)
    - Decision Recommendation Created (AI outcome) - it needs to be manually validated
    - Draft Created
    - Completed (draft reply was approved and sent)
- Create COMPLAINT table with columns ID, CUSTOMER_ID, STATUS_ID, CREATED_DTTM, UPDATED_DTTM, RESOLVED_DTTM, SUBJECT, TEXT, DRAFT_EMAIL_SUBJECT, DRAFT_EMAIL_BODY, OPERATOR_ID connected with CUSTOMER table via CUSTOMER_ID FK, connected with COMPLAINT_STATUS table via STATUS_ID FK, connected with OPERATOR table via OPERATOR_ID FK (nullable)
- Create BANK_ACCOUNT table with columns ID, CUSTOMER_ID, CREATED_DTTM, ACCOUNT_NUMBER, CURRENCY, BALANCE, ACCOUNT_TYPE (CHECKING/SAVINGS/CREDIT), connect with CUSTOMER table via CUSTOMER_ID, populate with 2-3 mock accounts per customer (different currencies)
- Create COMPLAINT_STATUS_LOG table with columns ID, COMPLAINT_ID, STATUS_ID, UPDATED_DTTM connect with COMPLAINT table via COMPLAINT_ID and COMPLAINT_STATUS table via STATUS_ID FK
- Create COMPLAINT_ATTACHMENT table with columns ID, COMPLAINT_ID, FILE_NAME, FILE_PATH, MIME_TYPE, FILE_SIZE, UPLOADED_DTTM, connect with COMPLAINT table via COMPLAINT_ID
- Create AUDIT_LOG table with columns ID, ENTITY_TYPE, ENTITY_ID, ACTION (CREATE/UPDATE/DELETE), PERFORMED_BY, PERFORMED_DTTM, DETAILS, No FK constraints — generic log table for all entities
- Create REFUSAL_REASON table with columns ID, NAME
- Populate REFUSAL_REASON table with values:
    1. Insufficient credit history
    2. Missing required documents
    3. Income below minimum threshold
    4. Outstanding debt obligations
    5. Property valuation too low
    6. Application data mismatch
- Add REFUSAL_REASON_ID column (nullable) to COMPLAINT table, connect with REFUSAL_REASON table via REFUSAL_REASON_ID FK

# Frontend TODOs
- Create simple Bank application, use React framework
- Configure API base URL via environment variable (REACT_APP_API_URL)
- Create Home page with 2 buttons: Dashboard, Customer View
  - Dashboard button navigates to /dashboard
  - Customer View button navigates to /customer/:id (use mock customer ID for demo)
- Dashboard page (/dashboard):
  - Create admin page with tabs mapped to complaint statuses:
    - Tab 1 — Submitted/In Process (AI): complaints with status "Submitted", complaints with statuses "Data Extracted", "Categorised", "Decision Recommendation Created"
    - Tab 2 — Draft Created (AI): complaints with status "Draft Created", show draft email subject and body, add Approve & Send button for operator
    - Tab 3 — Completed: complaints with status "Completed"
  - Each tab shows complaint cards with: customer name, subject, created date, current status
  - Clicking a complaint card opens complaint detail modal
- Customer Account page (/customer/:id):
  - Load customer data from API by ID
  - Create UI block for Account Details: First Name, Last Name, Date of Birth, Email
  - Create UI block for Financial Details: list of bank accounts with account number,
    currency, balance, account type; show total balance aggregated in EUR
  - Create UI block for Complaint Form:
    - Name and Surname [preloaded from API, read-only]
    - Subject (short text input)
    - Text (long text textarea)
    - Refusal Reason [dropdown preloaded from REFUSAL_REASON table via API, one random value auto-selected on page load, read-only]
    - File attachments (multiple files allowed)
    - Submit button — POST to /api/complaints

# Backend TODOs
- Create Java/Spring Boot backend project with dependencies: Spring Web, Spring Data JPA, Spring Security, PostgreSQL Driver, Lombok, MapStruct, springdoc-openapi
- Create connection to bca-g6 PostgreSQL DB via application.properties
- Create Entity classes (Hibernate): Customer, Operator, Complaint, ComplaintStatus, ComplaintStatusLog, ComplaintAttachment, BankAccount, RefusalReason, AuditLog
- Create Repository interfaces (Spring Data JPA): CustomerRepository, OperatorRepository, ComplaintRepository, ComplaintStatusRepository, ComplaintStatusLogRepository, ComplaintAttachmentRepository, BankAccountRepository, RefusalReasonRepository
- Create Service layer:
  - CustomerService — get customer by ID
  - BankAccountService — get accounts by customer ID
  - RefusalReasonService — get all refusal reasons
  - ComplaintService:
    - create complaint with randomly assigned REFUSAL_REASON_ID
    - update complaint status with COMPLAINT_STATUS_LOG entry
    - get complaints filtered by status
  - EmailService:
    - send email using draft subject and body when operator approves
- Create REST API layer:
  - GET  /api/customers/{id}            — get customer details
  - GET  /api/customers/{id}/accounts   — get bank accounts
  - GET  /api/refusal-reasons           — get all refusal reasons
  - POST /api/complaints                — create complaint, randomly assign REFUSAL_REASON_ID,
                                          trigger async AI processing (another application)
  - GET  /api/complaints                — get all complaints (optional filter by status)
  - GET  /api/complaints/{id}           — get complaint details
  - POST /api/complaints/{id}/approve   — operator approves draft, send email,
                                          set status "Completed"
- Configure Swagger UI via springdoc-openapi (available at /swagger-ui.html)
- Create GlobalExceptionHandler (@ControllerAdvice) for unified error responses