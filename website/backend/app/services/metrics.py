from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.models import Complaint, DailyMetrics, StatusEnum
from app.services.utils import generate_uuid7


def compute_daily_metrics(db: Session):
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= today
    ).scalar() or 0

    open_count = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= today,
        Complaint.status == StatusEnum.open,
    ).scalar() or 0

    resolved_count = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= today,
        Complaint.status == StatusEnum.resolved,
    ).scalar() or 0

    escalated_count = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= today,
        Complaint.status == StatusEnum.escalated,
    ).scalar() or 0

    avg_resolution = db.query(
        func.avg(
            func.extract("epoch", Complaint.resolved_at - Complaint.created_at) / 3600
        )
    ).filter(
        Complaint.created_at >= today,
        Complaint.status == StatusEnum.resolved,
        Complaint.resolved_at.isnot(None),
    ).scalar()
    avg_resolution_time = round(avg_resolution, 2) if avg_resolution else None

    total_for_sla = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= today,
        Complaint.status != StatusEnum.open,
    ).scalar() or 0

    sla_compliant = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= today,
        Complaint.status != StatusEnum.open,
        Complaint.sla_breached == False,
    ).scalar() or 0

    sla_compliance_rate = round((sla_compliant / total_for_sla) * 100, 2) if total_for_sla > 0 else 100.0

    existing = db.query(DailyMetrics).filter(DailyMetrics.date == today).first()

    if existing:
        existing.total_complaints = total
        existing.open_complaints = open_count
        existing.resolved_complaints = resolved_count
        existing.escalated_complaints = escalated_count
        existing.avg_resolution_time_hours = avg_resolution_time
        existing.sla_compliance_rate = sla_compliance_rate
    else:
        metric = DailyMetrics(
            id=generate_uuid7(),
            date=today,
            total_complaints=total,
            open_complaints=open_count,
            resolved_complaints=resolved_count,
            escalated_complaints=escalated_count,
            avg_resolution_time_hours=avg_resolution_time,
            sla_compliance_rate=sla_compliance_rate,
        )
        db.add(metric)

    db.commit()