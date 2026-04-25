-- Run this script while connected to database: bca-g6
-- After 04_agent_columns.sql.
-- Seeds demo complaints at every pipeline status for frontend / demo work.

BEGIN;

-- ── Extra customers ────────────────────────────────────────────

INSERT INTO customer (first_name, middle_name, last_name, dob, email)
VALUES ('Jane', NULL, 'Smith', DATE '1985-08-23', 'jane.smith@example.com')
ON CONFLICT (email) DO UPDATE SET
    first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, dob = EXCLUDED.dob;

INSERT INTO customer (first_name, middle_name, last_name, dob, email)
VALUES ('Maria', 'L', 'Garcia', DATE '1992-03-14', 'maria.garcia@example.com')
ON CONFLICT (email) DO UPDATE SET
    first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, dob = EXCLUDED.dob;

INSERT INTO customer (first_name, middle_name, last_name, dob, email)
VALUES ('Robert', NULL, 'Johnson', DATE '1978-11-02', 'robert.johnson@example.com')
ON CONFLICT (email) DO UPDATE SET
    first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, dob = EXCLUDED.dob;

INSERT INTO customer (first_name, middle_name, last_name, dob, email)
VALUES ('Emily', 'R', 'Chen', DATE '1995-06-30', 'emily.chen@example.com')
ON CONFLICT (email) DO UPDATE SET
    first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, dob = EXCLUDED.dob;

-- ── Bank accounts for new customers ───────────────────────────

INSERT INTO bank_account (customer_id, account_number, currency, balance, account_type)
SELECT id, 'EE382200221020145685', 'EUR', 8750.00, 'CHECKING'
FROM customer WHERE email = 'jane.smith@example.com'
ON CONFLICT (account_number) DO UPDATE SET balance = EXCLUDED.balance;

INSERT INTO bank_account (customer_id, account_number, currency, balance, account_type)
SELECT id, 'EE501010220012345678', 'EUR', 3200.50, 'SAVINGS'
FROM customer WHERE email = 'maria.garcia@example.com'
ON CONFLICT (account_number) DO UPDATE SET balance = EXCLUDED.balance;

INSERT INTO bank_account (customer_id, account_number, currency, balance, account_type)
SELECT id, 'EE701700017000123456', 'EUR', 15400.00, 'CHECKING'
FROM customer WHERE email = 'robert.johnson@example.com'
ON CONFLICT (account_number) DO UPDATE SET balance = EXCLUDED.balance;

INSERT INTO bank_account (customer_id, account_number, currency, balance, account_type)
SELECT id, 'EE601400017000234567', 'EUR', 920.75, 'CREDIT'
FROM customer WHERE email = 'emily.chen@example.com'
ON CONFLICT (account_number) DO UPDATE SET balance = EXCLUDED.balance;

-- ── Complaint 1: Submitted (status_id = 1) ────────────────────

INSERT INTO complaint (id, customer_id, status_id, subject, text, created_dttm, updated_dttm)
SELECT 1001, c.id, 1,
       'Unauthorized ATM withdrawal',
       'I noticed an ATM withdrawal of 200 EUR on 2026-04-20 that I did not make. My card was in my possession the whole time. Please investigate and reverse this transaction.',
       NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours'
FROM customer c WHERE c.email = 'jane.smith@example.com'
ON CONFLICT (id) DO UPDATE SET
    status_id = EXCLUDED.status_id, subject = EXCLUDED.subject, text = EXCLUDED.text;

-- ── Complaint 2: Data Extracted (status_id = 2) ───────────────

INSERT INTO complaint (id, customer_id, status_id, subject, text, extracted_data, created_dttm, updated_dttm)
SELECT 1002, c.id, 2,
       'Double charge on credit card',
       'I was charged twice for a purchase at Electronics Store on 2026-04-18. The amount of 149.99 EUR appeared two times on my statement. I only made one purchase.',
       '{"merchant": "Electronics Store", "amount": 149.99, "currency": "EUR", "transaction_date": "2026-04-18", "occurrences": 2, "customer_account": "EE501010220012345678"}',
       NOW() - INTERVAL '5 hours', NOW() - INTERVAL '4 hours'
FROM customer c WHERE c.email = 'maria.garcia@example.com'
ON CONFLICT (id) DO UPDATE SET
    status_id = EXCLUDED.status_id, subject = EXCLUDED.subject, text = EXCLUDED.text, extracted_data = EXCLUDED.extracted_data;

-- ── Complaint 3: Categorised (status_id = 3) ──────────────────

INSERT INTO complaint (id, customer_id, status_id, subject, text, extracted_data, category, created_dttm, updated_dttm)
SELECT 1003, c.id, 3,
       'Loan interest rate discrepancy',
       'My loan agreement states a fixed interest rate of 3.5%, but my latest statement shows 4.1%. This has been going on for two months. I request a correction and reimbursement of the overcharged interest.',
       '{"loan_type": "personal", "agreed_rate": 3.5, "charged_rate": 4.1, "duration_months": 2, "customer_account": "EE701700017000123456"}',
       'Loan / Interest Rate',
       NOW() - INTERVAL '1 day', NOW() - INTERVAL '20 hours'
FROM customer c WHERE c.email = 'robert.johnson@example.com'
ON CONFLICT (id) DO UPDATE SET
    status_id = EXCLUDED.status_id, subject = EXCLUDED.subject, text = EXCLUDED.text, extracted_data = EXCLUDED.extracted_data, category = EXCLUDED.category;

-- ── Complaint 4: Decision Recommendation Created (status_id = 4)

INSERT INTO complaint (id, customer_id, status_id, subject, text, extracted_data, category, recommendation, recommendation_reasoning, created_dttm, updated_dttm)
SELECT 1004, c.id, 4,
       'Failed wire transfer with fee charged',
       'I initiated a wire transfer of 5000 EUR to account GB29NWBK60161331926819 on 2026-04-15. The transfer failed but I was still charged a 25 EUR fee. I would like the fee refunded.',
       '{"transfer_amount": 5000, "currency": "EUR", "destination_account": "GB29NWBK60161331926819", "transfer_date": "2026-04-15", "fee_charged": 25, "customer_account": "DE89370400440532013000"}',
       'Wire Transfer / Fees',
       'POSITIVE',
       'The customer was charged a fee for a failed wire transfer. Bank policy states that fees for failed outgoing transfers caused by system errors should be refunded. The transfer failure was due to a timeout in the SWIFT network, which is not the customer''s fault. Recommend full refund of the 25 EUR fee.',
       NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day'
FROM customer c WHERE c.email = 'john.doe@example.com'
ON CONFLICT (id) DO UPDATE SET
    status_id = EXCLUDED.status_id, subject = EXCLUDED.subject, text = EXCLUDED.text, extracted_data = EXCLUDED.extracted_data,
    category = EXCLUDED.category, recommendation = EXCLUDED.recommendation, recommendation_reasoning = EXCLUDED.recommendation_reasoning;

-- ── Complaint 5: Draft Created (status_id = 5) ────────────────

INSERT INTO complaint (id, customer_id, status_id, subject, text, extracted_data, category, recommendation, recommendation_reasoning, draft_email_subject, draft_email_body, created_dttm, updated_dttm)
SELECT 1005, c.id, 5,
       'Overdraft fee dispute',
       'I was charged a 35 EUR overdraft fee on 2026-04-10. I had set up a salary deposit that was delayed by one day due to a bank holiday. I believe this fee should be waived as the situation was beyond my control.',
       '{"fee_amount": 35, "currency": "EUR", "fee_date": "2026-04-10", "account_type": "CREDIT", "customer_account": "EE601400017000234567", "salary_deposit_expected": "2026-04-09", "salary_deposit_actual": "2026-04-10"}',
       'Account Fees / Overdraft',
       'POSITIVE',
       'The overdraft was caused by a one-day delay in salary deposit due to a bank holiday. Customer has no prior history of overdrafts. Bank policy allows fee waivers for first-time occurrences caused by external factors. Recommend waiving the 35 EUR fee.',
       'Re: Overdraft Fee Dispute — Resolution',
       E'Dear Emily,\n\nThank you for contacting us regarding the overdraft fee charged to your account on 10 April 2026.\n\nWe have reviewed your case and can confirm that the fee was triggered by a one-day delay in your salary deposit caused by a bank holiday. As this is a first-time occurrence and was outside your control, we have decided to waive the 35 EUR overdraft fee.\n\nThe credit will appear on your account within 1–2 business days.\n\nIf you have any further questions, please do not hesitate to reach out.\n\nKind regards,\nHelmes Bank Customer Support',
       NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days'
FROM customer c WHERE c.email = 'emily.chen@example.com'
ON CONFLICT (id) DO UPDATE SET
    status_id = EXCLUDED.status_id, subject = EXCLUDED.subject, text = EXCLUDED.text, extracted_data = EXCLUDED.extracted_data,
    category = EXCLUDED.category, recommendation = EXCLUDED.recommendation, recommendation_reasoning = EXCLUDED.recommendation_reasoning,
    draft_email_subject = EXCLUDED.draft_email_subject, draft_email_body = EXCLUDED.draft_email_body;

-- ── Complaint 6: Completed (status_id = 6) ────────────────────

INSERT INTO complaint (id, customer_id, status_id, subject, text, extracted_data, category, recommendation, recommendation_reasoning, draft_email_subject, draft_email_body, resolved_dttm, created_dttm, updated_dttm)
SELECT 1006, c.id, 6,
       'Debit card fraud',
       'My debit card was used for three online purchases totalling 450 EUR on 2026-04-05 that I did not authorize. I have since blocked my card. Please refund the fraudulent transactions.',
       '{"transactions": [{"merchant": "OnlineShop A", "amount": 150}, {"merchant": "OnlineShop B", "amount": 200}, {"merchant": "OnlineShop C", "amount": 100}], "total": 450, "currency": "EUR", "fraud_date": "2026-04-05", "card_blocked": true, "customer_account": "EE382200221020145685"}',
       'Card Fraud / Unauthorized Transactions',
       'POSITIVE',
       'Customer reports unauthorized online transactions. Card has been blocked. Transaction patterns are consistent with card-not-present fraud. Bank fraud policy mandates full reimbursement for verified unauthorized transactions within 60 days. Recommend full refund of 450 EUR.',
       'Re: Debit Card Fraud Report — Resolution',
       E'Dear Jane,\n\nThank you for reporting the unauthorized transactions on your debit card.\n\nAfter a thorough investigation, we have confirmed that the three transactions totalling 450 EUR were fraudulent. We have processed a full refund to your account.\n\nYour new debit card has been dispatched and should arrive within 3–5 business days.\n\nThank you for your patience, and please contact us if you need anything else.\n\nKind regards,\nHelmes Bank Customer Support',
       NOW() - INTERVAL '1 day',
       NOW() - INTERVAL '5 days', NOW() - INTERVAL '1 day'
FROM customer c WHERE c.email = 'jane.smith@example.com'
ON CONFLICT (id) DO UPDATE SET
    status_id = EXCLUDED.status_id, subject = EXCLUDED.subject, text = EXCLUDED.text, extracted_data = EXCLUDED.extracted_data,
    category = EXCLUDED.category, recommendation = EXCLUDED.recommendation, recommendation_reasoning = EXCLUDED.recommendation_reasoning,
    draft_email_subject = EXCLUDED.draft_email_subject, draft_email_body = EXCLUDED.draft_email_body, resolved_dttm = EXCLUDED.resolved_dttm;

-- ── Status logs ───────────────────────────────────────────────

-- Each complaint gets a log entry for each status it has passed through.
-- Complaint 1: Submitted
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1001, 1, NOW() - INTERVAL '2 hours'
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1001 AND status_id = 1);

-- Complaint 2: Submitted → Data Extracted
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1002, 1, NOW() - INTERVAL '5 hours'
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1002 AND status_id = 1);
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1002, 2, NOW() - INTERVAL '4 hours'
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1002 AND status_id = 2);

-- Complaint 3: Submitted → Data Extracted → Categorised
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1003, 1, NOW() - INTERVAL '1 day'
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1003 AND status_id = 1);
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1003, 2, NOW() - INTERVAL '23 hours'
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1003 AND status_id = 2);
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1003, 3, NOW() - INTERVAL '20 hours'
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1003 AND status_id = 3);

-- Complaint 4: Submitted → ... → Recommendation Created
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1004, s.id, NOW() - INTERVAL '2 days' + (s.id * INTERVAL '2 hours')
FROM generate_series(1, 4) AS s(id)
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1004 AND status_id = s.id);

-- Complaint 5: Submitted → ... → Draft Created
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1005, s.id, NOW() - INTERVAL '3 days' + (s.id * INTERVAL '3 hours')
FROM generate_series(1, 5) AS s(id)
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1005 AND status_id = s.id);

-- Complaint 6: Submitted → ... → Completed
INSERT INTO complaint_status_log (complaint_id, status_id, updated_dttm)
SELECT 1006, s.id, NOW() - INTERVAL '5 days' + (s.id * INTERVAL '4 hours')
FROM generate_series(1, 6) AS s(id)
WHERE NOT EXISTS (SELECT 1 FROM complaint_status_log WHERE complaint_id = 1006 AND status_id = s.id);

-- ── Agent logs ────────────────────────────────────────────────

-- Extraction logs for complaints 2+
INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1002, 'extraction_agent', 'extract_data', '{"complaint_id": 1002}',
       'Parsed complaint text. Identified merchant name, amount, currency, date, and duplicate charge pattern.',
       '{"extracted_fields": ["merchant", "amount", "currency", "transaction_date", "occurrences"]}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1002 AND agent_name = 'extraction_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1003, 'extraction_agent', 'extract_data', '{"complaint_id": 1003}',
       'Parsed complaint text. Identified loan type, agreed vs charged interest rates, and duration of discrepancy.',
       '{"extracted_fields": ["loan_type", "agreed_rate", "charged_rate", "duration_months"]}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1003 AND agent_name = 'extraction_agent');

-- Categorization logs for complaints 3+
INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1003, 'categorization_agent', 'categorize', '{"complaint_id": 1003}',
       'Complaint involves loan interest rate mismatch. Mapped to Loan / Interest Rate category.',
       '{"category": "Loan / Interest Rate"}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1003 AND agent_name = 'categorization_agent');

-- Recommendation logs for complaints 4+
INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1004, 'extraction_agent', 'extract_data', '{"complaint_id": 1004}',
       'Parsed wire transfer details including amount, destination, date, and fee.',
       '{"extracted_fields": ["transfer_amount", "destination_account", "transfer_date", "fee_charged"]}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1004 AND agent_name = 'extraction_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1004, 'categorization_agent', 'categorize', '{"complaint_id": 1004}',
       'Complaint involves failed wire transfer and associated fee. Mapped to Wire Transfer / Fees.',
       '{"category": "Wire Transfer / Fees"}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1004 AND agent_name = 'categorization_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1004, 'recommendation_agent', 'recommend', '{"complaint_id": 1004}',
       'Fee charged for failed transfer due to SWIFT timeout. Bank policy supports refund. Recommend POSITIVE.',
       '{"recommendation": "POSITIVE", "reasoning": "System error caused failure; policy mandates refund."}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1004 AND agent_name = 'recommendation_agent');

-- Draft logs for complaints 5+
INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1005, 'extraction_agent', 'extract_data', '{"complaint_id": 1005}',
       'Parsed overdraft fee details including amount, date, and salary deposit delay.',
       '{"extracted_fields": ["fee_amount", "fee_date", "salary_deposit_expected", "salary_deposit_actual"]}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1005 AND agent_name = 'extraction_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1005, 'categorization_agent', 'categorize', '{"complaint_id": 1005}',
       'Complaint involves overdraft fee. Mapped to Account Fees / Overdraft.',
       '{"category": "Account Fees / Overdraft"}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1005 AND agent_name = 'categorization_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1005, 'recommendation_agent', 'recommend', '{"complaint_id": 1005}',
       'First-time overdraft caused by bank holiday delay. Policy allows waiver. Recommend POSITIVE.',
       '{"recommendation": "POSITIVE"}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1005 AND agent_name = 'recommendation_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1005, 'drafting_agent', 'draft_response', '{"complaint_id": 1005}',
       'Generated customer-facing email confirming fee waiver with expected timeline.',
       '{"draft_generated": true}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1005 AND agent_name = 'drafting_agent');

-- Completed complaint 6: all agent logs
INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1006, 'extraction_agent', 'extract_data', '{"complaint_id": 1006}',
       'Parsed fraud report. Identified three unauthorized transactions, total amount, and card block status.',
       '{"extracted_fields": ["transactions", "total", "fraud_date", "card_blocked"]}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1006 AND agent_name = 'extraction_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1006, 'categorization_agent', 'categorize', '{"complaint_id": 1006}',
       'Complaint involves unauthorized card transactions. Mapped to Card Fraud / Unauthorized Transactions.',
       '{"category": "Card Fraud / Unauthorized Transactions"}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1006 AND agent_name = 'categorization_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1006, 'recommendation_agent', 'recommend', '{"complaint_id": 1006}',
       'Verified fraud pattern. Bank fraud policy mandates reimbursement within 60 days. Recommend POSITIVE.',
       '{"recommendation": "POSITIVE"}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1006 AND agent_name = 'recommendation_agent');

INSERT INTO agent_log (complaint_id, agent_name, action_type, input_context, reasoning_process, output_context)
SELECT 1006, 'drafting_agent', 'draft_response', '{"complaint_id": 1006}',
       'Generated resolution email confirming full refund and new card dispatch.',
       '{"draft_generated": true}'
WHERE NOT EXISTS (SELECT 1 FROM agent_log WHERE complaint_id = 1006 AND agent_name = 'drafting_agent');

COMMIT;
