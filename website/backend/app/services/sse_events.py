import json
from datetime import datetime, timezone
from app.routes.sse import sse_manager


async def broadcast_new_complaint(complaint_id: str):
    await sse_manager.broadcast("complaint_update", {
        "type": "new_complaint",
        "complaint_id": complaint_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def broadcast_status_change(complaint_id: str, new_status: str):
    await sse_manager.broadcast("status_change", {
        "type": "status_changed",
        "complaint_id": complaint_id,
        "new_status": new_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def broadcast_sla_breach(complaint_id: str):
    await sse_manager.broadcast("sla_breach", {
        "type": "sla_breach",
        "complaint_id": complaint_id,
        "breach_time": datetime.now(timezone.utc).isoformat(),
    })