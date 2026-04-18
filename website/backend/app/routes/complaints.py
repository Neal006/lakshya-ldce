import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from math import ceil
from app.database import get_db
from app.models.models import (
    Profile, Customer, Complaint, ComplaintTimeline,
    CategoryEnum, PriorityEnum, StatusEnum, SubmittedViaEnum, RoleEnum,
)
from app.schemas.complaint import (
    CreateComplaintRequest, UpdateStatusRequest, EscalateRequest,
    ComplaintResponse, ComplaintDetailResponse, ComplaintListItemResponse,
    CallAttenderListItemResponse, CustomerBriefResponse, CustomerNameOnlyResponse,
    TimelineEntryResponse, PaginationResponse, ComplaintListResponse,
    CallAttenderListResponse, StatusUpdateResponse, EscalateResponse,
    DataWrapperComplaint, DataWrapperComplaintDetail,
    DataWrapperComplaintList, DataWrapperCallAttenderList,
    DataWrapperStatusUpdate, DataWrapperEscalate,
)
from app.services.ml import classify_complaint
from app.services.sla import calculate_sla_deadline
from app.services.sse_events import broadcast_new_complaint, broadcast_status_change
from app.services.email import send_resolution_notification, send_escalation_notification
from app.middleware.auth import get_current_user, require_roles
from app.middleware.exceptions import AppException

router = APIRouter()

ALLOWED_TRANSITIONS = {
    StatusEnum.open: [StatusEnum.in_progress, StatusEnum.resolved, StatusEnum.escalated],
    StatusEnum.in_progress: [StatusEnum.resolved, StatusEnum.escalated],
    StatusEnum.escalated: [StatusEnum.in_progress, StatusEnum.resolved],
    StatusEnum.resolved: [],
}


@router.post("", status_code=201, response_model=DataWrapperComplaint)
async def create_complaint(request: CreateComplaintRequest, db: Session = Depends(get_db), current_user: Profile = Depends(require_roles("admin", "call_attender"))):
    customer = db.query(Customer).filter(Customer.email == request.customer_email).first()
    if not customer:
        customer = Customer(
            name=request.customer_name,
            email=request.customer_email,
            phone=request.customer_phone,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    try:
        ml_result = await classify_complaint(request.raw_text)
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
        raw_text=request.raw_text,
        category=category_enum,
        priority=priority_enum,
        resolution_steps=resolution_steps_json,
        sentiment_score=sentiment_score,
        status=StatusEnum.open,
        submitted_via=SubmittedViaEnum(request.submitted_via.value),
        sla_deadline=sla_deadline,
        created_by=current_user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        action="complaint_created",
        performed_by=current_user.id,
        notes=f"Complaint received via {request.submitted_via.value}",
    )
    db.add(timeline_entry)
    db.commit()

    await broadcast_new_complaint(complaint.id)

    complaint.resolution_steps = resolution_steps
    complaint_response = _format_complaint_response(complaint, customer, db)

    return DataWrapperComplaint(data={"complaint": complaint_response.model_dump(mode="json")})


@router.get("", response_model=DataWrapperComplaintList)
def list_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    submitted_via: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    query = db.query(Complaint)

    if status:
        try:
            query = query.filter(Complaint.status == StatusEnum(status))
        except ValueError:
            pass
    if category:
        try:
            query = query.filter(Complaint.category == CategoryEnum(category))
        except ValueError:
            pass
    if priority:
        try:
            query = query.filter(Complaint.priority == PriorityEnum(priority))
        except ValueError:
            pass
    if submitted_via:
        try:
            query = query.filter(Complaint.submitted_via == SubmittedViaEnum(submitted_via))
        except ValueError:
            pass
    if search:
        query = query.filter(Complaint.raw_text.ilike(f"%{search}%"))

    total = query.count()
    total_pages = ceil(total / limit) if total > 0 else 1
    complaints = query.order_by(Complaint.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    if current_user.role == RoleEnum.call_attender:
        items = []
        for c in complaints:
            steps = c.resolution_steps
            if isinstance(steps, str):
                try:
                    steps = json.loads(steps)
                except (json.JSONDecodeError, TypeError):
                    steps = []
            items.append(CallAttenderListItemResponse(
                id=c.id,
                customer=CustomerNameOnlyResponse(name=c.customer.name if c.customer else "Unknown"),
                raw_text=c.raw_text,
                resolution_steps=steps,
                status=c.status.value,
                created_at=c.created_at,
            ))
        return DataWrapperCallAttenderList(data=CallAttenderListResponse(
            complaints=items,
            pagination=PaginationResponse(page=page, limit=limit, total=total, total_pages=total_pages),
        ).model_dump(mode="json"))

    items = []
    for c in complaints:
        items.append(ComplaintListItemResponse(
            id=c.id,
            customer=CustomerBriefResponse(
                name=c.customer.name if c.customer else "Unknown",
                email=c.customer.email if c.customer else "",
            ),
            raw_text=c.raw_text,
            category=c.category.value if c.category else None,
            priority=c.priority.value if c.priority else None,
            status=c.status.value,
            sla_deadline=c.sla_deadline,
            sla_breached=c.sla_breached,
            created_at=c.created_at,
        ))

    return DataWrapperComplaintList(data=ComplaintListResponse(
        complaints=items,
        pagination=PaginationResponse(page=page, limit=limit, total=total, total_pages=total_pages),
    ).model_dump(mode="json"))


@router.get("/{complaint_id}", response_model=DataWrapperComplaintDetail)
def get_complaint(complaint_id: str, db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise AppException(status_code=404, code="NOT_FOUND", message="Complaint not found")

    customer = complaint.customer
    steps = complaint.resolution_steps
    if isinstance(steps, str):
        try:
            steps = json.loads(steps)
        except (json.JSONDecodeError, TypeError):
            steps = []

    timeline = []
    for entry in complaint.timeline:
        performer = None
        if entry.performed_by_profile:
            performer = {"name": entry.performed_by_profile.name, "role": entry.performed_by_profile.role.value}
        timeline.append(TimelineEntryResponse(
            id=entry.id,
            action=entry.action,
            performed_by=performer,
            notes=entry.notes,
            created_at=entry.created_at,
        ))

    response = ComplaintDetailResponse(
        id=complaint.id,
        customer_id=complaint.customer_id,
        customer=CustomerBriefResponse(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
        ),
        raw_text=complaint.raw_text,
        category=complaint.category.value if complaint.category else None,
        priority=complaint.priority.value if complaint.priority else None,
        resolution_steps=steps,
        sentiment_score=complaint.sentiment_score,
        status=complaint.status.value,
        submitted_via=complaint.submitted_via.value,
        sla_deadline=complaint.sla_deadline,
        sla_breached=complaint.sla_breached,
        created_at=complaint.created_at,
        resolved_at=complaint.resolved_at,
        timeline=timeline,
    )
    return DataWrapperComplaintDetail(data={"complaint": response.model_dump(mode="json")})


@router.patch("/{complaint_id}/status", response_model=DataWrapperStatusUpdate)
async def update_complaint_status(
    complaint_id: str,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin", "call_attender")),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise AppException(status_code=404, code="NOT_FOUND", message="Complaint not found")

    new_status = request.status
    allowed = ALLOWED_TRANSITIONS.get(complaint.status, [])
    if new_status not in allowed:
        raise AppException(
            status_code=400,
            code="INVALID_STATUS_TRANSITION",
            message=f"Cannot transition from {complaint.status.value} to {new_status.value}",
        )

    complaint.status = new_status
    if new_status == StatusEnum.resolved:
        complaint.resolved_at = datetime.now(timezone.utc)

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        action="status_changed",
        performed_by=current_user.id,
        notes=request.notes or f"Status changed to {new_status.value}",
    )
    db.add(timeline_entry)
    db.commit()
    db.refresh(complaint)

    await broadcast_status_change(complaint.id, complaint.status.value)

    if new_status == StatusEnum.resolved and complaint.customer:
        steps = complaint.resolution_steps
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except (json.JSONDecodeError, TypeError):
                steps = []
        await send_resolution_notification(
            customer_name=complaint.customer.name,
            customer_email=complaint.customer.email,
            complaint_id=complaint.id,
            category=complaint.category.value if complaint.category else "General",
            resolution_steps=steps or [],
        )

    timeline = []
    for entry in complaint.timeline[-5:]:
        performer = {"name": entry.performed_by_profile.name} if entry.performed_by_profile else None
        timeline.append(TimelineEntryResponse(
            id=entry.id,
            action=entry.action,
            performed_by=performer,
            notes=entry.notes,
            created_at=entry.created_at,
        ))

    return DataWrapperStatusUpdate(data={"complaint": StatusUpdateResponse(
        id=complaint.id,
        status=complaint.status.value,
        updated_at=complaint.updated_at,
        timeline=timeline,
    ).model_dump(mode="json")})


@router.post("/{complaint_id}/escalate", response_model=DataWrapperEscalate)
async def escalate_complaint(
    complaint_id: str,
    request: EscalateRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin", "call_attender")),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise AppException(status_code=404, code="NOT_FOUND", message="Complaint not found")

    if complaint.status == StatusEnum.resolved:
        raise AppException(
            status_code=400,
            code="INVALID_STATUS_TRANSITION",
            message="Cannot escalate a resolved complaint",
        )

    complaint.status = StatusEnum.escalated
    complaint.escalation_reason = request.reason
    complaint.escalated_at = datetime.now(timezone.utc)

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        action="complaint_escalated",
        performed_by=current_user.id,
        notes=f"Escalated: {request.reason}",
    )
    db.add(timeline_entry)
    db.commit()
    db.refresh(complaint)

    await broadcast_status_change(complaint.id, "escalated")

    if complaint.customer:
        await send_escalation_notification(
            customer_name=complaint.customer.name,
            customer_email=complaint.customer.email,
            complaint_id=complaint.id,
            reason=request.reason,
        )

    return DataWrapperEscalate(data={"complaint": EscalateResponse(
        id=complaint.id,
        status=complaint.status.value,
        escalation_reason=complaint.escalation_reason,
        escalated_at=complaint.escalated_at,
    ).model_dump(mode="json")})


def _format_complaint_response(complaint: Complaint, customer: Customer, db: Session) -> ComplaintResponse:
    steps = complaint.resolution_steps
    if isinstance(steps, str):
        try:
            steps = json.loads(steps)
        except (json.JSONDecodeError, TypeError):
            steps = []

    return ComplaintResponse(
        id=complaint.id,
        customer_id=complaint.customer_id,
        customer=CustomerBriefResponse(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
        ),
        raw_text=complaint.raw_text,
        category=complaint.category.value if complaint.category else None,
        priority=complaint.priority.value if complaint.priority else None,
        resolution_steps=steps,
        sentiment_score=complaint.sentiment_score,
        status=complaint.status.value,
        submitted_via=complaint.submitted_via.value,
        sla_deadline=complaint.sla_deadline,
        sla_breached=complaint.sla_breached,
        created_at=complaint.created_at,
        resolved_at=complaint.resolved_at,
    )