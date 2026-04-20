-- =============================================================================
-- SOLV.ai — populate demo data (run in Supabase SQL Editor)
-- Safe to re-run: uses ON CONFLICT / DO UPDATE where possible.
-- Run AFTER your base tables exist (employees, customers, products, complaints…).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1) Schema alignment (employees roles, complaints.resolved_at)
-- -----------------------------------------------------------------------------
ALTER TABLE employees DROP CONSTRAINT IF EXISTS employees_role_check;
ALTER TABLE employees ADD CONSTRAINT employees_role_check CHECK (
  role IN ('admin', 'operational', 'call_center', 'quality_assurance')
);

ALTER TABLE complaints ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

-- -----------------------------------------------------------------------------
-- 2) Demo logins — password for all: admin123
--    (bcrypt hash cost 12, same as prisma/seed and 002_seed_data.sql)
-- -----------------------------------------------------------------------------
INSERT INTO employees (id, name, email, password_hash, role, department) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'Admin User', 'admin@company.com', '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi', 'admin', 'Management'),
  ('a0000000-0000-0000-0000-000000000002', 'Operations Manager', 'ops@company.com', '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi', 'operational', 'Operations'),
  ('a0000000-0000-0000-0000-000000000003', 'Support Agent', 'support@company.com', '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi', 'call_center', 'Customer Support'),
  ('a0000000-0000-0000-0000-000000000004', 'QA Lead', 'qa@company.com', '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi', 'quality_assurance', 'Quality Assurance')
ON CONFLICT (email) DO UPDATE SET
  name = EXCLUDED.name,
  password_hash = EXCLUDED.password_hash,
  role = EXCLUDED.role,
  department = EXCLUDED.department;

-- -----------------------------------------------------------------------------
-- 3) SLA — supports EITHER public.sla_config (singular) OR public.sla_configs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
  IF to_regclass('public.sla_config') IS NOT NULL THEN
    INSERT INTO sla_config (priority_level, response_time_hours, resolution_time_hours) VALUES
      ('High', 1, 4),
      ('Medium', 4, 24),
      ('Low', 24, 72)
    ON CONFLICT (priority_level) DO UPDATE SET
      response_time_hours = EXCLUDED.response_time_hours,
      resolution_time_hours = EXCLUDED.resolution_time_hours,
      updated_at = now();
  ELSIF to_regclass('public.sla_configs') IS NOT NULL THEN
    INSERT INTO sla_configs (priority, response_hours, resolve_hours) VALUES
      ('High', 1, 4),
      ('Medium', 4, 24),
      ('Low', 24, 72)
    ON CONFLICT (priority) DO UPDATE SET
      response_hours = EXCLUDED.response_hours,
      resolve_hours = EXCLUDED.resolve_hours,
      updated_at = now();
  END IF;
END $$;

-- -----------------------------------------------------------------------------
-- 4) Customers & products (needed for complaints FKs)
-- -----------------------------------------------------------------------------
INSERT INTO customers (id, name, email, phone) VALUES
  ('c0000001-0000-0000-0000-000000000001', 'Rajesh Kumar', 'rajesh.kumar@email.com', '+91-98765-43201'),
  ('c0000002-0000-0000-0000-000000000002', 'Priya Sharma', 'priya.sharma@email.com', '+91-98765-43202'),
  ('c0000003-0000-0000-0000-000000000003', 'Amit Patel', 'amit.patel@email.com', '+91-98765-43203'),
  ('c0000004-0000-0000-0000-000000000004', 'Sunita Verma', 'sunita.verma@email.com', '+91-98765-43204'),
  ('c0000005-0000-0000-0000-000000000005', 'Deepak Singh', 'deepak.singh@email.com', '+91-98765-43205')
ON CONFLICT (email) DO NOTHING;

INSERT INTO products (id, name, sku, category) VALUES
  ('p0000001-0000-0000-0000-000000000001', 'Parle-G Glucose Biscuits', 'PLG-001', 'Product'),
  ('p0000002-0000-0000-0000-000000000002', 'Frooti Mango Drink', 'FRT-002', 'Product'),
  ('p0000003-0000-0000-0000-000000000003', 'Marie Gold Biscuits', 'MRG-003', 'Product'),
  ('p0000004-0000-0000-0000-000000000004', 'Hide & Seek Cookies', 'HDS-004', 'Product'),
  ('p0000005-0000-0000-0000-000000000005', 'Bakery Fresh Bread', 'BFB-005', 'Product'),
  ('p0000006-0000-0000-0000-000000000006', 'Tropical Juice Pack', 'TJP-006', 'Product')
ON CONFLICT (sku) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 5) Sample complaints (skip if these IDs already exist)
-- -----------------------------------------------------------------------------
INSERT INTO complaints (
  id, complaint_text, category, priority, sentiment_score, source, status,
  immediate_action, resolution_steps, assigned_team, escalation_required,
  customer_response, customer_id, product_id, created_at, updated_at, resolved_at
) VALUES
  ('d0000d01-0000-4000-8000-000000000001', 'Plastic fragment found inside biscuit pack — safety concern.', 'Product', 'High', -0.85, 'call', 'in_progress', 'Hold batch review', NULL, 'Quality Assurance', true, NULL, 'c0000001-0000-0000-0000-000000000001', 'p0000001-0000-0000-0000-000000000001', now() - interval '2 days', now() - interval '1 day', NULL),
  ('d0000d02-0000-4000-8000-000000000002', 'Frooti tasted off; suspected storage issue.', 'Product', 'High', -0.7, 'email', 'assigned', 'Cold chain check', NULL, 'Supply Chain', false, NULL, 'c0000002-0000-0000-0000-000000000002', 'p0000002-0000-0000-0000-000000000002', now() - interval '3 days', now() - interval '2 days', NULL),
  ('d0000d03-0000-4000-8000-000000000003', 'Packaging hard to open — spills every time.', 'Packaging', 'Medium', -0.35, 'email', 'new', NULL, NULL, 'Packaging Team', false, NULL, 'c0000003-0000-0000-0000-000000000003', 'p0000001-0000-0000-0000-000000000001', now() - interval '5 days', now() - interval '5 days', NULL),
  ('d0000d04-0000-4000-8000-000000000004', 'Retailer selling above MRP.', 'Trade', 'High', -0.72, 'call', 'escalated', 'Trade audit', NULL, 'Trade Compliance', true, NULL, 'c0000004-0000-0000-0000-000000000004', 'p0000002-0000-0000-0000-000000000002', now() - interval '1 day', now() - interval '12 hours', NULL),
  ('d0000d05-0000-4000-8000-000000000005', 'Bread mold before expiry — quality issue.', 'Product', 'Medium', -0.55, 'walkin', 'resolved', 'Replacement sent', NULL, 'Quality Assurance', false, 'Thanks for your patience.', 'c0000005-0000-0000-0000-000000000005', 'p0000005-0000-0000-0000-000000000005', now() - interval '10 days', now() - interval '8 days', now() - interval '8 days'),
  ('d0000d06-0000-4000-8000-000000000006', 'Positive: great taste and freshness.', 'Product', 'Low', 0.82, 'email', 'resolved', NULL, NULL, 'Customer Success', false, 'Glad you enjoyed!', 'c0000002-0000-0000-0000-000000000002', 'p0000003-0000-0000-0000-000000000003', now() - interval '14 days', now() - interval '12 days', now() - interval '12 days'),
  ('d0000d07-0000-4000-8000-000000000007', 'Label peeled off juice pack in fridge.', 'Packaging', 'Low', -0.12, 'walkin', 'new', NULL, NULL, 'Packaging Team', false, NULL, 'c0000001-0000-0000-0000-000000000001', 'p0000006-0000-0000-0000-000000000006', now() - interval '4 hours', now() - interval '4 hours', NULL),
  ('d0000d08-0000-4000-8000-000000000008', 'Cookie box seal broken on delivery.', 'Packaging', 'High', -0.68, 'email', 'in_progress', NULL, NULL, 'Safety & Compliance', true, NULL, 'c0000003-0000-0000-0000-000000000003', 'p0000004-0000-0000-0000-000000000004', now() - interval '8 hours', now() - interval '4 hours', NULL),
  ('d0000d09-0000-4000-8000-000000000009', 'Wrong brand shipped from online order.', 'Trade', 'Medium', -0.45, 'email', 'assigned', NULL, NULL, 'E-Commerce Team', false, NULL, 'c0000004-0000-0000-0000-000000000004', 'p0000002-0000-0000-0000-000000000002', now() - interval '2 days', now() - interval '1 day', NULL),
  ('d0000d0a-0000-4000-8000-000000000010', 'Nutrition label mismatch vs website.', 'Packaging', 'Medium', -0.28, 'email', 'new', NULL, NULL, 'Regulatory Affairs', false, NULL, 'c0000005-0000-0000-0000-000000000005', 'p0000003-0000-0000-0000-000000000003', now() - interval '1 day', now() - interval '1 day', NULL)
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 6) Optional: more volume — after this succeeds, you can run:
--    supabase/migrations/002_seed_data.sql
--    for 50+ additional complaints and timeline rows.
-- =============================================================================
