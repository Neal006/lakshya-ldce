import asyncio
import logging
from app.database import SessionLocal
from app.services.sla import check_sla_breaches
from app.services.sse_events import broadcast_sla_breach

logger = logging.getLogger(__name__)

_sla_task = None


async def run_sla_checks():
    while True:
        try:
            db = SessionLocal()
            breached_ids = check_sla_breaches(db)
            db.close()
            for complaint_id in breached_ids:
                await broadcast_sla_breach(complaint_id)
            if breached_ids:
                logger.info(f"SLA breach detected for {len(breached_ids)} complaint(s)")
        except Exception as e:
            logger.error(f"SLA breach check failed: {e}")
        try:
            db.close()
        except Exception:
            pass
        await asyncio.sleep(60)


def start_sla_background_task():
    global _sla_task
    if _sla_task is None or _sla_task.done():
        _sla_task = asyncio.create_task(run_sla_checks())
        logger.info("SLA breach detection background task started")