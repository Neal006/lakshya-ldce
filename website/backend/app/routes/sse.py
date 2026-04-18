import asyncio
import json
from datetime import datetime, timezone
from typing import Set
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse
from app.middleware.auth import get_current_user
from app.services.auth import decode_token
from app.database import SessionLocal
from app.models.models import Profile

router = APIRouter()

_connections: Set[asyncio.Queue] = []


class SSEManager:
    def __init__(self):
        self.connections: Set[asyncio.Queue] = set()

    def add(self, queue: asyncio.Queue):
        self.connections.add(queue)

    def remove(self, queue: asyncio.Queue):
        self.connections.discard(queue)

    async def broadcast(self, event: str, data: dict):
        payload = json.dumps(data, default=str)
        dead = set()
        for queue in self.connections:
            try:
                queue.put_nowait({"event": event, "data": payload})
            except asyncio.QueueFull:
                dead.add(queue)
        for q in dead:
            self.connections.discard(q)


sse_manager = SSEManager()


async def event_generator(queue: asyncio.Queue, user_id: str):
    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield message
            except asyncio.TimeoutError:
                yield {
                    "event": "ping",
                    "data": json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }),
                }
    except asyncio.CancelledError:
        pass
    finally:
        sse_manager.remove(queue)


@router.get("/stream")
async def complaint_stream(token: str = Query(..., description="JWT access token")):
    try:
        payload = decode_token(token, token_type="access")
        user_id = payload.get("sub")
        if not user_id:
            return EventSourceResponse(iter([]))
        db = SessionLocal()
        user = db.query(Profile).filter(Profile.id == user_id, Profile.is_active == True).first()
        db.close()
        if not user:
            return EventSourceResponse(iter([]))
    except Exception:
        return EventSourceResponse(iter([]))

    queue = asyncio.Queue(maxsize=100)
    sse_manager.add(queue)

    return EventSourceResponse(event_generator(queue, user_id))