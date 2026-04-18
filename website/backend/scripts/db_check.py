#!/usr/bin/env python3
"""
Simple Database Connection Check for Development
Returns TRUE when connection is successful, FALSE otherwise.

Usage:
    python scripts/db_check.py
    
Environment:
    Uses DATABASE_URL from environment or defaults to SQLite (./ts14.db)
    For development, no external database needed.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Load environment if .env exists
try:
    from dotenv import load_dotenv
    env_path = backend_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Use SQLite by default for development
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{backend_dir}/ts14.db")


def check_connection():
    """Check database connection and return True/False."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except SQLAlchemyError:
        return False
    except Exception:
        return False


if __name__ == "__main__":
    if check_connection():
        print("TRUE")
        sys.exit(0)
    else:
        print("FALSE")
        sys.exit(1)