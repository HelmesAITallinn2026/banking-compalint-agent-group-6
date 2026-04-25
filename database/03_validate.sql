-- Run this script while connected to database: bca-g6
-- Provides quick verification output after schema + seed scripts.

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'customer',
      'operator',
      'complaint_status',
      'complaint',
      'bank_account',
      'complaint_status_log',
      'complaint_attachment',
      'audit_log',
      'refusal_reason'
  )
ORDER BY table_name;

SELECT COUNT(*) AS customer_count FROM customer;
SELECT COUNT(*) AS operator_count FROM operator;
SELECT COUNT(*) AS complaint_status_count FROM complaint_status;
SELECT COUNT(*) AS refusal_reason_count FROM refusal_reason;
SELECT COUNT(*) AS bank_account_count FROM bank_account;
SELECT COUNT(*) AS complaint_count FROM complaint;
SELECT COUNT(*) AS agent_log_count FROM agent_log;

SELECT c.id, cs.name AS status, c.subject
FROM complaint c
JOIN complaint_status cs ON cs.id = c.status_id
ORDER BY c.id;

SELECT
    c.conname AS constraint_name,
    c.conrelid::regclass AS table_name
FROM pg_constraint c
WHERE c.contype = 'f'
  AND c.conrelid::regclass::text IN (
      'complaint',
      'bank_account',
      'complaint_status_log',
      'complaint_attachment'
  )
ORDER BY table_name, constraint_name;

SELECT
    id,
    name
FROM complaint_status
ORDER BY id;

SELECT
    id,
    name
FROM refusal_reason
ORDER BY id;
