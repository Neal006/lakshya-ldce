#!/usr/bin/env python3
"""
Quick Supabase Setup Helper

This script helps you get your Supabase database password and create tables.

STEPS TO GET YOUR DATABASE PASSWORD:
1. Go to https://supabase.com/dashboard
2. Sign in with your account
3. Select your project: lawvfitflgnntxtgjltp
4. Click on Project Settings (gear icon on left sidebar)
5. Click on "Database" in the left menu
6. Under "Connection string", click on "URI" tab
7. You'll see: postgresql://postgres:[YOUR-PASSWORD]@db.lawvfitflgnntxtgjltp.supabase.co:5432/postgres
8. Copy the password part (replace [YOUR-DB-PASSWORD] in .env file)

Or find password under "Database Password" section - click "Reset password" if you forgot it.

Once you have the password, update your .env file:
    DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.lawvfitflgnntxtgjltp.supabase.co:5432/postgres

Then run: python scripts/setup_supabase.py
"""

import os
import sys
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
env_path = backend_dir / ".env"

print("="*70)
print("SUPABASE SETUP HELPER")
print("="*70)

# Check if .env exists
if not env_path.exists():
    print("\n[ERROR] .env file not found!")
    print("Creating .env file...")
    sys.exit(1)

# Read current .env
with open(env_path, 'r') as f:
    content = f.read()

# Check if password is placeholder
if '[YOUR-DB-PASSWORD]' in content:
    print("\n[!] DATABASE_URL has placeholder password")
    print("\n" + "="*70)
    print("TO GET YOUR DATABASE PASSWORD:")
    print("="*70)
    print("\n1. Open https://supabase.com/dashboard")
    print("2. Select project: lawvfitflgnntxtgjltp")
    print("3. Go to: Project Settings > Database")
    print("4. Find: Connection string > URI")
    print("5. Copy the password from the URI")
    print("\nOR:")
    print("5. Find: Database Password section")
    print("6. Click 'Reset password' if you don't know it")
    print("\n" + "="*70)
    print("THEN UPDATE .env FILE:")
    print("="*70)
    print("\nCurrent line:")
    print('  DATABASE_URL=postgresql://postgres:[YOUR-DB-PASSWORD]@db.lawvfitflgnntxtgjltp.supabase.co:5432/postgres')
    print("\nChange to (replace YOUR_PASSWORD with actual password):")
    print('  DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.lawvfitflgnntxtgjltp.supabase.co:5432/postgres')
    print("\n" + "="*70)
    print("AFTER UPDATING .env, RUN:")
    print("  python scripts/setup_supabase.py")
    print("="*70)
    sys.exit(1)
else:
    print("\n[OK] .env file looks good!")
    print("\nChecking database connection...")
    
    # Try to import and test
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url or "postgresql" not in db_url:
            print("[ERROR] DATABASE_URL not found or invalid")
            sys.exit(1)
        
        print(f"\n[OK] Found DATABASE_URL")
        print(f"  Project: lawvfitflgnntxtgjltp")
        
        # Try connection
        from sqlalchemy import create_engine, text
        
        engine = create_engine(db_url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"\n[OK] Connected to Supabase PostgreSQL!")
            print(f"  Server: {version[:40]}...")
            
            # Check tables
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            tables = [r[0] for r in result.fetchall()]
            
            if tables:
                print(f"\n[OK] Found {len(tables)} tables:")
                for t in sorted(tables):
                    print(f"  - {t}")
            else:
                print("\n[!] No tables found yet")
                print("Run: python scripts/setup_supabase.py")
        
        engine.dispose()
        
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\nPossible issues:")
        print("  - Wrong password in DATABASE_URL")
        print("  - Database not active (check Supabase dashboard)")
        print("  - Network/firewall blocking connection")
        sys.exit(1)