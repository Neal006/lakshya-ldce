import random
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import (
    Profile, Customer, Complaint, ComplaintTimeline, SLAConfig,
    CategoryEnum, PriorityEnum, StatusEnum, SubmittedViaEnum, RoleEnum,
)
from app.middleware.auth import require_roles
from app.services.sla import calculate_sla_deadline
from pydantic import BaseModel, Field

router = APIRouter()


class SeedRequest(BaseModel):
    count: int = Field(default=100, ge=1, le=5000)


CUSTOMER_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohan Gupta", "Ananya Singh", "Vikram Reddy",
    "Neha Joshi", "Arjun Kumar", "Kavya Nair", "Aditya Verma", "Meera Iyer",
    "Rahul Deshmukh", "Sanya Kapoor", "Dev Bhat", "Ishita Rao", "Karan Mehta",
    "Pooja Saxena", "Rishi Agarwal", "Simran Kaur", "Varun Malhotra", "Tanya Choudhary",
    "Nikhil Pandey", "Divya Menon", "Amit Chauhan", "Ritu Bhattacharya", "Suresh Hegde",
]

PRODUCT_COMPLAINTS = [
    "Product stopped working after 2 days of use. Very disappointed with the quality.",
    "The device overheats within 30 minutes of operation. Safety concern!",
    "Received a defective unit. Screen flickers constantly.",
    "Battery drains extremely fast. Lasts only 30 minutes on full charge.",
    "Software crashes every time I try to open the settings menu.",
    "The product makes a loud grinding noise when turned on. Unusable!",
    "Color is completely different from what was shown on the website.",
    "Missing components in the package. User manual was not included.",
    "The power button broke after just one week of use. Very fragile.",
    "Product fails to connect to WiFi despite multiple attempts.",
    "Touchscreen response is delayed by several seconds. Frustrating experience.",
    "Audio quality is terrible - constant static and buzzing noise.",
    "Camera produces blurry images even in good lighting conditions.",
    "Water resistance claim is false. Device got damaged in light rain.",
    "Charging port is loose and doesn't hold the cable properly.",
]

PACKAGING_COMPLAINTS = [
    "Package arrived completely crushed. The outer box was in terrible condition.",
    "Received the wrong item instead of what I ordered. Mixed up order.",
    "Missing items from my order. Only 3 out of 5 items were in the box.",
    "Packaging was torn and the product was exposed. No bubble wrap at all.",
    "The seal on the box was already broken when I received it.",
    "Items were loose inside the package with no padding. Everything was scratched.",
    "Delivery was delayed by 2 weeks. No tracking updates provided.",
    "Product box was damaged and looked like it had been opened before.",
    "No protective covering on the fragile parts during shipping.",
    "Package left in the rain outside my door. Everything was soaked.",
    "Multiple items were dented due to poor packaging material.",
    "The shipping label was stuck directly on the product box, not the outer box.",
    "Insulation material was insufficient. Frozen items arrived thawed.",
    "Recyclable packaging claim is false - lots of plastic wrap used.",
    "The outer carton was too small for the items, forcing them to be crammed in.",
]

TRADE_COMPLAINTS = [
    "Ordered 500 units but only received 200. Short shipment.",
    "Bulk order discount not applied as promised by the sales representative.",
    "Invoice amount does not match the quoted price. Overcharged by 15%.",
    "Trade credit application rejected without proper review. Unfair.",
    "Return policy for bulk orders is unreasonably restrictive.",
    "Warranty terms for bulk purchase are different from individual purchase.",
    "Delivery timeline was promised at 3 days but took 3 weeks.",
    "Product catalog prices not matching the actual invoiced prices.",
    "Sales representative provided incorrect product specifications.",
    "Minimum order quantity is too high for small businesses.",
    "Refund for returned bulk order has been pending for 60 days.",
    "Customer support for trade accounts is unresponsive. No callback.",
    "Volume discount tier structure is unclear and misleading.",
    "Shipping charges for international bulk orders are excessive.",
    "Contract renewal terms were changed without prior notification.",
]


@router.post("/seed")
async def seed_demo(
    request: SeedRequest = SeedRequest(),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin")),
):
    count = request.count

    sla_configs = db.query(SLAConfig).all()
    if not sla_configs:
        default_slas = [
            SLAConfig(priority=PriorityEnum.high, deadline_hours=4),
            SLAConfig(priority=PriorityEnum.medium, deadline_hours=8),
            SLAConfig(priority=PriorityEnum.low, deadline_hours=24),
        ]
        for sla in default_slas:
            db.add(sla)
        db.commit()

    statuses = list(StatusEnum)
    categories = list(CategoryEnum)
    priorities = list(PriorityEnum)
    submission_channels = list(SubmittedViaEnum)

    category_complaints = {
        CategoryEnum.product: PRODUCT_COMPLAINTS,
        CategoryEnum.packaging: PACKAGING_COMPLAINTS,
        CategoryEnum.trade: TRADE_COMPLAINTS,
    }

    customers = []
    for name in CUSTOMER_NAMES * 2:
        email = f"{name.lower().replace(' ', '.')}@example.com"
        existing = db.query(Customer).filter(Customer.email == email).first()
        if existing:
            customers.append(existing)
        else:
            customer = Customer(
                name=name,
                email=email,
                phone=f"+91-{random.randint(7000000000, 9999999999)}",
            )
            db.add(customer)
            customers.append(customer)

    db.flush()

    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    complaints_created = 0

    for i in range(count):
        category = random.choice(categories)
        complaint_text = random.choice(category_complaints[category])

        priority_weights = [0.2, 0.5, 0.3]
        priority = random.choices(priorities, weights=priority_weights, k=1)[0]

        status_weights = [0.15, 0.2, 0.55, 0.1]
        status = random.choices(statuses, weights=status_weights, k=1)[0]

        customer = random.choice(customers)

        submitted_via = random.choice(submission_channels)

        created_at = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        sentiment_score = round(random.uniform(-0.8, 0.5), 2)

        resolution_steps_map = {
            CategoryEnum.product: json.dumps([
                "1. Verify product warranty status",
                "2. Check for common troubleshooting steps",
                "3. Initiate replacement if under warranty",
                "4. Schedule pickup for defective unit",
            ]),
            CategoryEnum.packaging: json.dumps([
                "1. Document packaging damage with photos",
                "2. Verify shipping carrier and tracking info",
                "3. Arrange replacement shipment",
                "4. File carrier damage claim if applicable",
            ]),
            CategoryEnum.trade: json.dumps([
                "1. Verify order details and customer account",
                "2. Check inventory and fulfillment status",
                "3. Coordinate with logistics for delivery update",
                "4. Provide resolution timeline to customer",
            ]),
        }

        sla_hours_map = {PriorityEnum.high: 4, PriorityEnum.medium: 8, PriorityEnum.low: 24}
        sla_deadline = created_at + timedelta(hours=sla_hours_map[priority])

        resolved_at = None
        if status == StatusEnum.resolved:
            resolution_hours = random.uniform(1, sla_hours_map[priority] * 1.5)
            resolved_at = created_at + timedelta(hours=resolution_hours)

        escalated_at = None
        escalation_reason = None
        if status == StatusEnum.escalated:
            escalated_at = created_at + timedelta(hours=random.uniform(0.5, 3))
            escalation_reason = random.choice([
                "Customer requested supervisor review",
                "SLA breach imminent",
                "Customer threatened legal action",
                "Recurring issue not resolved by first response",
                "Safety concern identified",
            ])

        sla_breached = False
        if status != StatusEnum.resolved:
            if resolved_at is None:
                check_time = datetime.now(timezone.utc)
                effective_deadline = sla_deadline
                if check_time > effective_deadline:
                    sla_breached = True
        elif resolved_at and sla_deadline and resolved_at > sla_deadline:
            sla_breached = True

        complaint = Complaint(
            customer_id=customer.id,
            raw_text=complaint_text,
            category=category,
            priority=priority,
            resolution_steps=resolution_steps_map[category],
            sentiment_score=sentiment_score,
            status=status,
            submitted_via=submitted_via,
            sla_deadline=sla_deadline,
            sla_breached=sla_breached,
            created_by=current_user.id,
            resolved_at=resolved_at,
            escalated_at=escalated_at,
            escalation_reason=escalation_reason,
            created_at=created_at,
        )
        db.add(complaint)
        complaints_created += 1

        if complaints_created % 100 == 0:
            db.flush()

    db.commit()

    return {
        "data": {
            "seeded_count": complaints_created,
            "message": "Demo data seeded successfully",
        }
    }


@router.post("/clear")
async def clear_demo(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin")),
):
    complaint_count = db.query(Complaint).count()

    db.query(ComplaintTimeline).delete()
    db.query(Complaint).delete()

    customers_with_complaints = (
        db.query(Customer)
        .filter(~Customer.complaints.any())
        .all()
    )
    for c in customers_with_complaints:
        # Only delete customers that were likely created by demo
        db.delete(c)

    db.commit()

    return {
        "data": {
            "cleared_count": complaint_count,
            "message": "Demo data cleared successfully",
        }
    }