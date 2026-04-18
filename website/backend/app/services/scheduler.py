import asyncio
import logging
from app.database import SessionLocal
from app.services.sla import check_sla_breaches
from app.services.sse_events import broadcast_sla_breach
from app.services.email import send_sla_breach_notification
from app.models.models import Complaint

logger = logging.getLogger(__name__)

_sla_task = None
_metrics_task = None


async def run_sla_checks():
    while True:
        try:
            db = SessionLocal()
            breached_ids = check_sla_breaches(db)
            for complaint_id in breached_ids:
                await broadcast_sla_breach(complaint_id)
                complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
                if complaint and complaint.customer:
                    await send_sla_breach_notification(
                        customer_name=complaint.customer.name,
                        customer_email=complaint.customer.email,
                        complaint_id=complaint.id,
                        sla_deadline=complaint.sla_deadline.isoformat() if complaint.sla_deadline else "N/A",
                    )
            if breached_ids:
                logger.info(f"SLA breach detected for {len(breached_ids)} complaint(s)")
        except Exception as e:
            logger.error(f"SLA breach check failed: {e}")
        try:
            db.close()
        except Exception:
            pass
        await asyncio.sleep(60)


async def run_daily_metrics():
    while True:
        try:
            db = SessionLocal()
            from app.services.metrics import compute_daily_metrics
            compute_daily_metrics(db)
            db.close()
            logger.info("Daily metrics computed")
        except Exception as e:
            logger.error(f"Daily metrics computation failed: {e}")
        try:
            db.close()
        except Exception:
            pass
        await asyncio.sleep(3600)


def start_background_tasks():
    global _sla_task, _metrics_task
    if _sla_task is None or _sla_task.done():
        _sla_task = asyncio.create_task(run_sla_checks())
        logger.info("SLA breach detection background task started")
    if _metrics_task is None or _metrics_task.done():
        _metrics_task = asyncio.create_task(run_daily_metrics())
        logger.info("Daily metrics background task started")