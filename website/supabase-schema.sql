-- TS-14 Complaint Management System Schema
-- Run this in the Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Products table
CREATE TABLE IF NOT EXISTS products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  sku VARCHAR(100) UNIQUE NOT NULL,
  category VARCHAR(100) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Complaints table
CREATE TABLE IF NOT EXISTS complaints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  complaint_text TEXT NOT NULL,
  category VARCHAR(50) NOT NULL CHECK (category IN ('Product', 'Packaging', 'Trade')),
  priority VARCHAR(20) NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
  sentiment_score NUMERIC(5,4) DEFAULT 0.0000,
  source VARCHAR(20) NOT NULL CHECK (source IN ('email', 'call', 'walkin')),
  product_id UUID REFERENCES products(id),
  status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'assigned', 'in_progress', 'resolved', 'escalated')),
  customer_response TEXT,
  immediate_action TEXT,
  escalation_required BOOLEAN DEFAULT false,
  assigned_team VARCHAR(100),
  customer_name VARCHAR(255),
  customer_email VARCHAR(255),
  customer_phone VARCHAR(50),
  audio_base64 TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Complaint Timeline table (for tracking status changes)
CREATE TABLE IF NOT EXISTS complaint_timeline (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  complaint_id UUID REFERENCES complaints(id) ON DELETE CASCADE,
  status_from VARCHAR(20),
  status_to VARCHAR(20) NOT NULL,
  changed_by VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operational', 'call_center')),
  department VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SLA Configuration table
CREATE TABLE IF NOT EXISTS sla_config (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  priority_level VARCHAR(20) UNIQUE NOT NULL CHECK (priority_level IN ('Low', 'Medium', 'High')),
  response_time_hours INTEGER NOT NULL,
  resolution_time_hours INTEGER NOT NULL,
  is_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_priority ON complaints(priority);
CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
CREATE INDEX IF NOT EXISTS idx_complaints_source ON complaints(source);
CREATE INDEX IF NOT EXISTS idx_complaints_product_id ON complaints(product_id);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);
CREATE INDEX IF NOT EXISTS idx_complaints_customer_email ON complaints(customer_email);
CREATE INDEX IF NOT EXISTS idx_complaints_assigned_team ON complaints(assigned_team);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_complaints_status_priority ON complaints(status, priority);
CREATE INDEX IF NOT EXISTS idx_complaints_category_status ON complaints(category, status);
CREATE INDEX IF NOT EXISTS idx_complaints_date_range ON complaints(created_at DESC);

-- Indexes for timeline
CREATE INDEX IF NOT EXISTS idx_timeline_complaint_id ON complaint_timeline(complaint_id);
CREATE INDEX IF NOT EXISTS idx_timeline_created_at ON complaint_timeline(created_at);

-- Indexes for employees
CREATE INDEX IF NOT EXISTS idx_employees_role ON employees(role);
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);

-- Insert sample data
INSERT INTO products (name, sku, category) VALUES
  ('ProWellness Collagen Peptide', 'PW-COL-001', 'supplement'),
  ('ImmunoBoost Vitamin C + Zinc', 'IB-VIT-002', 'vitamin'),
  ('OmegaCare Deep Sea Fish Oil', 'OC-OMG-003', 'wellness'),
  ('VitaGlow Multivitamin Complex', 'VG-MUL-004', 'vitamin'),
  ('PureHerb Ashwagandha Capsules', 'PH-ASH-005', 'supplement'),
  ('FlexiJoint Glucosamine Tablets', 'FJ-GLU-006', 'wellness')
ON CONFLICT (sku) DO NOTHING;

-- Insert sample SLA configurations
INSERT INTO sla_config (priority_level, response_time_hours, resolution_time_hours) VALUES
  ('High', 2, 24),
  ('Medium', 8, 72),
  ('Low', 24, 168)
ON CONFLICT (priority_level) DO NOTHING;

-- Enable Row Level Security (RLS) for multi-tenancy if needed
-- ALTER TABLE products ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

-- Sample RLS policies (uncomment to enable)
-- CREATE POLICY "Employees can view their own records" ON employees
--   FOR SELECT USING (auth.uid() = id);