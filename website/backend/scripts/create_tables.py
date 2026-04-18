#!/usr/bin/env python3
"""
Database Schema Creation Script with Optimized Indexing

This script creates all tables with strategic indexes for fast data retrieval
at minimal database cost. Indexes are chosen based on common query patterns:

- Complaint filtering by status, category, priority
- SLA breach detection queries
- Timeline lookups by complaint
- Analytics aggregations
- Full-text search on complaint text

Usage:
    python scripts/create_tables.py              # Create all tables
    python scripts/create_tables.py --force      # Drop and recreate
    python scripts/create_tables.py --indexes    # Show index recommendations
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
except ImportError:
    pass

from sqlalchemy import create_engine, text, Index
from sqlalchemy.exc import SQLAlchemyError
from app.database import Base, engine
from app.models.models import (
    Profile, Customer, Complaint, ComplaintTimeline,
    SLAConfig, DailyMetrics, StatusEnum, CategoryEnum, PriorityEnum
)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{backend_dir}/ts14.db")


# Additional optimized indexes for faster queries
# These complement the indexes defined in models.py
OPTIMIZED_INDEXES = [
    # Composite index for common complaint filtering (status + created_at for recent first)
    {
        "name": "idx_complaint_status_created",
        "table": "complaints",
        "columns": ["status", "created_at"],
    },
    # Composite index for category + priority filtering
    {
        "name": "idx_complaint_category_priority",
        "table": "complaints",
        "columns": ["category", "priority"],
    },
    # Index for SLA breach queries (find overdue unresolved complaints)
    {
        "name": "idx_complaint_sla_breach",
        "table": "complaints",
        "columns": ["sla_deadline", "sla_breached", "status"],
    },
    # Index for submitted_via filtering (email vs call vs dashboard)
    {
        "name": "idx_complaint_submitted_via",
        "table": "complaints",
        "columns": ["submitted_via", "created_at"],
    },
    # Index for resolved_at (analytics: resolution time calculations)
    {
        "name": "idx_complaint_resolved",
        "table": "complaints",
        "columns": ["resolved_at", "created_at"],
    },
    # Index for escalated complaints
    {
        "name": "idx_complaint_escalated",
        "table": "complaints",
        "columns": ["escalated_at", "status"],
    },
    # Composite index for timeline lookups with ordering
    {
        "name": "idx_timeline_complaint_created",
        "table": "complaint_timeline",
        "columns": ["complaint_id", "created_at"],
    },
    # Index for customer complaints lookup
    {
        "name": "idx_complaint_customer_created",
        "table": "complaints",
        "columns": ["customer_id", "created_at"],
    },
    # Index for daily metrics date lookups
    {
        "name": "idx_metrics_date",
        "table": "daily_metrics",
        "columns": ["date"],
    },
]


def create_tables():
    """Create all tables from SQLAlchemy models."""
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully")
        return True
    except SQLAlchemyError as e:
        print(f"[ERROR] Failed to create tables: {e}")
        return False


def drop_tables():
    """Drop all tables (use with caution)."""
    try:
        Base.metadata.drop_all(bind=engine)
        print("[OK] All tables dropped")
        return True
    except SQLAlchemyError as e:
        print(f"[ERROR] Failed to drop tables: {e}")
        return False


def create_additional_indexes():
    """Create optimized indexes for faster queries."""
    created = 0
    skipped = 0
    
    with engine.connect() as conn:
        for idx_config in OPTIMIZED_INDEXES:
            try:
                # Check if index already exists
                index_name = idx_config["name"]
                table_name = idx_config["table"]
                columns = ", ".join(f'"{c}"' for c in idx_config["columns"])
                
                # Create index SQL
                sql = f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ({columns})'
                
                conn.execute(text(sql))
                conn.commit()
                print(f"[OK] Created index: {index_name} on {table_name}({columns})")
                created += 1
                
            except SQLAlchemyError as e:
                print(f"[SKIP] Index {idx_config['name']}: {e}")
                skipped += 1
    
    print(f"\n[SUMMARY] Created: {created}, Skipped: {skipped}")
    return created, skipped


def seed_sla_config():
    """Seed default SLA configuration values."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    
    try:
        with Session() as session:
            # Check if SLA configs already exist
            existing = session.query(SLAConfig).first()
            if existing:
                print("[INFO] SLA config already exists, skipping")
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
            print("[OK] Default SLA configuration seeded")
            return True
            
    except SQLAlchemyError as e:
        print(f"[ERROR] Failed to seed SLA config: {e}")
        return False


def show_index_recommendations():
    """Display index recommendations and query optimization tips."""
    print("\n" + "=" * 70)
    print("INDEX OPTIMIZATION RECOMMENDATIONS")
    print("=" * 70)
    
    print("\n[EXISTING INDEXES from models.py]")
    print("  - profiles.email (UNIQUE)")
    print("  - customers.email (UNIQUE)")
    print("  - complaints.customer_id (FK)")
    print("  - complaints.status")
    print("  - complaints.created_at")
    print("  - complaint_timeline.complaint_id (FK)")
    print("  - daily_metrics.date")
    
    print("\n[ADDITIONAL OPTIMIZED INDEXES]")
    for idx in OPTIMIZED_INDEXES:
        cols = ", ".join(idx["columns"])
        print(f"  - {idx['name']}: {idx['table']}({cols})")
    
    print("\n[QUERY OPTIMIZATION GUIDE]")
    print("\n1. Complaint List with Filters:")
    print("   Use: status + created_at composite index")
    print("   Query: WHERE status='open' ORDER BY created_at DESC")
    
    print("\n2. SLA Breach Detection:")
    print("   Use: sla_deadline + sla_breached + status index")
    print("   Query: WHERE sla_deadline < NOW() AND sla_breached = false")
    
    print("\n3. Category/Priority Analytics:")
    print("   Use: category + priority composite index")
    print("   Query: WHERE category='Product' AND priority='High'")
    
    print("\n4. Customer Complaint History:")
    print("   Use: customer_id + created_at composite index")
    print("   Query: WHERE customer_id = X ORDER BY created_at DESC")
    
    print("\n5. Timeline for Complaint:")
    print("   Use: complaint_id + created_at composite index")
    print("   Query: WHERE complaint_id = X ORDER BY created_at")
    
    print("\n6. Resolution Time Analytics:")
    print("   Use: resolved_at + created_at index")
    print("   Query: WHERE resolved_at IS NOT NULL")
    
    print("\n[PERFORMANCE TIPS]")
    print("  - Always filter by indexed columns first")
    print("  - Use LIMIT for pagination, not OFFSET for large tables")
    print("  - Consider covering indexes for frequently accessed columns")
    print("  - Monitor slow query logs and add indexes accordingly")
    print("  - Avoid indexes on columns with low cardinality (boolean, enum with few values)")
    print("=" * 70)


def verify_schema():
    """Verify tables were created correctly."""
    try:
        with engine.connect() as conn:
            # Get list of tables
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = [r[0] for r in result.fetchall()]
            
            print("\n[VERIFICATION] Created Tables:")
            expected = ['profiles', 'customers', 'complaints', 'complaint_timeline', 
                       'sla_config', 'daily_metrics']
            
            for table in expected:
                status = "[OK]" if table in tables else "[MISSING]"
                print(f"  {status} {table}")
            
            # Count indexes
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ))
            indexes = [r[0] for r in result.fetchall()]
            print(f"\n[OK] Total indexes created: {len(indexes)}")
            
            return all(t in tables for t in expected)
            
    except SQLAlchemyError as e:
        print(f"[ERROR] Verification failed: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create database tables with optimized indexing"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop existing tables before creating (DANGER: data loss)"
    )
    parser.add_argument(
        "--indexes-only",
        action="store_true",
        help="Only create additional indexes, skip table creation"
    )
    parser.add_argument(
        "--recommendations",
        action="store_true",
        help="Show index recommendations without creating anything"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing schema"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TS-14 Database Schema Creation with Optimized Indexing")
    print("=" * 70)
    print(f"Database: {DATABASE_URL}")
    print("=" * 70)
    
    if args.recommendations:
        show_index_recommendations()
        return
    
    if args.verify:
        verify_schema()
        return
    
    success = True
    
    # Drop tables if force flag
    if args.force:
        print("\n[!] Dropping all tables (force mode)...")
        if not drop_tables():
            success = False
    
    # Create tables
    if not args.indexes_only:
        print("\n[STEP 1] Creating tables from models...")
        if not create_tables():
            success = False
    
    # Create additional indexes
    print("\n[STEP 2] Creating optimized indexes...")
    created, skipped = create_additional_indexes()
    
    # Seed default data
    if not args.indexes_only:
        print("\n[STEP 3] Seeding default data...")
        if not seed_sla_config():
            success = False
    
    # Verify
    print("\n[STEP 4] Verifying schema...")
    if verify_schema():
        print("\n[OK] Database setup complete!")
    else:
        print("\n[ERROR] Schema verification failed")
        success = False
    
    if success:
        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("  - Run: python scripts/db_check.py")
        print("  - Run: python scripts/create_tables.py --recommendations")
        print("  - Seed demo data: python scripts/seed_demo.py")
        print("=" * 70)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()