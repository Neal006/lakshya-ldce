from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import ML_SERVICE_URL, ENVIRONMENT
import httpx

router = APIRouter()

VERSION = "1.0.0"


@router.get("")
async def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    ml_status = "connected"

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ML_SERVICE_URL}/health")
            if response.status_code != 200:
                ml_status = "unavailable"
    except Exception:
        ml_status = "unavailable"

    return {
        "data": {
            "status": "healthy" if db_status == "connected" else "degraded",
            "version": VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": db_status,
                "ml_service": ml_status,
            },
        }
    }