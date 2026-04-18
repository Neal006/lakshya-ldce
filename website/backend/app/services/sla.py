from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.models import Complaint, SLAConfig, PriorityEnum, StatusEnum


DEFAULT_SLA_HOURS = {
    PriorityEnum.high: 4,
    PriorityEnum.medium: 8,
    PriorityEnum.low: 24,
}


def calculate_sla_deadline(priority: str, db: Session) -> datetime:
    sla_config = db.query(SLAConfig).filter(SLAConfig.priority == PriorityEnum(priority)).first()
    hours = sla_config.deadline_hours if sla_config else DEFAULT_SLA_HOURS.get(PriorityEnum(priority), 8)
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def check_sla_breaches(db: Session) -> list[str]:
    now = datetime.now(timezone.utc)
    breached = db.query(Complaint).filter(
        Complaint.sla_deadline < now,
        Complaint.sla_breached == False,
        Complaint.status != StatusEnum.resolved,
    ).all()
    breached_ids = []
    for complaint in breached:
        complaint.sla_breached = True
        breached_ids.append(complaint.id)
    if breached_ids:
        db.commit()
    return breached_ids