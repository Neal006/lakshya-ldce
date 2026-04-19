-- =============================================================================
-- Clear dummy / seed data before loading real data (e.g. text_classifier/data/data.csv)
-- Supabase → SQL Editor → paste → Run
--
-- REMOVES: complaints, complaint_timeline, daily_metrics, customers, products
-- KEEPS: employees (logins), SLA config (sla_config / sla_configs)
-- =============================================================================

BEGIN;

-- One statement: Postgres truncates in a safe order for FKs. CASCADE clears dependent rows.
TRUNCATE TABLE
  complaint_timeline,
  complaints,
  daily_metrics,
  customers,
  products
CASCADE;

COMMIT;

-- If `daily_metrics` does not exist in your project, use this instead:
-- BEGIN;
-- TRUNCATE TABLE complaint_timeline, complaints, customers, products CASCADE;
-- COMMIT;
