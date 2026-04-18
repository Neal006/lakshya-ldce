#!/usr/bin/env python3
"""
Supabase Table Creator & Data Seeder

Creates all tables on Supabase PostgreSQL and populates with 10 rows of dummy data.
Uses psycopg2 for direct database access.

Usage:
    python scripts/setup_supabase.py                           # Interactive (will ask for password)
    python scripts/setup_supabase.py --password YOUR_PASSWORD   # With password
    python scripts/setup_supabase.py --check-only              # Just check connection
"""

import os
import sys
import json
import getpass
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Load environment
try:
    from dotenv import load_dotenv
    env_path = backend_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

try:
    import psycopg2
    from psycopg2 import sql as pgsql
except ImportError:
    print("[ERROR] psycopg2-binary is not installed")
    print("Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from psycopg2.extras import RealDictCursor
except ImportError:
    pass

# Supabase connection details from .env
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
PROJECT_REF = ""
if SUPABASE_URL:
    try:
        PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0]
    except (IndexError, ValueError):
        pass

SUPABASE_HOST = f"db.{PROJECT_REF}.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"


# ============================================================
# SQL: Create all tables with optimized indexes
# ============================================================

CREATE_TABLES_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- TABLE: profiles (User accounts)
-- ===========================================
CREATE TABLE IF NOT EXISTS profiles (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'call_attender'
        CHECK (role IN ('admin', 'qa', 'call_attender')),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles (email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles (role);
CREATE INDEX IF NOT EXISTS idx_profiles_active ON profiles (is_active) WHERE is_active = TRUE;

-- ===========================================
-- TABLE: customers
-- ===========================================
CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email);

-- ===========================================
-- TABLE: complaints (Core table)
-- ===========================================
CREATE TABLE IF NOT EXISTS complaints (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    raw_text TEXT NOT NULL,
    category VARCHAR(20)
        CHECK (category IN ('Product', 'Packaging', 'Trade')),
    priority VARCHAR(10)
        CHECK (priority IN ('High', 'Medium', 'Low')),
    resolution_steps TEXT,
    sentiment_score FLOAT,
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'resolved', 'escalated')),
    submitted_via VARCHAR(20) NOT NULL DEFAULT 'dashboard'
        CHECK (submitted_via IN ('email', 'call', 'dashboard')),
    escalation_reason TEXT,
    sla_deadline TIMESTAMPTZ,
    sla_breached BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(36) REFERENCES profiles(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    escalated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_complaints_customer_id ON complaints (customer_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints (status);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints (created_at DESC);

-- Composite indexes for filtered + sorted queries
CREATE INDEX IF NOT EXISTS idx_complaints_status_created ON complaints (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_category_priority ON complaints (category, priority);
CREATE INDEX IF NOT EXISTS idx_complaints_sla_breach ON complaints (sla_deadline, sla_breached) WHERE status != 'resolved';
CREATE INDEX IF NOT EXISTS idx_complaints_submitted_via ON complaints (submitted_via, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_resolved ON complaints (resolved_at) WHERE resolved_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_complaints_escalated ON complaints (escalated_at) WHERE escalated_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_complaints_customer_created ON complaints (customer_id, created_at DESC);

-- ===========================================
-- TABLE: complaint_timeline
-- ===========================================
CREATE TABLE IF NOT EXISTS complaint_timeline (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    complaint_id VARCHAR(36) NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    performed_by VARCHAR(36) REFERENCES profiles(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_timeline_complaint_id ON complaint_timeline (complaint_id);
CREATE INDEX IF NOT EXISTS idx_timeline_complaint_created ON complaint_timeline (complaint_id, created_at);

-- ===========================================
-- TABLE: sla_config
-- ===========================================
CREATE TABLE IF NOT EXISTS sla_config (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    priority VARCHAR(10) UNIQUE NOT NULL
        CHECK (priority IN ('High', 'Medium', 'Low')),
    deadline_hours INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===========================================
-- TABLE: daily_metrics
-- ===========================================
CREATE TABLE IF NOT EXISTS daily_metrics (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    date TIMESTAMPTZ NOT NULL,
    total_complaints INTEGER DEFAULT 0,
    open_complaints INTEGER DEFAULT 0,
    resolved_complaints INTEGER DEFAULT 0,
    escalated_complaints INTEGER DEFAULT 0,
    avg_resolution_time_hours FLOAT,
    sla_compliance_rate FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_date ON daily_metrics (date);

-- ===========================================
-- Enable Row Level Security (Supabase requires this)
-- ===========================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE sla_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_metrics ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (bypasses RLS)
CREATE POLICY "Service role full access" ON profiles FOR ALL USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "Service role full access" ON customers FOR ALL USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "Service role full access" ON complaints FOR ALL USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "Service role full access" ON complaint_timeline FOR ALL USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "Service role full access" ON sla_config FOR ALL USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "Service role full access" ON daily_metrics FOR ALL USING (TRUE) WITH CHECK (TRUE);
"""


# ============================================================
# SQL: Insert 10 rows of dummy data
# ============================================================

SEED_DATA_SQL_TEMPLATE = """
-- Clear existing data (in reverse dependency order)
DELETE FROM complaint_timeline;
DELETE FROM complaints;
DELETE FROM sla_config;
DELETE FROM daily_metrics;
DELETE FROM customers;
DELETE FROM profiles;

-- ===========================================
-- INSERT: 2 profiles (1 admin, 1 call_attender)
-- ===========================================
INSERT INTO profiles (id, email, name, role, hashed_password, is_active, created_at) VALUES
('prof-001-admin', 'admin@ts14.com', 'Admin User', 'admin', '$2b$12$LJ3m4ys3JvZMQhObgXW7WuFPE8jE3vVvGZLQqHvNKY7tFQZ1FOKK6', TRUE, NOW()),
('prof-002-call', 'caller@ts14.com', 'Rahul Sharma', 'call_attender', '$2b$12$LJ3m4ys3JvZMQhObgXW7WuFPE8jE3vVvGZLQqHvNKY7tFQZ1FOKK6', TRUE, NOW());

-- ===========================================
-- INSERT: 5 customers
-- ===========================================
INSERT INTO customers (id, name, email, phone, created_at) VALUES
('cust-001', 'Priya Patel', 'priya.patel@email.com', '+91-9876543210', NOW() - INTERVAL '25 days'),
('cust-002', 'Amit Kumar', 'amit.kumar@email.com', '+91-9876543211', NOW() - INTERVAL '20 days'),
('cust-003', 'Sneha Reddy', 'sneha.reddy@email.com', '+91-9876543212', NOW() - INTERVAL '15 days'),
('cust-004', 'Vikram Singh', 'vikram.singh@email.com', '+91-9876543213', NOW() - INTERVAL '10 days'),
('cust-005', 'Ananya Joshi', 'ananya.joshi@email.com', '+91-9876543214', NOW() - INTERVAL '5 days');

-- ===========================================
-- INSERT: 3 SLA configs
-- ===========================================
INSERT INTO sla_config (id, priority, deadline_hours, created_at) VALUES
('sla-001', 'High', 4, NOW()),
('sla-002', 'Medium', 8, NOW()),
('sla-003', 'Low', 24, NOW());

-- ===========================================
-- INSERT: 10 complaints with varied data
-- ===========================================
INSERT INTO complaints (id, customer_id, raw_text, category, priority, resolution_steps, sentiment_score, status, submitted_via, sla_deadline, sla_breached, created_by, resolved_at, escalated_at, escalation_reason, created_at) VALUES
(
    'comp-001', 'cust-001',
    'Product stopped working after just 2 days of use. Very disappointed with the quality!',
    'Product', 'High',
    '["1. Verify product warranty status","2. Check for common troubleshooting steps","3. Initiate replacement if under warranty","4. Schedule pickup for defective unit"]',
    -0.75, 'open', 'call',
    NOW() + INTERVAL '4 hours', FALSE,
    'prof-002-call', NULL, NULL, NULL,
    NOW() - INTERVAL '2 hours'
),
(
    'comp-002', 'cust-002',
    'Package arrived completely crushed. The outer box was in terrible condition.',
    'Packaging', 'High',
    '["1. Document packaging damage with photos","2. Verify shipping carrier and tracking info","3. Arrange replacement shipment","4. File carrier damage claim if applicable"]',
    -0.6, 'in_progress', 'email',
    NOW() + INTERVAL '3 hours', FALSE,
    'prof-002-call', NULL, NULL, NULL,
    NOW() - INTERVAL '5 hours'
),
(
    'comp-003', 'cust-003',
    'Bulk order discount not applied as promised by the sales representative.',
    'Trade', 'Medium',
    '["1. Verify order details and customer account","2. Check inventory and fulfillment status","3. Coordinate with logistics for delivery update","4. Provide resolution timeline to customer"]',
    -0.3, 'in_progress', 'dashboard',
    NOW() + INTERVAL '6 hours', FALSE,
    'prof-001-admin', NULL, NULL, NULL,
    NOW() - INTERVAL '2 days'
),
(
    'comp-004', 'cust-001',
    'The device overheats within 30 minutes of operation. Safety concern!',
    'Product', 'High',
    '["1. Verify product warranty status","2. Check for common troubleshooting steps","3. Initiate replacement if under warranty","4. Schedule pickup for defective unit"]',
    -0.8, 'escalated', 'call',
    NOW() - INTERVAL '1 hour', TRUE,
    'prof-002-call', NULL, NOW() - INTERVAL '2 hours', 'Customer threatened legal action',
    NOW() - INTERVAL '1 day'
),
(
    'comp-005', 'cust-004',
    'Missing items from my order. Only received 3 out of 5 items.',
    'Packaging', 'Medium',
    '["1. Document packaging damage with photos","2. Verify shipping carrier and tracking info","3. Arrange replacement shipment","4. File carrier damage claim if applicable"]',
    -0.4, 'open', 'email',
    NOW() + INTERVAL '7 hours', FALSE,
    'prof-002-call', NULL, NULL, NULL,
    NOW() - INTERVAL '1 hour'
),
(
    'comp-006', 'cust-002',
    'Software crashes every time I try to open the settings menu.',
    'Product', 'Low',
    '["1. Verify product warranty status","2. Check for common troubleshooting steps","3. Initiate replacement if under warranty","4. Schedule pickup for defective unit"]',
    -0.2, 'open', 'dashboard',
    NOW() + INTERVAL '22 hours', FALSE,
    'prof-001-admin', NULL, NULL, NULL,
    NOW() - INTERVAL '3 hours'
),
(
    'comp-007', 'cust-005',
    'Return policy for bulk orders is unreasonably restrictive.',
    'Trade', 'Low',
    '["1. Verify order details and customer account","2. Check inventory and fulfillment status","3. Coordinate with logistics for delivery update","4. Provide resolution timeline to customer"]',
    0.1, 'resolved', 'email',
    NOW() - INTERVAL '20 hours', FALSE,
    'prof-002-call', NOW() - INTERVAL '4 hours', NULL, NULL,
    NOW() - INTERVAL '2 days'
),
(
    'comp-008', 'cust-003',
    'The product color is completely different from what was shown on the website.',
    'Product', 'Medium',
    '["1. Verify product warranty status","2. Check for common troubleshooting steps","3. Initiate replacement if under warranty","4. Schedule pickup for defective unit"]',
    -0.5, 'resolved', 'call',
    NOW() - INTERVAL '6 hours', FALSE,
    'prof-002-call', NOW() - INTERVAL '1 hour', NULL, NULL,
    NOW() - INTERVAL '8 hours'
),
(
    'comp-009', 'cust-004',
    'Invoice amount does not match the quoted price. Overcharged by 15%.',
    'Trade', 'High',
    '["1. Verify order details and customer account","2. Check inventory and fulfillment status","3. Coordinate with logistics for delivery update","4. Provide resolution timeline to customer"]',
    -0.7, 'open', 'email',
    NOW() + INTERVAL '2 hours', FALSE,
    'prof-002-call', NULL, NULL, NULL,
    NOW() - INTERVAL '30 minutes'
),
(
    'comp-010', 'cust-005',
    'No protective covering on the fragile parts during shipping. Everything was scratched.',
    'Packaging', 'Low',
    '["1. Document packaging damage with photos","2. Verify shipping carrier and tracking info","3. Arrange replacement shipment","4. File carrier damage claim if applicable"]',
    -0.35, 'in_progress', 'dashboard',
    NOW() + INTERVAL '16 hours', FALSE,
    'prof-001-admin', NULL, NULL, NULL,
    NOW() - INTERVAL '8 hours'
);

-- ===========================================
-- INSERT: Timeline entries for each complaint
-- ===========================================
INSERT INTO complaint_timeline (id, complaint_id, action, performed_by, notes, created_at) VALUES
('tl-001', 'comp-001', 'complaint_created', 'prof-002-call', 'Complaint received via phone call', NOW() - INTERVAL '2 hours'),
('tl-002', 'comp-002', 'complaint_created', 'prof-002-call', 'Complaint received via email', NOW() - INTERVAL '5 hours'),
('tl-003', 'comp-002', 'status_changed', 'prof-002-call', 'Status changed to in_progress', NOW() - INTERVAL '3 hours'),
('tl-004', 'comp-003', 'complaint_created', 'prof-001-admin', 'Complaint received via dashboard', NOW() - INTERVAL '2 days'),
('tl-005', 'comp-003', 'status_changed', 'prof-001-admin', 'Status changed to in_progress', NOW() - INTERVAL '1 day'),
('tl-006', 'comp-004', 'complaint_created', 'prof-002-call', 'Complaint received via phone call', NOW() - INTERVAL '1 day'),
('tl-007', 'comp-004', 'complaint_escalated', 'prof-002-call', 'Customer threatened legal action', NOW() - INTERVAL '2 hours'),
('tl-008', 'comp-005', 'complaint_created', 'prof-002-call', 'Complaint received via email', NOW() - INTERVAL '1 hour'),
('tl-009', 'comp-006', 'complaint_created', 'prof-001-admin', 'Complaint received via dashboard', NOW() - INTERVAL '3 hours'),
('tl-010', 'comp-007', 'complaint_created', 'prof-002-call', 'Complaint received via email', NOW() - INTERVAL '2 days'),
('tl-011', 'comp-007', 'status_changed', 'prof-002-call', 'Status changed to in_progress', NOW() - INTERVAL '1 day'),
('tl-012', 'comp-007', 'status_changed', 'prof-002-call', 'Status changed to resolved', NOW() - INTERVAL '4 hours'),
('tl-013', 'comp-008', 'complaint_created', 'prof-002-call', 'Complaint received via phone call', NOW() - INTERVAL '8 hours'),
('tl-014', 'comp-008', 'status_changed', 'prof-002-call', 'Status changed to in_progress', NOW() - INTERVAL '6 hours'),
('tl-015', 'comp-008', 'status_changed', 'prof-002-call', 'Status changed to resolved', NOW() - INTERVAL '1 hour'),
('tl-016', 'comp-009', 'complaint_created', 'prof-002-call', 'Complaint received via email', NOW() - INTERVAL '30 minutes'),
('tl-017', 'comp-010', 'complaint_created', 'prof-001-admin', 'Complaint received via dashboard', NOW() - INTERVAL '8 hours'),
('tl-018', 'comp-010', 'status_changed', 'prof-001-admin', 'Status changed to in_progress', NOW() - INTERVAL '4 hours');
"""


def get_connection(password=None):
    """Get psycopg2 connection to Supabase PostgreSQL."""
    if not password:
        # Try from DATABASE_URL in .env
        db_url = os.getenv("DATABASE_URL", "")
        if db_url and "postgresql" in db_url and "[YOUR-DB-PASSWORD]" not in db_url:
            try:
                conn = psycopg2.connect(db_url)
                return conn
            except Exception:
                pass
    
    # Construct connection string
    if not password:
        print("\n[INPUT] Enter your Supabase database password.")
        print("        Find it at: Supabase Dashboard > Project Settings > Database > Connection string")
        password = getpass.getpass("        Password: ")
    
    conn_string = (
        f"host={SUPABASE_HOST} "
        f"port={SUPABASE_PORT} "
        f"dbname={SUPABASE_DB} "
        f"user={SUPABASE_USER} "
        f"password={password}"
    )
    
    try:
        conn = psycopg2.connect(conn_string)
        return conn
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Could not connect to Supabase: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your database password is correct")
        print("  2. Make sure your IP is not blocked (Supabase Dashboard > Settings > Database)")
        print("  3. Try resetting your database password in Supabase Dashboard")
        return None


def check_connection(conn):
    """Verify database connection."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"[OK] Connected to: {version[:60]}...")
            return True
    except Exception as e:
        print(f"[ERROR] Connection check failed: {e}")
        return False


def create_tables(conn):
    """Create all tables with indexes on Supabase."""
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLES_SQL)
        conn.commit()
        print("[OK] All tables created on Supabase")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to create tables: {e}")
        return False


def verify_tables(conn):
    """Verify all tables exist and show row counts."""
    expected_tables = ['profiles', 'customers', 'complaints', 
                       'complaint_timeline', 'sla_config', 'daily_metrics']
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = [row['tablename'] for row in cur.fetchall()]
        
        print(f"\n[VERIFICATION] Tables on Supabase ({len(tables)} total):")
        print("-" * 50)
        
        all_found = True
        for table in expected_tables:
            if table in tables:
                with conn.cursor() as cur:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                    count = cur.fetchone()[0]
                print(f"  [OK] {table:.<35} {count:>5} rows")
            else:
                print(f"  [MISSING] {table}")
                all_found = False
        
        print("-" * 50)
        return all_found
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False


def verify_indexes(conn):
    """Show all indexes on the tables."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT tablename, indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            indexes = cur.fetchall()
        
        print(f"\n[INDEXES] Created ({len(indexes)} total):")
        print("-" * 50)
        current_table = ""
        for idx in indexes:
            if idx['tablename'] != current_table:
                current_table = idx['tablename']
                print(f"\n  {current_table}:")
            print(f"    - {idx['indexname']}")
        print("-" * 50)
        
    except Exception as e:
        print(f"[WARN] Could not verify indexes: {e}")


def seed_data(conn):
    """Insert 10 rows of dummy data."""
    try:
        with conn.cursor() as cur:
            cur.execute(SEED_DATA_SQL_TEMPLATE)
        conn.commit()
        print("[OK] Dummy data inserted (10 complaints, 5 customers, 2 profiles)")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to seed data: {e}")
        print(f"  Detail: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Supabase database")
    parser.add_argument("--password", type=str, help="Supabase database password")
    parser.add_argument("--check-only", action="store_true", help="Only check connection")
    parser.add_argument("--seed-only", action="store_true", help="Only seed data (tables must exist)")
    parser.add_argument("--drop", action="store_true", help="Drop all tables first (DANGER)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SUPABASE TABLE CREATOR & DATA SEEDER")
    print("=" * 60)
    print(f"Project: {PROJECT_REF}")
    print(f"Host:    {SUPABASE_HOST}")
    print("=" * 60)
    
    # Connect
    print("\n[STEP 1] Connecting to Supabase...")
    conn = get_connection(args.password)
    
    if not conn:
        sys.exit(1)
    
    if not check_connection(conn):
        conn.close()
        sys.exit(1)
    
    if args.check_only:
        print("\n[OK] Connection successful!")
        conn.close()
        sys.exit(0)
    
    # Drop tables if requested
    if args.drop:
        print("\n[!] Dropping all tables...")
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DROP TABLE IF EXISTS complaint_timeline CASCADE;
                    DROP TABLE IF EXISTS complaints CASCADE;
                    DROP TABLE IF EXISTS customers CASCADE;
                    DROP TABLE IF EXISTS profiles CASCADE;
                    DROP TABLE IF EXISTS sla_config CASCADE;
                    DROP TABLE IF EXISTS daily_metrics CASCADE;
                """)
            conn.commit()
            print("[OK] All tables dropped")
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to drop tables: {e}")
    
    # Create tables
    if not args.seed_only:
        print("\n[STEP 2] Creating tables and indexes...")
        if not create_tables(conn):
            conn.close()
            sys.exit(1)
        
        print("\n[STEP 3] Verifying tables...")
        verify_tables(conn)
        verify_indexes(conn)
    
    # Seed data
    print("\n[STEP 4] Seeding dummy data...")
    if not seed_data(conn):
        conn.close()
        sys.exit(1)
    
    # Final verification
    print("\n[STEP 5] Final verification...")
    verify_tables(conn)
    
    print("\n" + "=" * 60)
    print("[OK] SUPABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\nYou can now see your tables at:")
    print("  https://supabase.com/dashboard/project/lawvfitflgnntxtgjltp/editor")
    print("\nTest logins (password for all: SecurePass123):")
    print("  Admin:        admin@ts14.com")
    print("  Call Attender: caller@ts14.com")
    print("=" * 60)
    
    conn.close()


if __name__ == "__main__":
    main()