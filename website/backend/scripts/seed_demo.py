#!/usr/bin/env python3
"""
Demo Data Seeding Script with Performance Testing

Seeds the database with sample data and tests query performance.
Uses batch inserts and optimized transactions for minimal overhead.

Usage:
    python scripts/seed_demo.py                    # Seed 100 records
    python scripts/seed_demo.py --count 1000       # Seed 1000 records
    python scripts/seed_demo.py --test-queries     # Test query performance
"""

import os
import sys
import random
import json
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

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.models.models import (
    Profile, Customer, Complaint, ComplaintTimeline, SLAConfig,
    CategoryEnum, PriorityEnum, StatusEnum, SubmittedViaEnum, RoleEnum
)
from app.services.utils import generate_uuid7
from app.database import Base, engine

Session = sessionmaker(bind=engine)

# Sample data for realistic complaints
SAMPLE_COMPLAINTS = {
    CategoryEnum.product: [
        "Product stopped working after just 2 days of use. Very disappointed!",
        "The device overheats within 30 minutes. Safety hazard!",
        "Received defective unit with flickering screen.",
        "Battery drains completely in 30 minutes. Not usable.",
        "Software crashes when opening settings menu.",
        "Loud grinding noise when powered on. Unacceptable.",
        "Product color doesn't match website photos.",
        "Missing user manual and accessories in package.",
        "Power button broke after one week. Poor quality.",
        "WiFi connection keeps dropping every few minutes.",
    ],
    CategoryEnum.packaging: [
        "Package arrived crushed and damaged. Outer box torn.",
        "Received wrong item. Ordered X got Y.",
        "Missing items from order. Only partial delivery.",
        "No protective padding. Items scratched and damaged.",
        "Box seal was already broken when delivered.",
        "Items were loose inside with no bubble wrap.",
        "Delivery delayed by 2 weeks. No updates provided.",
        "Product box damaged and looked previously opened.",
        "No fragile handling. Electronics damaged in transit.",
        "Package left outside in rain. Everything soaked.",
    ],
    CategoryEnum.trade: [
        "Ordered 500 units, received only 200. Short shipment.",
        "Bulk discount not applied as promised by sales rep.",
        "Invoice amount exceeds quoted price by 15%.",
        "Trade credit application rejected without review.",
        "Return policy for bulk orders too restrictive.",
        "Warranty terms different from individual purchase.",
        "Promised 3-day delivery took 3 weeks.",
        "Catalog prices don't match invoiced prices.",
        "Sales rep gave incorrect product specifications.",
        "Minimum order quantity too high for small business.",
    ],
}

CUSTOMER_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohan Gupta", "Ananya Singh", "Vikram Reddy",
    "Neha Joshi", "Arjun Kumar", "Kavya Nair", "Aditya Verma", "Meera Iyer",
    "Rahul Deshmukh", "Sanya Kapoor", "Dev Bhat", "Ishita Rao", "Karan Mehta",
    "Pooja Saxena", "Rishi Agarwal", "Simran Kaur", "Varun Malhotra", "Tanya Choudhary",
]


def seed_customers(session, count=20):
    """Create sample customers."""
    customers = []
    
    for i, name in enumerate(CUSTOMER_NAMES[:count]):
        email = f"{name.lower().replace(' ', '.')}@example.com"
        
        # Check if exists
        existing = session.query(Customer).filter(Customer.email == email).first()
        if existing:
            customers.append(existing)
            continue
        
        customer = Customer(
            id=generate_uuid7(),
            name=name,
            email=email,
            phone=f"+91-{random.randint(7000000000, 9999999999)}",
        )
        session.add(customer)
        customers.append(customer)
    
    session.flush()
    print(f"[OK] Created {len(customers)} customers")
    return customers


def seed_complaints(session, customers, count=100):
    """Create sample complaints with realistic data."""
    categories = list(CategoryEnum)
    priorities = list(PriorityEnum)
    statuses = list(StatusEnum)
    channels = list(SubmittedViaEnum)
    
    complaints = []
    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    
    for i in range(count):
        category = random.choice(categories)
        complaint_text = random.choice(SAMPLE_COMPLAINTS[category])
        
        # Weighted priority selection
        priority = random.choices(
            priorities, 
            weights=[0.2, 0.5, 0.3],  # 20% high, 50% medium, 30% low
            k=1
        )[0]
        
        # Weighted status selection
        status = random.choices(
            statuses,
            weights=[0.15, 0.25, 0.50, 0.10],  # open, in_progress, resolved, escalated
            k=1
        )[0]
        
        customer = random.choice(customers)
        
        # Random timestamp within last 30 days
        created_at = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        
        # Calculate SLA deadline based on priority
        sla_hours = {PriorityEnum.high: 4, PriorityEnum.medium: 8, PriorityEnum.low: 24}
        sla_deadline = created_at + timedelta(hours=sla_hours[priority])
        
        # Determine resolution/escalation times
        resolved_at = None
        escalated_at = None
        escalation_reason = None
        sla_breached = False
        
        if status == StatusEnum.resolved:
            resolution_hours = random.uniform(1, sla_hours[priority] * 0.8)
            resolved_at = created_at + timedelta(hours=resolution_hours)
            if resolved_at > sla_deadline:
                sla_breached = True
        elif status == StatusEnum.escalated:
            escalated_at = created_at + timedelta(hours=random.uniform(0.5, sla_hours[priority] * 0.5))
            escalation_reason = random.choice([
                "Customer requested supervisor",
                "SLA breach imminent",
                "Customer threatened legal action",
                "Recurring issue",
            ])
        
        # Generate resolution steps
        resolution_steps = json.dumps([
            f"1. Verify {category.value.lower()} issue details",
            "2. Check warranty/return eligibility",
            "3. Initiate replacement/refund process",
            "4. Follow up with customer",
        ])
        
        complaint = Complaint(
            id=generate_uuid7(),
            customer_id=customer.id,
            raw_text=complaint_text,
            category=category,
            priority=priority,
            resolution_steps=resolution_steps,
            sentiment_score=round(random.uniform(-0.8, 0.3), 2),
            status=status,
            submitted_via=random.choice(channels),
            sla_deadline=sla_deadline,
            sla_breached=sla_breached,
            resolved_at=resolved_at,
            escalated_at=escalated_at,
            escalation_reason=escalation_reason,
            created_at=created_at,
        )
        session.add(complaint)
        complaints.append(complaint)
        
        # Flush every 100 to manage memory
        if i % 100 == 0 and i > 0:
            session.flush()
    
    session.flush()
    print(f"[OK] Created {len(complaints)} complaints")
    return complaints


def seed_timeline(session, complaints):
    """Create timeline entries for complaints."""
    count = 0
    
    for complaint in complaints:
        # Always add 'created' entry
        timeline = ComplaintTimeline(
            id=generate_uuid7(),
            complaint_id=complaint.id,
            action="complaint_created",
            notes=f"Complaint received via {complaint.submitted_via.value}",
            created_at=complaint.created_at,
        )
        session.add(timeline)
        count += 1
        
        # Add status change if not open
        if complaint.status != StatusEnum.open:
            timeline = ComplaintTimeline(
                id=generate_uuid7(),
                complaint_id=complaint.id,
                action="status_changed",
                notes=f"Status changed to {complaint.status.value}",
                created_at=complaint.created_at + timedelta(hours=1),
            )
            session.add(timeline)
            count += 1
        
        # Add escalation entry if escalated
        if complaint.escalated_at:
            timeline = ComplaintTimeline(
                id=generate_uuid7(),
                complaint_id=complaint.id,
                action="complaint_escalated",
                notes=complaint.escalation_reason or "Escalated",
                created_at=complaint.escalated_at,
            )
            session.add(timeline)
            count += 1
    
    print(f"[OK] Created {count} timeline entries")


def test_query_performance(session):
    """Test query performance with indexes."""
    import time
    
    print("\n" + "=" * 70)
    print("QUERY PERFORMANCE TEST")
    print("=" * 70)
    
    queries = [
        ("Filter by status (open)", 
         lambda s: s.query(Complaint).filter(Complaint.status == StatusEnum.open).count()),
        
        ("Filter by category + priority",
         lambda s: s.query(Complaint).filter(
             Complaint.category == CategoryEnum.product,
             Complaint.priority == PriorityEnum.high
         ).count()),
        
        ("Recent complaints (last 7 days)",
         lambda s: s.query(Complaint).filter(
             Complaint.created_at > datetime.now(timezone.utc) - timedelta(days=7)
         ).count()),
        
        ("SLA breach detection",
         lambda s: s.query(Complaint).filter(
             Complaint.sla_deadline < datetime.now(timezone.utc),
             Complaint.sla_breached == False,
             Complaint.status != StatusEnum.resolved
         ).count()),
        
        ("Customer complaint history",
         lambda s: s.query(Complaint).filter(
             Complaint.customer_id == s.query(Customer).first().id
         ).order_by(Complaint.created_at.desc()).limit(10).all()),
        
        ("Timeline for complaint",
         lambda s: s.query(ComplaintTimeline).filter(
             ComplaintTimeline.complaint_id == s.query(Complaint).first().id
         ).order_by(ComplaintTimeline.created_at).all()),
    ]
    
    for name, query in queries:
        start = time.time()
        try:
            result = query(session)
            elapsed = (time.time() - start) * 1000  # ms
            print(f"  {name:.<40} {elapsed:>8.2f} ms")
        except Exception as e:
            print(f"  {name:.<40} ERROR: {e}")
    
    print("=" * 70)


def show_statistics(session):
    """Display database statistics."""
    print("\n" + "=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)
    
    stats = {
        "Customers": session.query(Customer).count(),
        "Complaints": session.query(Complaint).count(),
        "Timeline Entries": session.query(ComplaintTimeline).count(),
        "Open": session.query(Complaint).filter(Complaint.status == StatusEnum.open).count(),
        "In Progress": session.query(Complaint).filter(Complaint.status == StatusEnum.in_progress).count(),
        "Resolved": session.query(Complaint).filter(Complaint.status == StatusEnum.resolved).count(),
        "Escalated": session.query(Complaint).filter(Complaint.status == StatusEnum.escalated).count(),
        "SLA Breached": session.query(Complaint).filter(Complaint.sla_breached == True).count(),
    }
    
    for name, count in stats.items():
        print(f"  {name:.<25} {count:>6}")
    
    print("=" * 70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed demo data with performance testing")
    parser.add_argument("--count", type=int, default=100, help="Number of complaints to create")
    parser.add_argument("--test-queries", action="store_true", help="Test query performance")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TS-14 Demo Data Seeding")
    print("=" * 70)
    
    try:
        with Session() as session:
            if args.stats:
                show_statistics(session)
                return
            
            print(f"\n[STEP 1] Creating {args.count} complaints...")
            
            # Seed in transaction
            customers = seed_customers(session, count=min(20, args.count // 5 + 1))
            complaints = seed_complaints(session, customers, count=args.count)
            seed_timeline(session, complaints)
            
            session.commit()
            print("\n[OK] All data committed successfully")
            
            # Show stats
            show_statistics(session)
            
            # Test queries if requested
            if args.test_queries:
                test_query_performance(session)
            
            print("\n[OK] Demo data seeding complete!")
            
    except SQLAlchemyError as e:
        print(f"\n[ERROR] Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()