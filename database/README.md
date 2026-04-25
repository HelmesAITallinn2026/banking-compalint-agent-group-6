# Database Scripts

## Files
- 00_create_database.sql: creates role bca_g6_app and database bca-g6.
- 01_schema.sql: creates all required tables, constraints, indexes, and update trigger.
- 02_seed.sql: inserts required baseline records and mock data.
- 03_validate.sql: checks table presence, counts, and key constraints.
- 04_agent_columns.sql: adds AI processing columns and agent_log table.
- 05_seed_complaints.sql: seeds demo complaints at every pipeline status.

## Run Order
1. Run 00_create_database.sql as PostgreSQL admin user.
2. Connect to database bca-g6.
3. Run 01_schema.sql.
4. Run 02_seed.sql.
5. Run 04_agent_columns.sql.
6. Run 05_seed_complaints.sql.
7. Run 03_validate.sql.

## psql Example
Use these commands from project root:

```bash
psql -U postgres -f database/00_create_database.sql
psql -U bca_g6_app -d bca-g6 -f database/01_schema.sql
psql -U bca_g6_app -d bca-g6 -f database/02_seed.sql
psql -U bca_g6_app -d bca-g6 -f database/04_agent_columns.sql
psql -U bca_g6_app -d bca-g6 -f database/05_seed_complaints.sql
psql -U bca_g6_app -d bca-g6 -f database/03_validate.sql
```

## Rollback Notes
- Full reset:

```sql
DROP DATABASE IF EXISTS "bca-g6";
DROP ROLE IF EXISTS bca_g6_app;
```

- Schema-only reset (connected to bca-g6):

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```
