from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, extract
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Complaint, CategoryEnum, PriorityEnum, StatusEnum
from app.middleware.auth import get_current_user, require_roles
from app.middleware.exceptions import AppException
from app.models.models import Profile

router = APIRouter()


@router.get("/dashboard")
async def dashboard_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin", "qa")),
):
    query = db.query(Complaint)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Complaint.created_at >= start_dt)
        except (ValueError, TypeError):
            raise AppException(status_code=400, code="VALIDATION_ERROR", message="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(Complaint.created_at <= end_dt)
        except (ValueError, TypeError):
            raise AppException(status_code=400, code="VALIDATION_ERROR", message="Invalid end_date format")

    total_complaints = query.count()
    open_complaints = query.filter(Complaint.status == StatusEnum.open).count()
    in_progress_complaints = query.filter(Complaint.status == StatusEnum.in_progress).count()
    resolved_complaints = query.filter(Complaint.status == StatusEnum.resolved).count()
    escalated_complaints = query.filter(Complaint.status == StatusEnum.escalated).count()

    avg_resolution_result = query.filter(
        Complaint.status == StatusEnum.resolved,
        Complaint.resolved_at.isnot(None),
        Complaint.created_at.isnot(None),
    ).with_entities(
        func.avg(
            func.extract("epoch", Complaint.resolved_at - Complaint.created_at) / 3600
        )
    ).scalar()
    avg_resolution_time_hours = round(avg_resolution_result, 1) if avg_resolution_result else None

    total_for_sla = query.filter(Complaint.status != StatusEnum.open).count()
    sla_compliant = query.filter(
        Complaint.sla_breached == False,
        Complaint.status != StatusEnum.open,
    ).count()
    sla_compliance_rate = round((sla_compliant / total_for_sla) * 100, 1) if total_for_sla > 0 else 100.0

    by_category = []
    for cat in CategoryEnum:
        count = query.filter(Complaint.category == cat).count()
        percentage = round((count / total_complaints) * 100, 1) if total_complaints > 0 else 0
        by_category.append({"category": cat.value, "count": count, "percentage": percentage})

    by_priority = []
    for pri in PriorityEnum:
        count = query.filter(Complaint.priority == pri).count()
        percentage = round((count / total_complaints) * 100, 1) if total_complaints > 0 else 0
        by_priority.append({"priority": pri.value, "count": count, "percentage": percentage})

    by_status = []
    for st in StatusEnum:
        count = query.filter(Complaint.status == st).count()
        by_status.append({"status": st.value, "count": count})

    resolution_trend_query = query.filter(
        Complaint.status == StatusEnum.resolved,
        Complaint.resolved_at.isnot(None),
        Complaint.created_at.isnot(None),
    )

    effective_start = start_dt if start_date else None
    effective_end = end_dt if end_date else datetime.now(timezone.utc)
    if not effective_start:
        earliest = db.query(func.min(Complaint.created_at)).filter(
            Complaint.status == StatusEnum.resolved,
            Complaint.resolved_at.isnot(None),
        ).scalar()
        effective_start = earliest if earliest else effective_end - timedelta(days=30)

    trend_results = resolution_trend_query.with_entities(
        func.date_trunc("day", Complaint.resolved_at).label("day"),
        func.avg(
            func.extract("epoch", Complaint.resolved_at - Complaint.created_at) / 3600
        ).label("avg_hours"),
    ).group_by(func.date_trunc("day", Complaint.resolved_at)).order_by(func.date_trunc("day", Complaint.resolved_at)).all()

    resolution_time_trend = [
        {"date": row.day.strftime("%Y-%m-%d") if row.day else "", "avg_hours": round(row.avg_hours, 1) if row.avg_hours else 0}
        for row in trend_results
    ]

    hour_query = query.with_entities(
        extract("hour", Complaint.created_at).label("hour"),
        func.count(Complaint.id).label("count"),
    ).group_by(extract("hour", Complaint.created_at)).order_by(extract("hour", Complaint.created_at)).all()

    complaints_by_hour = [{"hour": int(row.hour), "count": row.count} for row in hour_query]

    return {
        "data": {
            "summary": {
                "total_complaints": total_complaints,
                "open_complaints": open_complaints,
                "resolved_complaints": resolved_complaints,
                "escalated_complaints": escalated_complaints,
                "avg_resolution_time_hours": avg_resolution_time_hours,
                "sla_compliance_rate": sla_compliance_rate,
            },
            "by_category": by_category,
            "by_priority": by_priority,
            "by_status": by_status,
            "resolution_time_trend": resolution_time_trend,
            "complaints_by_hour": complaints_by_hour,
        }
    }


@router.get("/products")
async def product_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin", "qa")),
):
    query = db.query(Complaint)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Complaint.created_at >= start_dt)
        except (ValueError, TypeError):
            raise AppException(status_code=400, code="VALIDATION_ERROR", message="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(Complaint.created_at <= end_dt)
        except (ValueError, TypeError):
            raise AppException(status_code=400, code="VALIDATION_ERROR", message="Invalid end_date format")

    if category:
        try:
            cat_enum = CategoryEnum(category)
            query = query.filter(Complaint.category == cat_enum)
        except ValueError:
            raise AppException(status_code=400, code="VALIDATION_ERROR", message=f"Invalid category: {category}")

    results = query.with_entities(
        Complaint.category,
        func.count(Complaint.id).label("complaint_count"),
    ).group_by(Complaint.category).all()

    products = []
    for row in results:
        cat_name = row.category.value if row.category else "Uncategorized"

        cat_query = query.filter(Complaint.category == row.category) if row.category else query

        top_issues = db.query(Complaint.raw_text).filter(
            Complaint.category == row.category if row.category else True
        ).order_by(Complaint.created_at.desc()).limit(5).all()
        top_issue_texts = [t[0][:50] for t in top_issues[:3]]

        avg_res = db.query(
            func.avg(
                func.extract("epoch", Complaint.resolved_at - Complaint.created_at) / 3600
            )
        ).filter(
            Complaint.category == row.category if row.category else True,
            Complaint.status == StatusEnum.resolved,
            Complaint.resolved_at.isnot(None),
        ).scalar()

        products.append({
            "product_name": cat_name,
            "complaint_count": row.complaint_count,
            "top_issues": top_issue_texts,
            "avg_resolution_time": round(avg_res, 1) if avg_res else None,
            "category": cat_name,
        })

    return {"data": {"products": products}}