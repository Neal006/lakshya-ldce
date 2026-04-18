import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, generate_latest
from fastapi.responses import PlainTextResponse

from config import (
    STT_SERVICE_URL, CLASSIFIER_SERVICE_URL, BACKEND_SERVICE_URL,
    OLLAMA_BASE_URL, PRIMARY_LLM, PRIMARY_TTS, NETWORK_MODE,
)

REQUEST_COUNT = Counter("orchestrator_requests_total", "Total requests", ["endpoint", "status"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("  Lakshya Voice Orchestrator")
    print("=" * 50)
    print(f"  STT:             {STT_SERVICE_URL}")
    print(f"  Classifier:      {CLASSIFIER_SERVICE_URL}")
    print(f"  Backend:         {BACKEND_SERVICE_URL}")
    print(f"  LLM:             {PRIMARY_LLM}")
    print(f"  TTS:             {PRIMARY_TTS}")
    print(f"  Network:         {NETWORK_MODE}")
    print("=" * 50)
    yield


app = FastAPI(
    title="Lakshya Voice Orchestrator",
    description="AI-Powered Voice Complaint Management - Orchestration Layer",
    version="1.0.0",
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

    coordinator = PipelineCoordinator()
    result = await coordinator.process_text(text, session)

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