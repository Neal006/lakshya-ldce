import json
import hmac
import hashlib
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Customer, Complaint, ComplaintTimeline, SubmittedViaEnum
from app.services.ml import classify_complaint
from app.services.sla import calculate_sla_deadline
from app.services.sse_events import broadcast_new_complaint
from app.middleware.exceptions import AppException
from app.config import BREVO_WEBHOOK_SIGNATURE
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

router = APIRouter()


class InboundEmailPayload(BaseModel):
    event: str = "inbound"
    email: Optional[dict] = None


class EmailData(BaseModel):
    frm: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    subject: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None

    model_config = {"populate_by_name": True}


@router.post("/email/inbound")
async def inbound_email(
    request: Request,
    db: Session = Depends(get_db),
):
    if BREVO_WEBHOOK_SIGNATURE:
        signature = request.headers.get("X-Webhook-Signature", "")
        if not _verify_brevo_signature(await request.body(), signature):
            raise AppException(
                status_code=400,
                code="INVALID_SIGNATURE",
                message="Webhook signature verification failed",
            )

    try:
        body = await request.json()
    except Exception:
        raise AppException(
            status_code=400,
            code="INVALID_PAYLOAD",
            message="Could not parse email payload",
        )

    email_data = body.get("email", body)
    sender_email = email_data.get("from", "").strip()
    subject = email_data.get("subject", "").strip()
    text_body = email_data.get("text", "").strip()
    html_body = email_data.get("html", "").strip()

    complaint_text = text_body or html_body or subject
    if not complaint_text:
        raise AppException(
            status_code=400,
            code="INVALID_PAYLOAD",
            message="No complaint text found in email",
        )

    if subject and subject != complaint_text:
        complaint_text = f"{subject}\n\n{text_body or html_body}"

    if not sender_email:
        raise AppException(
            status_code=400,
            code="INVALID_PAYLOAD",
            message="No sender email found",
        )

    sender_name = sender_email.split("@")[0].replace(".", " ").title()

    customer_created = False
    customer = db.query(Customer).filter(Customer.email == sender_email).first()
    if not customer:
        customer = Customer(
            name=sender_name,
            email=sender_email,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        customer_created = True

    try:
        ml_result = await classify_complaint(complaint_text)
    except Exception:
        ml_result = {
            "category": "Product",
            "priority": "Medium",
            "sentiment_score": 0.0,
            "resolution_steps": [
                "1. Verify product warranty status",
                "2. Check for common troubleshooting steps",
                "3. Initiate replacement if under warranty",
                "4. Schedule pickup for defective unit",
            ],
        }

    from app.models.models import CategoryEnum, PriorityEnum, StatusEnum

    category = ml_result.get("category", "Product")
    priority = ml_result.get("priority", "Medium")
    sentiment_score = ml_result.get("sentiment_score", 0.0)
    resolution_steps = ml_result.get("resolution_steps", [])

    try:
        category_enum = CategoryEnum(category)
    except ValueError:
        category_enum = CategoryEnum.product

    try:
        priority_enum = PriorityEnum(priority)
    except ValueError:
        priority_enum = PriorityEnum.medium

    sla_deadline = calculate_sla_deadline(priority_enum.value, db)

    if isinstance(resolution_steps, list):
        resolution_steps_json = json.dumps(resolution_steps)
    else:
        resolution_steps_json = resolution_steps

    complaint = Complaint(
        customer_id=customer.id,
        raw_text=complaint_text,
        category=category_enum,
        priority=priority_enum,
        resolution_steps=resolution_steps_json,
        sentiment_score=sentiment_score,
        status=StatusEnum.open,
        submitted_via=SubmittedViaEnum.email,
        sla_deadline=sla_deadline,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        action="complaint_created",
        notes=f"Complaint received via email from {sender_email}",
    )
    db.add(timeline_entry)
    db.commit()

    await broadcast_new_complaint(complaint.id)

    return {
        "data": {
            "complaint_id": complaint.id,
            "customer_created": customer_created,
            "message": "Complaint created from email",
        }
    }


def _verify_brevo_signature(payload: bytes, signature: str) -> bool:
    if not BREVO_WEBHOOK_SIGNATURE:
        return True
    expected = hmac.new(
        BREVO_WEBHOOK_SIGNATURE.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)