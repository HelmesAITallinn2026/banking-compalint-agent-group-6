# Database Implementation Plan

## Objective
Create and initialize PostgreSQL database bca-g6 with all required tables, relations, and seed data needed by the complaint handling application.

## Scope
- Database creation and connection baseline
- Schema creation for all domain tables
- Foreign key and constraint setup
- Seed data for required lookup and demo entities
- Basic validation queries and handover notes

## Phase 1: Setup and Baseline
1. Install or confirm PostgreSQL availability.
2. Create database bca-g6.
3. Create a dedicated application user with least-privilege access.
4. Define naming conventions for tables, constraints, and indexes.

## Phase 2: Core Schema
1. Create table CUSTOMER:
   - ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, DOB, EMAIL
2. Create table OPERATOR:
   - ID, USERNAME, EMAIL, ROLE, CREATED_DTTM
3. Create table COMPLAINT_STATUS:
   - ID, NAME, COMMENT
4. Create table REFUSAL_REASON:
   - ID, NAME

## Phase 3: Complaint Domain Schema
1. Create table COMPLAINT:
   - ID, CUSTOMER_ID, STATUS_ID, CREATED_DTTM, UPDATED_DTTM, RESOLVED_DTTM
   - SUBJECT, TEXT, DRAFT_EMAIL_SUBJECT, DRAFT_EMAIL_BODY
   - OPERATOR_ID (nullable), REFUSAL_REASON_ID (nullable)
2. Add FKs from COMPLAINT to:
   - CUSTOMER(ID)
   - COMPLAINT_STATUS(ID)
   - OPERATOR(ID)
   - REFUSAL_REASON(ID)
3. Create table COMPLAINT_STATUS_LOG:
   - ID, COMPLAINT_ID, STATUS_ID, UPDATED_DTTM
4. Add FKs from COMPLAINT_STATUS_LOG to COMPLAINT(ID) and COMPLAINT_STATUS(ID).
5. Create table COMPLAINT_ATTACHMENT:
   - ID, COMPLAINT_ID, FILE_NAME, FILE_PATH, MIME_TYPE, FILE_SIZE, UPLOADED_DTTM
6. Add FK from COMPLAINT_ATTACHMENT to COMPLAINT(ID).

## Phase 4: Customer Finance and Audit Schema
1. Create table BANK_ACCOUNT:
   - ID, CUSTOMER_ID, CREATED_DTTM, ACCOUNT_NUMBER, CURRENCY, BALANCE, ACCOUNT_TYPE
2. Add FK from BANK_ACCOUNT to CUSTOMER(ID).
3. Create table AUDIT_LOG:
   - ID, ENTITY_TYPE, ENTITY_ID, ACTION, PERFORMED_BY, PERFORMED_DTTM, DETAILS
   - Keep without FK constraints by design.

## Phase 5: Seed Data
1. Insert one mocked CUSTOMER row.
2. Insert one mocked OPERATOR row.
3. Insert COMPLAINT_STATUS values:
   - Submitted
   - Data Extracted
   - Categorised
   - Decision Recommendation Created
   - Draft Created
   - Completed
4. Insert all six REFUSAL_REASON values from architecture notes.
5. Insert 2-3 BANK_ACCOUNT records for the mocked customer across different currencies.

## Phase 6: Data Quality and Performance Baseline
1. Add NOT NULL constraints where required.
2. Add uniqueness constraints:
   - CUSTOMER.EMAIL
   - OPERATOR.USERNAME
   - OPERATOR.EMAIL
   - BANK_ACCOUNT.ACCOUNT_NUMBER
3. Add indexes for common filters:
   - COMPLAINT.STATUS_ID
   - COMPLAINT.CUSTOMER_ID
   - COMPLAINT.CREATED_DTTM
   - COMPLAINT_STATUS_LOG.COMPLAINT_ID
4. Add check constraints:
   - OPERATOR.ROLE in (OPERATOR, ADMIN)
   - BANK_ACCOUNT.ACCOUNT_TYPE in (CHECKING, SAVINGS, CREDIT)

## Validation Checklist
- Schema can be created from scratch on an empty database.
- All expected foreign keys exist and validate correctly.
- Seed script is idempotent or clearly documented as one-time.
- Querying complaint list with status filters is fast on sample data.
- Customer page data can be read from CUSTOMER and BANK_ACCOUNT without null-related issues.

## Deliverables
- SQL script: schema creation
- SQL script: seed data
- Readme section with run order and rollback notes

## Risks and Mitigations
- Risk: Mismatch between DB enum-like values and backend constants.
  - Mitigation: Keep lookup values in migration scripts and backend constants synchronized.
- Risk: Currency conversion for total EUR not represented in schema.
  - Mitigation: Keep conversion logic in backend service and document conversion rate source.
