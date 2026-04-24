# Frontend Implementation Plan

## Objective
Build React application for customer complaint submission and operator dashboard aligned with backend APIs and complaint lifecycle.

## Scope
- React app setup in frontend folder
- Routing and page structure
- API client and environment-based configuration
- Dashboard, customer account, and complaint form flows
- Basic responsive styling and UX states

## Phase 1: Project Setup
1. Initialize React application in frontend folder.
2. Add routing and HTTP client libraries.
3. Add environment configuration:
   - REACT_APP_API_URL for API base URL
4. Define core app layout and navigation shell.

## Phase 2: Routing and Navigation
1. Configure routes:
   - /
   - /dashboard
   - /customer/:id
2. Build Home page with two primary actions:
   - Dashboard button to /dashboard
   - Customer View button to /customer/:id using mock customer ID

## Phase 3: API Integration Layer
1. Create centralized API client with base URL from REACT_APP_API_URL.
2. Implement API functions:
   - getCustomer(id)
   - getCustomerAccounts(id)
   - getRefusalReasons()
   - createComplaint(payload, attachments)
   - getComplaints(status?)
   - getComplaint(id)
   - approveComplaint(id)
3. Add reusable error handling and loading-state utilities.

## Phase 4: Customer Account Page
1. Account Details block:
   - first name, last name, DOB, email
2. Financial Details block:
   - accounts table/list with account number, currency, balance, account type
   - compute and display total balance in EUR
3. Complaint Form block:
   - preloaded read-only Name and Surname
   - subject input
   - long text textarea
   - refusal reason dropdown loaded from API
   - auto-select one random refusal reason on initial load and keep read-only
   - multiple file attachments input
   - submit to POST /api/complaints

## Phase 5: Dashboard Page
1. Build tabbed view with three tabs:
   - Submitted/In Process (Submitted, Data Extracted, Categorised, Decision Recommendation Created)
   - Draft Created (Draft Created)
   - Completed (Completed)
2. In each tab, render complaint cards with:
   - customer name
   - subject
   - created date
   - current status
3. Implement complaint detail modal on card click.
4. In Draft Created tab, show draft email subject and body and add Approve and Send button.

## Phase 6: UX Quality
1. Add loading, empty, and error states for each data block.
2. Add success and failure feedback for complaint submission and approval actions.
3. Ensure mobile and desktop responsive behavior.
4. Keep consistent visual style according to project design notes.

## Testing Plan
1. Component tests for:
   - complaint form validation and submission
   - dashboard tab filtering behavior
2. Integration tests for API-driven pages using mocked endpoints.
3. End-to-end smoke tests:
   - create complaint as customer
   - approve draft complaint as operator

## Deliverables
- Buildable React project in frontend folder
- Environment-driven API configuration
- Customer and dashboard flows connected to backend APIs
- Basic automated tests for critical interactions

## Risks and Mitigations
- Risk: Frontend selected refusal reason differs from backend random assignment.
  - Mitigation: After create response, show backend-assigned refusal reason as final value.
- Risk: EUR total depends on missing conversion rates.
  - Mitigation: Show total based on backend-provided converted amount when available, otherwise use documented fallback.
