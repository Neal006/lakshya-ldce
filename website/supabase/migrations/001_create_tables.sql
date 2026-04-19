-- ============================================
-- SOLV.ai (TS-14) - Supabase Database Schema
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- EMPLOYEES (replaces User table for auth)
-- ============================================
CREATE TABLE IF NOT EXISTS employees (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'call_center' CHECK (role IN ('admin', 'operational', 'call_center')),
  department TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- CUSTOMERS
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  phone TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- PRODUCTS
-- ============================================
CREATE TABLE IF NOT EXISTS products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  sku TEXT UNIQUE NOT NULL,
  category TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- COMPLAINTS
-- ============================================
CREATE TABLE IF NOT EXISTS complaints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  complaint_text TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('Product', 'Packaging', 'Trade')),
  priority TEXT NOT NULL CHECK (priority IN ('High', 'Medium', 'Low')),
  sentiment_score DOUBLE PRECISION NOT NULL DEFAULT 0,
  source TEXT NOT NULL CHECK (source IN ('email', 'call', 'walkin')),
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'assigned', 'in_progress', 'escalated', 'resolved', 'closed')),
  immediate_action TEXT,
  resolution_steps JSONB,
  assigned_team TEXT,
  escalation_required BOOLEAN NOT NULL DEFAULT false,
  customer_response TEXT,
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

-- ============================================
-- COMPLAINT TIMELINE
-- ============================================
CREATE TABLE IF NOT EXISTS complaint_timeline (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  performed_by TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- SLA CONFIG
-- ============================================
CREATE TABLE IF NOT EXISTS sla_configs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  priority TEXT NOT NULL UNIQUE CHECK (priority IN ('High', 'Medium', 'Low')),
  response_hours INTEGER NOT NULL,
  resolve_hours INTEGER NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- DAILY METRICS
-- ============================================
CREATE TABLE IF NOT EXISTS daily_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  date DATE NOT NULL UNIQUE,
  total_complaints INTEGER NOT NULL DEFAULT 0,
  high_priority INTEGER NOT NULL DEFAULT 0,
  medium_priority INTEGER NOT NULL DEFAULT 0,
  low_priority INTEGER NOT NULL DEFAULT 0,
  product_count INTEGER NOT NULL DEFAULT 0,
  packaging_count INTEGER NOT NULL DEFAULT 0,
  trade_count INTEGER NOT NULL DEFAULT 0,
  avg_sentiment DOUBLE PRECISION NOT NULL DEFAULT 0,
  resolved_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_priority ON complaints(priority);
CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);
CREATE INDEX IF NOT EXISTS idx_complaints_product_id ON complaints(product_id);
CREATE INDEX IF NOT EXISTS idx_complaints_customer_id ON complaints(customer_id);
CREATE INDEX IF NOT EXISTS idx_complaints_source ON complaints(source);
CREATE INDEX IF NOT EXISTS idx_complaint_timeline_complaint_id ON complaint_timeline(complaint_id);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);

-- ============================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE sla_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_metrics ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS POLICIES - allow service role full access
-- ============================================
CREATE POLICY "Service role full access on employees" ON employees FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access on customers" ON customers FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access on products" ON products FOR ALL USING (true);
CREATE POLICY "Service role full access on complaints" ON complaints FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access on complaint_timeline" ON complaint_timeline FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access on sla_configs" ON sla_configs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access on daily_metrics" ON daily_metrics FOR ALL USING (auth.role() = 'service_role');

-- Allow anon key to read products (already confirmed working)
CREATE POLICY "Public read access on products" ON products FOR SELECT USING (true);

-- Allow anon key to read complaints (for SSE/event streams)
CREATE POLICY "Public read access on complaints" ON complaints FOR SELECT USING (true);

-- Allow anon key to read complaint_timeline
CREATE POLICY "Public read access on complaint_timeline" ON complaint_timeline FOR SELECT USING (true);