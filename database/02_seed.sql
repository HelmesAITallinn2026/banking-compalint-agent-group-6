-- Run this script while connected to database: bca-g6
-- Idempotent seed for baseline data.

BEGIN;

INSERT INTO customer (first_name, middle_name, last_name, dob, email)
VALUES ('John', 'A', 'Doe', DATE '1990-05-12', 'john.doe@example.com')
ON CONFLICT (email)
DO UPDATE SET
    first_name = EXCLUDED.first_name,
    middle_name = EXCLUDED.middle_name,
    last_name = EXCLUDED.last_name,
    dob = EXCLUDED.dob;

INSERT INTO operator (username, email, role, created_dttm)
VALUES ('operator.demo', 'operator.demo@bank.example', 'OPERATOR', NOW())
ON CONFLICT (username)
DO UPDATE SET
    email = EXCLUDED.email,
    role = EXCLUDED.role;

INSERT INTO complaint_status (id, name, comment)
VALUES
    (1, 'Submitted', 'Complaint was submitted by customer'),
    (2, 'Data Extracted', 'AI extracted relevant data from complaint'),
    (3, 'Categorised', 'AI categorised complaint'),
    (4, 'Decision Recommendation Created', 'AI generated recommendation, operator validation required'),
    (5, 'Draft Created', 'Draft response generated'),
    (6, 'Completed', 'Draft approved and sent to customer')
ON CONFLICT (id)
DO UPDATE SET
    name = EXCLUDED.name,
    comment = EXCLUDED.comment;

SELECT setval(
    pg_get_serial_sequence('complaint_status', 'id'),
    (SELECT GREATEST(COALESCE(MAX(id), 1), 1) FROM complaint_status),
    true
);

INSERT INTO refusal_reason (id, name)
VALUES
    (1, 'Insufficient credit history'),
    (2, 'Missing required documents'),
    (3, 'Income below minimum threshold'),
    (4, 'Outstanding debt obligations'),
    (5, 'Property valuation too low'),
    (6, 'Application data mismatch')
ON CONFLICT (id)
DO UPDATE SET
    name = EXCLUDED.name;

SELECT setval(
    pg_get_serial_sequence('refusal_reason', 'id'),
    (SELECT GREATEST(COALESCE(MAX(id), 1), 1) FROM refusal_reason),
    true
);

WITH target_customer AS (
    SELECT id
    FROM customer
    WHERE email = 'john.doe@example.com'
    LIMIT 1
)
INSERT INTO bank_account (customer_id, account_number, currency, balance, account_type)
SELECT id, 'DE89370400440532013000', 'EUR', 12500.50, 'CHECKING'
FROM target_customer
ON CONFLICT (account_number)
DO UPDATE SET
    customer_id = EXCLUDED.customer_id,
    currency = EXCLUDED.currency,
    balance = EXCLUDED.balance,
    account_type = EXCLUDED.account_type;

WITH target_customer AS (
    SELECT id
    FROM customer
    WHERE email = 'john.doe@example.com'
    LIMIT 1
)
INSERT INTO bank_account (customer_id, account_number, currency, balance, account_type)
SELECT id, 'US29NWBK60161331926819', 'USD', 5420.75, 'SAVINGS'
FROM target_customer
ON CONFLICT (account_number)
DO UPDATE SET
    customer_id = EXCLUDED.customer_id,
    currency = EXCLUDED.currency,
    balance = EXCLUDED.balance,
    account_type = EXCLUDED.account_type;

WITH target_customer AS (
    SELECT id
    FROM customer
    WHERE email = 'john.doe@example.com'
    LIMIT 1
)
INSERT INTO bank_account (customer_id, account_number, currency, balance, account_type)
SELECT id, 'GB7630006000011234567890189', 'GBP', 2310.00, 'CREDIT'
FROM target_customer
ON CONFLICT (account_number)
DO UPDATE SET
    customer_id = EXCLUDED.customer_id,
    currency = EXCLUDED.currency,
    balance = EXCLUDED.balance,
    account_type = EXCLUDED.account_type;

COMMIT;
