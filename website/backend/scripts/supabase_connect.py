#!/usr/bin/env python3
"""
Supabase Connection Script for TS-14 Complaint Resolution Engine

This script connects to Supabase PostgreSQL database using the credentials
from .env file (SUPABASE_URL and SUPABASE_KEY).

Usage:
    python scripts/supabase_connect.py              # Test connection
    python scripts/supabase_connect.py --tables     # List tables
    python scripts/supabase_connect.py --reset      # Reset database (caution!)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded environment from {env_path}")
else:
    load_dotenv()
    print("[WARN] No .env file found")

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # This is the anon key, not for DB connection
DATABASE_URL = os.getenv("DATABASE_URL")


def get_supabase_db_url():
    """
    Get Supabase database connection URL.
    
    For Supabase, you need the direct PostgreSQL connection string which looks like:
    postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
    
    This should be set in your .env file as DATABASE_URL.
    """
    if DATABASE_URL and "supabase" in DATABASE_URL:
        return DATABASE_URL
    
    if SUPABASE_URL:
        # Try to construct from Supabase URL
        # Extract project ref from URL like: https://xxxxx.supabase.co
        try:
            project_ref = SUPABASE_URL.split("//")[1].split(".")[0]
            print(f"[WARN] Please set your DATABASE_URL in .env file")
            print(f"  Format: postgresql://postgres:[PASSWORD]@db.{project_ref}.supabase.co:5432/postgres")
            print(f"  You can find this in Supabase Dashboard > Settings > Database")
        except IndexError:
            pass
    
    return None


class SupabaseConnection:
    """Supabase PostgreSQL connection manager."""
    
    def __init__(self):
        self.db_url = get_supabase_db_url()
        self.engine = None
        self.SessionLocal = None
    
    def connect(self):
        """Connect to Supabase PostgreSQL."""
        if not self.db_url:
            print("[ERROR] No database URL configured")
            print("\nTo connect to Supabase:")
            print("1. Go to Supabase Dashboard > Settings > Database")
            print("2. Copy the connection string (Session mode or Transaction mode)")
            print("3. Add to your .env file:")
            print('   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres')
            return False
        
        try:
            self.engine = create_engine(self.db_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            print("[OK] Connected to Supabase PostgreSQL")
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False
    
    def test_connection(self):
        """Test the connection."""
        try:
            with self.SessionLocal() as session:
                result = session.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"[OK] Connected to: {version}")
                return True
        except SQLAlchemyError as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False
    
    def list_tables(self):
        """List all tables."""
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_row_counts(self):
        """Get row counts for all tables."""
        tables = self.list_tables()
        counts = {}
        
        with self.SessionLocal() as session:
            for table in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
                    counts[table] = result.scalar()
                except SQLAlchemyError as e:
                    counts[table] = f"Error: {e}"
        
        return counts
    
    def execute(self, query: str):
        """Execute a query."""
        with self.SessionLocal() as session:
            result = session.execute(text(query))
            if result.returns_rows:
                return result.fetchall()
            session.commit()
            return result.rowcount
    
    def init_tables(self):
        """Create all tables from models."""
        from app.database import Base
        from app.models import models  # noqa
        
        print("Creating tables...")
        Base.metadata.create_all(bind=self.engine)
        print("[OK] Tables created")
    
    def close(self):
        """Close connection."""
        if self.engine:
            self.engine.dispose()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Supabase Connection Script")
    parser.add_argument("--tables", action="store_true", help="List all tables")
    parser.add_argument("--stats", action="store_true", help="Show table statistics")
    parser.add_argument("--init", action="store_true", help="Initialize tables from models")
    parser.add_argument("--query", type=str, help="Execute SQL query")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("TS-14 Supabase Connection")
    print("=" * 60)
    
    conn = SupabaseConnection()
    
    if not conn.connect():
        sys.exit(1)
    
    if not conn.test_connection():
        sys.exit(1)
    
    try:
        if args.tables:
            print("\n[TABLES] Tables:")
            for table in conn.list_tables():
                print(f"  - {table}")
        
        elif args.stats:
            print("\n[STATS] Table Statistics:")
            counts = conn.get_row_counts()
            for table, count in sorted(counts.items()):
                if isinstance(count, int):
                    print(f"  {table:.<30} {count:>6} rows")
                else:
                    print(f"  {table:.<30} {count}")
        
        elif args.init:
            conn.init_tables()
        
        elif args.query:
            print(f"\n[QUERY] Query: {args.query}")
            result = conn.execute(args.query)
            if isinstance(result, list):
                for row in result[:10]:  # Limit to 10 rows
                    print(f"  {row}")
                if len(result) > 10:
                    print(f"  ... and {len(result) - 10} more rows")
            else:
                print(f"[OK] Rows affected: {result}")
        
        else:
            print("\n[OK] Connected successfully!")
            print("\nAvailable commands:")
            print("  --tables    List all tables")
            print("  --stats     Show table statistics")
            print("  --init      Initialize tables from models")
            print("  --query SQL Execute a SQL query")
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()