#!/usr/bin/env python3
"""
Seed Supabase with 10 rows of dummy data via REST API (no password needed).
Uses SUPABASE_URL and SUPABASE_SERVICE_KEY from .env file.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

try:
    from dotenv import load_dotenv
    env_path = backend_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from supabase import create_client

URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ANON_KEY = os.getenv("SUPABASE_KEY")

if not URL or not SERVICE_KEY:
    print("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

sb = create_client(URL, SERVICE_KEY)


def seed_profiles():
    data = [
        {
            "id": "prof-001-admin",
            "email": "admin@ts14.com",
            "name": "Admin User",
            "role": "admin",
            "hashed_password": "$2b$12$LJ3m4ys3JvZMQhObgXW7WuFPE8jE3vVvGZLQqHvNKY7tFQZ1FOKK6",
            "is_active": True,
        },
        {
            "id": "prof-002-call",
            "email": "caller@ts14.com",
            "name": "Rahul Sharma",
            "role": "call_attender",
            "hashed_password": "$2b$12$LJ3m4ys3JvZMQhObgXW7WuFPE8jE3vVvGZLQqHvNKY7tFQZ1FOKK6",
            "is_active": True,
        },
    ]
    result = sb.table("profiles").upsert(data, on_conflict="id").execute()
    print(f"[OK] Inserted {len(result.data)} profiles")
    return result.data


def seed_customers():
    now = datetime.now(timezone.utc)
    data = [
        {"id": "cust-001", "name": "Priya Patel", "email": "priya.patel@email.com", "phone": "+91-9876543210", "created_at": (now - timedelta(days=25)).isoformat()},
        {"id": "cust-002", "name": "Amit Kumar", "email": "amit.kumar@email.com", "phone": "+91-9876543211", "created_at": (now - timedelta(days=20)).isoformat()},
        {"id": "cust-003", "name": "Sneha Reddy", "email": "sneha.reddy@email.com", "phone": "+91-9876543212", "created_at": (now - timedelta(days=15)).isoformat()},
        {"id": "cust-004", "name": "Vikram Singh", "email": "vikram.singh@email.com", "phone": "+91-9876543213", "created_at": (now - timedelta(days=10)).isoformat()},
        {"id": "cust-005", "name": "Ananya Joshi", "email": "ananya.joshi@email.com", "phone": "+91-9876543214", "created_at": (now - timedelta(days=5)).isoformat()},
    ]
    result = sb.table("customers").upsert(data, on_conflict="id").execute()
    print(f"[OK] Inserted {len(result.data)} customers")
    return result.data


def seed_sla_config():
    data = [
        {"id": "sla-001", "priority": "High", "deadline_hours": 4},
        {"id": "sla-002", "priority": "Medium", "deadline_hours": 8},
        {"id": "sla-003", "priority": "Low", "deadline_hours": 24},
    ]
    result = sb.table("sla_config").upsert(data, on_conflict="id").execute()
    print(f"[OK] Inserted {len(result.data)} SLA configs")
    return result.data


def seed_complaints():
    now = datetime.now(timezone.utc)
    
    resolution_steps_product = '["1. Verify product warranty status","2. Check for common troubleshooting steps","3. Initiate replacement if under warranty","4. Schedule pickup for defective unit"]'
    resolution_steps_packaging = '["1. Document packaging damage with photos","2. Verify shipping carrier and tracking info","3. Arrange replacement shipment","4. File carrier damage claim if applicable"]'
    resolution_steps_trade = '["1. Verify order details and customer account","2. Check inventory and fulfillment status","3. Coordinate with logistics for delivery update","4. Provide resolution timeline to customer"]'

    data = [
        {
            "id": "comp-001",
            "customer_id": "cust-001",
            "raw_text": "Product stopped working after just 2 days of use. Very disappointed with the quality!",
            "category": "Product",
            "priority": "High",
            "resolution_steps": resolution_steps_product,
            "sentiment_score": -0.75,
            "status": "open",
            "submitted_via": "call",
            "sla_deadline": (now + timedelta(hours=4)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-002-call",
            "resolved_at": None,
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "comp-002",
            "customer_id": "cust-002",
            "raw_text": "Package arrived completely crushed. The outer box was in terrible condition.",
            "category": "Packaging",
            "priority": "High",
            "resolution_steps": resolution_steps_packaging,
            "sentiment_score": -0.6,
            "status": "in_progress",
            "submitted_via": "email",
            "sla_deadline": (now + timedelta(hours=3)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-002-call",
            "resolved_at": None,
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(hours=5)).isoformat(),
        },
        {
            "id": "comp-003",
            "customer_id": "cust-003",
            "raw_text": "Bulk order discount not applied as promised by the sales representative.",
            "category": "Trade",
            "priority": "Medium",
            "resolution_steps": resolution_steps_trade,
            "sentiment_score": -0.3,
            "status": "in_progress",
            "submitted_via": "dashboard",
            "sla_deadline": (now + timedelta(hours=6)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-001-admin",
            "resolved_at": None,
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(days=2)).isoformat(),
        },
        {
            "id": "comp-004",
            "customer_id": "cust-001",
            "raw_text": "The device overheats within 30 minutes of operation. Safety concern!",
            "category": "Product",
            "priority": "High",
            "resolution_steps": resolution_steps_product,
            "sentiment_score": -0.8,
            "status": "escalated",
            "submitted_via": "call",
            "sla_deadline": (now - timedelta(hours=1)).isoformat(),
            "sla_breached": True,
            "created_by": "prof-002-call",
            "resolved_at": None,
            "escalated_at": (now - timedelta(hours=2)).isoformat(),
            "escalation_reason": "Customer threatened legal action",
            "created_at": (now - timedelta(days=1)).isoformat(),
        },
        {
            "id": "comp-005",
            "customer_id": "cust-004",
            "raw_text": "Missing items from my order. Only received 3 out of 5 items.",
            "category": "Packaging",
            "priority": "Medium",
            "resolution_steps": resolution_steps_packaging,
            "sentiment_score": -0.4,
            "status": "open",
            "submitted_via": "email",
            "sla_deadline": (now + timedelta(hours=7)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-002-call",
            "resolved_at": None,
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "comp-006",
            "customer_id": "cust-002",
            "raw_text": "Software crashes every time I try to open the settings menu.",
            "category": "Product",
            "priority": "Low",
            "resolution_steps": resolution_steps_product,
            "sentiment_score": -0.2,
            "status": "open",
            "submitted_via": "dashboard",
            "sla_deadline": (now + timedelta(hours=22)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-001-admin",
            "resolved_at": None,
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "id": "comp-007",
            "customer_id": "cust-005",
            "raw_text": "Return policy for bulk orders is unreasonably restrictive.",
            "category": "Trade",
            "priority": "Low",
            "resolution_steps": resolution_steps_trade,
            "sentiment_score": 0.1,
            "status": "resolved",
            "submitted_via": "email",
            "sla_deadline": (now - timedelta(hours=20)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-002-call",
            "resolved_at": (now - timedelta(hours=4)).isoformat(),
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(days=2)).isoformat(),
        },
        {
            "id": "comp-008",
            "customer_id": "cust-003",
            "raw_text": "The product color is completely different from what was shown on the website.",
            "category": "Product",
            "priority": "Medium",
            "resolution_steps": resolution_steps_product,
            "sentiment_score": -0.5,
            "status": "resolved",
            "submitted_via": "call",
            "sla_deadline": (now - timedelta(hours=6)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-002-call",
            "resolved_at": (now - timedelta(hours=1)).isoformat(),
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(hours=8)).isoformat(),
        },
        {
            "id": "comp-009",
            "customer_id": "cust-004",
            "raw_text": "Invoice amount does not match the quoted price. Overcharged by 15%.",
            "category": "Trade",
            "priority": "High",
            "resolution_steps": resolution_steps_trade,
            "sentiment_score": -0.7,
            "status": "open",
            "submitted_via": "email",
            "sla_deadline": (now + timedelta(hours=2)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-002-call",
            "resolved_at": None,
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(minutes=30)).isoformat(),
        },
        {
            "id": "comp-010",
            "customer_id": "cust-005",
            "raw_text": "No protective covering on the fragile parts during shipping. Everything was scratched.",
            "category": "Packaging",
            "priority": "Low",
            "resolution_steps": resolution_steps_packaging,
            "sentiment_score": -0.35,
            "status": "in_progress",
            "submitted_via": "dashboard",
            "sla_deadline": (now + timedelta(hours=16)).isoformat(),
            "sla_breached": False,
            "created_by": "prof-001-admin",
            "resolved_at": None,
            "escalated_at": None,
            "escalation_reason": None,
            "created_at": (now - timedelta(hours=8)).isoformat(),
        },
    ]
    
    result = sb.table("complaints").upsert(data, on_conflict="id").execute()
    print(f"[OK] Inserted {len(result.data)} complaints")
    return result.data


def seed_timeline():
    now = datetime.now(timezone.utc)
    
    data = [
        {"id": "tl-001", "complaint_id": "comp-001", "action": "complaint_created", "performed_by": "prof-002-call", "notes": "Complaint received via phone call", "created_at": (now - timedelta(hours=2)).isoformat()},
        {"id": "tl-002", "complaint_id": "comp-002", "action": "complaint_created", "performed_by": "prof-002-call", "notes": "Complaint received via email", "created_at": (now - timedelta(hours=5)).isoformat()},
        {"id": "tl-003", "complaint_id": "comp-002", "action": "status_changed", "performed_by": "prof-002-call", "notes": "Status changed to in_progress", "created_at": (now - timedelta(hours=3)).isoformat()},
        {"id": "tl-004", "complaint_id": "comp-003", "action": "complaint_created", "performed_by": "prof-001-admin", "notes": "Complaint received via dashboard", "created_at": (now - timedelta(days=2)).isoformat()},
        {"id": "tl-005", "complaint_id": "comp-003", "action": "status_changed", "performed_by": "prof-001-admin", "notes": "Status changed to in_progress", "created_at": (now - timedelta(days=1)).isoformat()},
        {"id": "tl-006", "complaint_id": "comp-004", "action": "complaint_created", "performed_by": "prof-002-call", "notes": "Complaint received via phone call", "created_at": (now - timedelta(days=1)).isoformat()},
        {"id": "tl-007", "complaint_id": "comp-004", "action": "complaint_escalated", "performed_by": "prof-002-call", "notes": "Customer threatened legal action", "created_at": (now - timedelta(hours=2)).isoformat()},
        {"id": "tl-008", "complaint_id": "comp-005", "action": "complaint_created", "performed_by": "prof-002-call", "notes": "Complaint received via email", "created_at": (now - timedelta(hours=1)).isoformat()},
        {"id": "tl-009", "complaint_id": "comp-006", "action": "complaint_created", "performed_by": "prof-001-admin", "notes": "Complaint received via dashboard", "created_at": (now - timedelta(hours=3)).isoformat()},
        {"id": "tl-010", "complaint_id": "comp-007", "action": "complaint_created", "performed_by": "prof-002-call", "notes": "Complaint received via email", "created_at": (now - timedelta(days=2)).isoformat()},
        {"id": "tl-011", "complaint_id": "comp-007", "action": "status_changed", "performed_by": "prof-002-call", "notes": "Status changed to in_progress", "created_at": (now - timedelta(days=1)).isoformat()},
        {"id": "tl-012", "complaint_id": "comp-007", "action": "status_changed", "performed_by": "prof-002-call", "notes": "Status changed to resolved", "created_at": (now - timedelta(hours=4)).isoformat()},
        {"id": "tl-013", "complaint_id": "comp-008", "action": "complaint_created", "performed_by": "prof-002-call", "notes": "Complaint received via phone call", "created_at": (now - timedelta(hours=8)).isoformat()},
        {"id": "tl-014", "complaint_id": "comp-008", "action": "status_changed", "performed_by": "prof-002-call", "notes": "Status changed to in_progress", "created_at": (now - timedelta(hours=6)).isoformat()},
        {"id": "tl-015", "complaint_id": "comp-008", "action": "status_changed", "performed_by": "prof-002-call", "notes": "Status changed to resolved", "created_at": (now - timedelta(hours=1)).isoformat()},
        {"id": "tl-016", "complaint_id": "comp-009", "action": "complaint_created", "performed_by": "prof-002-call", "notes": "Complaint received via email", "created_at": (now - timedelta(minutes=30)).isoformat()},
        {"id": "tl-017", "complaint_id": "comp-010", "action": "complaint_created", "performed_by": "prof-001-admin", "notes": "Complaint received via dashboard", "created_at": (now - timedelta(hours=8)).isoformat()},
        {"id": "tl-018", "complaint_id": "comp-010", "action": "status_changed", "performed_by": "prof-001-admin", "notes": "Status changed to in_progress", "created_at": (now - timedelta(hours=4)).isoformat()},
    ]
    
    result = sb.table("complaint_timeline").upsert(data, on_conflict="id").execute()
    print(f"[OK] Inserted {len(result.data)} timeline entries")
    return result.data


def verify():
    tables = ["profiles", "customers", "sla_config", "complaints", "complaint_timeline", "daily_metrics"]
    print("\n" + "=" * 55)
    print("VERIFICATION - Row counts")
    print("=" * 55)
    for table in tables:
        try:
            result = sb.table(table).select("*", count="exact").execute()
            count = len(result.data)
            print(f"  {table:.<35} {count:>3} rows")
        except Exception as e:
            print(f"  {table:.<35} ERROR: {e}")
    print("=" * 55)


def main():
    print("=" * 55)
    print("SUPABASE DATA SEEDER (via REST API)")
    print("=" * 55)
    
    try:
        print("\n[STEP 1] Seeding profiles (2 users)...")
        seed_profiles()
        
        print("[STEP 2] Seeding customers (5 customers)...")
        seed_customers()
        
        print("[STEP 3] Seeding SLA config (3 priorities)...")
        seed_sla_config()
        
        print("[STEP 4] Seeding complaints (10 complaints)...")
        seed_complaints()
        
        print("[STEP 5] Seeding timeline (18 entries)...")
        seed_timeline()
        
        print("[STEP 6] Verifying all data...")
        verify()
        
        print("\n[OK] DATA SEEDING COMPLETE!")
        print("\nCheck your tables at:")
        print("  https://supabase.com/dashboard/project/lawvfitflgnntxtgjltp/editor")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()