-- Run as a superuser or database admin.
-- Execute with psql while connected to the default postgres database.
-- This script is safe to re-run.

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bca_g6_app') THEN
        CREATE ROLE bca_g6_app LOGIN PASSWORD 'bca_g6_app_change_me';
    END IF;
END
$$;

SELECT 'CREATE DATABASE "bca-g6" OWNER bca_g6_app'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'bca-g6')
\gexec
