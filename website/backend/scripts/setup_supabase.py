#!/usr/bin/env python3
"""
Supabase Database Setup Script

Creates all tables directly on Supabase PostgreSQL.
Reads SUPABASE_URL and connects to the cloud database.

Usage:
    python scripts/setup_supabase.py           # Create tables on Supabase
    python scripts/setup_supabase.py --check   # Check connection only
    python scripts/setup_supabase.py --seed    # Create tables + seed data
"""

import os
import sys
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
        print(f"[OK] Loaded .env from {env_path}")
    else:
        print("[WARN] No .env file found")
except ImportError:
    print("[WARN] python-dotenv not installed")

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Get Supabase credentials from .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Construct Supabase PostgreSQL URL if not provided
# Format: postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
def get_supabase_db_url():
    """Get the correct Supabase PostgreSQL connection URL."""
    
    if DATABASE_URL and "postgresql" in DATABASE_URL:
        return DATABASE_URL
    
    if SUPABASE_URL:
        # Extract project reference from Supabase URL
        # URL format: https://[PROJECT-REF].supabase.co
        try:
            project_ref = SUPABASE_URL.split("//")[1].split(".")[0]
            
            print("\n" + "="*70)
            print("SUPABASE CONNECTION SETUP")
            print("="*70)
            print(f"\nProject Reference: {project_ref}")
            print(f"Supabase URL: {SUPABASE_URL}")
            
            print("\n[!] DATABASE_URL not found in .env")
            print("\nTo connect to Supabase, you need to add the PostgreSQL connection string.")
            print("\nSteps to get your connection string:")
            print("1. Go to https://supabase.com/dashboard")
            print("2. Select your project")
            print("3. Go to Project Settings (gear icon) > Database")
            print("4. Under 'Connection string', select 'URI' tab")
            print("5. Copy the connection string")
            print("6. Add to your .env file:")
            print(f"\n   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres")
            print("\n" + "="*70)
            
        except IndexError:
            print("[ERROR] Invalid SUPABASE_URL format")
    
    return None


def test_connection(db_url):
    """Test database connection."""
    try:
        engine = create_engine(db_url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"[OK] Connected to PostgreSQL")
            print(f"  Server: {version[:50]}...")
        engine.dispose()
        return True
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False


def create_tables_on_supabase(db_url):
    """Create all tables on Supabase."""
    from app.database import Base
    from app.models import models  # noqa - imports all models
    
    try:
        engine = create_engine(db_url)
        
        print("\n[STEP 1] Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables created successfully")
        
        # List created tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n[OK] Tables on Supabase ({len(tables)} total):")
        for table in sorted(tables):
            print(f"  - {table}")
        
        engine.dispose()
        return True
        
    except SQLAlchemyError as e:
        print(f"[ERROR] Failed to create tables: {e}")
        return False


def create_indexes_on_supabase(db_url):
    """Create optimized indexes on Supabase."""
    
    indexes = [
        ("idx_complaint_status_created", "CREATE INDEX IF NOT EXISTS idx_complaint_status_created ON complaints (status, created_at)"),
        ("idx_complaint_category_priority", "CREATE INDEX IF NOT EXISTS idx_complaint_category_priority ON complaints (category, priority)"),
        ("idx_complaint_sla_breach", "CREATE INDEX IF NOT EXISTS idx_complaint_sla_breach ON complaints (sla_deadline, sla_breached, status)"),
        ("idx_complaint_submitted_via", "CREATE INDEX IF NOT EXISTS idx_complaint_submitted_via ON complaints (submitted_via, created_at)"),
        ("idx_complaint_resolved", "CREATE INDEX IF NOT EXISTS idx_complaint_resolved ON complaints (resolved_at, created_at)"),
        ("idx_complaint_escalated", "CREATE INDEX IF NOT EXISTS idx_complaint_escalated ON complaints (escalated_at, status)"),
        ("idx_timeline_complaint_created", "CREATE INDEX IF NOT EXISTS idx_timeline_complaint_created ON complaint_timeline (complaint_id, created_at)"),
        ("idx_complaint_customer_created", "CREATE INDEX IF NOT EXISTS idx_complaint_customer_created ON complaints (customer_id, created_at)"),
        ("idx_metrics_date", "CREATE INDEX IF NOT EXISTS idx_metrics_date ON daily_metrics (date)"),
    ]
    
    try:
        engine = create_engine(db_url)
        
        print("\n[STEP 2] Creating optimized indexes...")
        created = 0
        
        with engine.connect() as conn:
            for idx_name, sql in indexes:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"[OK] Created index: {idx_name}")
                    created += 1
                except Exception as e:
                    print(f"[SKIP] {idx_name}: {e}")
        
        engine.dispose()
        print(f"\n[OK] Created {created}/{len(indexes)} indexes")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to create indexes: {e}")
        return False


def seed_sla_config_on_supabase(db_url):
    """Seed default SLA configuration."""
    from app.models.models import SLAConfig, PriorityEnum
    
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        
        print("\n[STEP 3] Seeding SLA configuration...")
        
        with Session() as session:
            # Check if already exists
            existing = session.query(SLAConfig).first()
            if existing:
                print("[INFO] SLA config already exists")
                return True
            
            # Create default SLA configs
            slas = [
                SLAConfig(priority=PriorityEnum.high, deadline_hours=4),
                SLAConfig(priority=PriorityEnum.medium, deadline_hours=8),
                SLAConfig(priority=PriorityEnum.low, deadline_hours=24),
            ]
            
            for sla in slas:
                session.add(sla)
            
            session.commit()
            print("[OK] SLA configuration seeded")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to seed SLA config: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Supabase database")
    parser.add_argument("--check", action="store_true", help="Check connection only")
    parser.add_argument("--seed", action="store_true", help="Also seed demo data")
    
    args = parser.parse_args()
    
    print("="*70)
    print("SUPABASE DATABASE SETUP")
    print("="*70)
    
    # Get database URL
    db_url = get_supabase_db_url()
    
    if not db_url:
        print("\n[ERROR] Cannot proceed without DATABASE_URL")
        print("\nPlease add your Supabase connection string to .env file:")
        print('DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres')
        sys.exit(1)
    
    # Test connection
    print("\n[STEP 0] Testing connection...")
    if not test_connection(db_url):
        sys.exit(1)
    
    if args.check:
        print("\n[OK] Connection test successful!")
        sys.exit(0)
    
    # Create tables
    if not create_tables_on_supabase(db_url):
        sys.exit(1)
    
    # Create indexes
    if not create_indexes_on_supabase(db_url):
        sys.exit(1)
    
    # Seed SLA config
    if not seed_sla_config_on_supabase(db_url):
        sys.exit(1)
    
    print("\n" + "="*70)
    print("[OK] SUPABASE SETUP COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Check Supabase Dashboard > Table Editor to see your tables")
    print("  2. Run: python scripts/seed_demo.py (to add demo data)")
    print("  3. Your API is ready to use with Supabase!")
    print("="*70)


if __name__ == "__main__":
    main()