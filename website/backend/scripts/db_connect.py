#!/usr/bin/env python3
"""
Database Connection Script for TS-14 Complaint Resolution Engine

This script provides database connection utilities and basic operations.
It reads configuration from environment variables (loaded from .env file).

Usage:
    python scripts/db_connect.py                    # Test connection
    python scripts/db_connect.py --tables           # List all tables
    python scripts/db_connect.py --stats            # Show database stats
    python scripts/db_connect.py --query "SELECT * FROM complaints LIMIT 5"
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import app modules
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded environment from {env_path}")
else:
    load_dotenv()
    print("[WARN] No .env file found, using system environment variables")

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ts14.db")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class DatabaseConnection:
    """Database connection manager for TS-14 backend."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        
    def connect(self):
        """Initialize database connection."""
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            print(f"[OK] Connected to database")
            print(f"  URL: {self._mask_url(self.database_url)}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect to database: {e}")
            return False
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of database URL."""
        if "@" in url:
            # Mask password in PostgreSQL URL
            parts = url.split("@")
            creds = parts[0].split("://")
            if len(creds) > 1:
                user_pass = creds[1].split(":")
                if len(user_pass) > 1:
                    return f"{creds[0]}://{user_pass[0]}:***@{parts[1]}"
        return url
    
    def get_session(self) -> Session:
        """Get a new database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1"))
                result.scalar()
                print("[OK] Database connection test passed")
                return True
        except SQLAlchemyError as e:
            print(f"[ERROR] Database connection test failed: {e}")
            return False
    
    def list_tables(self) -> list:
        """List all tables in the database."""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            return tables
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to list tables: {e}")
            return []
    
    def get_table_stats(self) -> dict:
        """Get row counts for all tables."""
        stats = {}
        tables = self.list_tables()
        
        with self.get_session() as session:
            for table in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    stats[table] = count
                except SQLAlchemyError as e:
                    stats[table] = f"Error: {e}"
        
        return stats
    
    def execute_query(self, query: str, params: dict = None):
        """Execute a raw SQL query."""
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                
                # Check if query returns results
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return columns, rows
                else:
                    session.commit()
                    return None, result.rowcount
        except SQLAlchemyError as e:
            print(f"[ERROR] Query execution failed: {e}")
            return None, None
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            print("[OK] Database connection closed")


def print_table(columns, rows, max_rows=20):
    """Print query results in a formatted table."""
    if not rows:
        print("No results found.")
        return
    
    # Truncate if too many rows
    if len(rows) > max_rows:
        display_rows = rows[:max_rows]
        truncated = True
    else:
        display_rows = rows
        truncated = False
    
    # Calculate column widths
    widths = [len(str(col)) for col in columns]
    for row in display_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)[:50]))  # Limit to 50 chars
    
    # Print header
    header = " | ".join(str(col).ljust(widths[i]) for i, col in enumerate(columns))
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in display_rows:
        formatted = " | ".join(str(val)[:50].ljust(widths[i]) for i, val in enumerate(row))
        print(formatted)
    
    if truncated:
        print(f"\n... and {len(rows) - max_rows} more rows")
    print("=" * len(header) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Database connection script for TS-14 Complaint Resolution Engine"
    )
    parser.add_argument(
        "--tables", 
        action="store_true",
        help="List all tables in the database"
    )
    parser.add_argument(
        "--stats",
        action="store_true", 
        help="Show table row counts"
    )
    parser.add_argument(
        "--query",
        type=str,
        metavar="SQL",
        help="Execute a SQL query"
    )
    parser.add_argument(
        "--supabase",
        action="store_true",
        help="Use Supabase connection instead of direct PostgreSQL"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("TS-14 Database Connection Script")
    print("=" * 60)
    
    # Determine database URL
    if args.supabase and SUPABASE_URL:
        # Construct Supabase PostgreSQL URL
        # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
        db_url = f"{SUPABASE_URL}/postgres"  # This is simplified, actual URL may differ
        print(f"\nUsing Supabase: {SUPABASE_URL}")
    else:
        db_url = DATABASE_URL
    
    # Connect to database
    db = DatabaseConnection(db_url)
    
    if not db.connect():
        sys.exit(1)
    
    if not db.test_connection():
        sys.exit(1)
    
    # Execute requested operations
    try:
        if args.tables:
            print("\n[TABLES] Database Tables:")
            tables = db.list_tables()
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
        
        elif args.stats:
            print("\n[STATS] Table Statistics:")
            stats = db.get_table_stats()
            for table, count in sorted(stats.items()):
                if isinstance(count, int):
                    print(f"  {table:.<30} {count:>6} rows")
                else:
                    print(f"  {table:.<30} {count}")
        
        elif args.query:
            print(f"\n[QUERY] Executing query: {args.query}")
            columns, rows = db.execute_query(args.query)
            if columns:
                print_table(columns, rows)
            elif rows is not None:
                print(f"[OK] Query executed successfully. Rows affected: {rows}")
        
        else:
            # Default: just show connection info
            print("\n[INFO] Available commands:")
            print("  --tables     List all tables")
            print("  --stats      Show table row counts")
            print("  --query SQL  Execute a SQL query")
            print("\n[OK] Database connection ready!")
    
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user")
    finally:
        db.close()


if __name__ == "__main__":
    main()