import os
import sys
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, generate_latest

from config import (
    STT_SERVICE_URL, CLASSIFIER_SERVICE_URL, BACKEND_SERVICE_URL,
    OLLAMA_BASE_URL, PRIMARY_LLM, PRIMARY_TTS, NETWORK_MODE, GENAI_SERVICE_URL,
)

# ---------------------------------------------------------------------------
# Logging Setup — console + file for debugging
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Console handler (INFO+)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
root_logger.addHandler(console_handler)

# File handler — full debug log
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "orchestrator.log"), encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
root_logger.addHandler(file_handler)

# Error-only file
error_handler = logging.FileHandler(os.path.join(LOG_DIR, "errors.log"), encoding="utf-8")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
root_logger.addHandler(error_handler)

# Quiet noisy third-party loggers
for noisy in ("httpx", "httpcore", "uvicorn.access", "websockets"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger("orchestrator")

REQUEST_COUNT = Counter("orchestrator_requests_total", "Total requests", ["endpoint", "status"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  Lakshya Voice Orchestrator — Starting")
    logger.info("=" * 60)
    logger.info(f"  STT:             {STT_SERVICE_URL}")
    logger.info(f"  Classifier:      {CLASSIFIER_SERVICE_URL}")
    logger.info(f"  Backend:         {BACKEND_SERVICE_URL}")
    logger.info(f"  GenAI:           {GENAI_SERVICE_URL}")
    logger.info(f"  LLM (dialog):    {PRIMARY_LLM}")
    logger.info(f"  TTS:             {PRIMARY_TTS}")
    logger.info(f"  Network:         {NETWORK_MODE}")
    logger.info(f"  Logs:            {LOG_DIR}")
    logger.info("=" * 60)
    yield
    logger.info("Orchestrator shutting down.")


app = FastAPI(
    title="Lakshya Voice Orchestrator",
    description="AI-Powered Voice Complaint Management - Orchestration Layer",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    checks = {}
    overall = "ok"

    import httpx
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{STT_SERVICE_URL}/health")
            checks["stt"] = {"status": "ok", "detail": r.json()}
        except Exception as e:
            checks["stt"] = {"status": "error", "detail": str(e)}
            overall = "degraded"

        try:
            r = await client.get(f"{CLASSIFIER_SERVICE_URL}/health")
            checks["classifier"] = {"status": "ok", "detail": r.json()}
        except Exception as e:
            checks["classifier"] = {"status": "error", "detail": str(e)}
            overall = "degraded"

        try:
            r = await client.get(f"{BACKEND_SERVICE_URL}/health")
            checks["backend"] = {"status": "ok", "detail": r.json() if r.status_code == 200 else r.text[:200]}
        except Exception as e:
            checks["backend"] = {"status": "error", "detail": str(e)}
            overall = "degraded"

        try:
            r = await client.get(f"{GENAI_SERVICE_URL}/health")
            data = r.json()
            checks["genai"] = {"status": "ok" if data.get("status") == "healthy" else "degraded", "detail": data}
        except Exception as e:
            checks["genai"] = {"status": "error", "detail": str(e)}
            overall = "degraded"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            checks["ollama"] = {"status": "ok" if r.status_code == 200 else "error"}
    except Exception:
        checks["ollama"] = {"status": "unavailable"}

    return {
        "status": overall,
        "timestamp": time.time(),
        "config": {
            "primary_llm": PRIMARY_LLM,
            "primary_tts": PRIMARY_TTS,
            "network_mode": NETWORK_MODE,
            "genai_url": GENAI_SERVICE_URL,
        },
        "services": checks,
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return generate_latest()


@app.post("/test/pipeline")
async def test_pipeline(request: Request):
    """
    Test endpoint: simulate a full pipeline call without telephony.
    Accepts JSON with 'text' field and runs through the full agent pipeline.
    """
    import json
    from pipeline.session import SessionManager, CallSession, SessionState
    from pipeline.coordinator import PipelineCoordinator

    body = await request.json()
    text = body.get("text", "")

    if not text:
        return JSONResponse({"error": "text field is required"}, status_code=400)

    manager = SessionManager()
    session = manager.create_session("test-call")
    session.state = SessionState.collecting
    session.transcript.append(text)

    coord = PipelineCoordinator()
    result = await coord.process_text(text, session)

    return {
        "call_sid": session.call_sid,
        "state": session.state.value,
        "extracted_data": session.extracted_data,
        "classification": session.classification,
        "resolution": session.resolution,
        "ticket_id": session.ticket_id,
        "pipeline_result": result,
    }


from telephony.twilio_handler import router as twilio_router
app.include_router(twilio_router, prefix="/twilio", tags=["Twilio Telephony"])
