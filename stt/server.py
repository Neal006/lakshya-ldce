"""
server.py — FastAPI inference server for Speech-to-Text.

Endpoints:
    GET  /health          → Server health check
    POST /transcribe      → Transcribe audio file (wav/mp3/ogg/flac)
    POST /transcribe/raw  → Transcribe raw PCM16 audio
    WS   /ws/transcribe   → Streaming transcription
    GET  /metrics         → Prometheus metrics

Start with:
    python run_server.py
    # or
    uvicorn server:app --host 0.0.0.0 --port 8000
"""

import contextlib
import time

import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel

from inference_engine import SAMPLE_RATE, STTEngine, StreamingChunker

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

stt_transcribe_requests_total = Counter(
    "stt_transcribe_requests_total",
    "Total transcription requests",
    ["endpoint", "status"],
)
stt_transcribe_latency_ms = Histogram(
    "stt_transcribe_latency_ms",
    "Transcription latency in milliseconds",
    ["endpoint"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TranscribeResponse(BaseModel):
    text: str
    confidence: float
    latency_ms: float
    model_used: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    vad_loaded: bool
    sample_rate: int

# ---------------------------------------------------------------------------
# App + lifespan
# ---------------------------------------------------------------------------

engine: STTEngine | None = None

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = STTEngine()
    print(f"STT Engine ready — device={engine.device}")
    yield
    engine = None
    print("STT Engine shut down.")

app = FastAPI(title="STT Inference Server", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=engine is not None,
        device=engine.device if engine else "N/A",
        vad_loaded=engine._vad is not None if engine else False,
        sample_rate=SAMPLE_RATE,
    )

@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    fmt: str = Form("wav"),
):
    t0 = time.perf_counter()
    try:
        audio_bytes = await file.read()
        result = engine.transcribe(audio_bytes, fmt=fmt)
        stt_transcribe_requests_total.labels(endpoint="transcribe", status="ok").inc()
    except Exception as exc:
        stt_transcribe_requests_total.labels(endpoint="transcribe", status="error").inc()
        raise
    finally:
        elapsed = (time.perf_counter() - t0) * 1000
        stt_transcribe_latency_ms.labels(endpoint="transcribe").observe(elapsed)
    return TranscribeResponse(**result.to_dict())

@app.post("/transcribe/raw", response_model=TranscribeResponse)
async def transcribe_raw(
    file: UploadFile = File(...),
    sample_rate: int = Form(SAMPLE_RATE),
):
    t0 = time.perf_counter()
    try:
        raw = await file.read()
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        result = engine.transcribe_raw(audio, sample_rate=sample_rate)
        stt_transcribe_requests_total.labels(endpoint="raw", status="ok").inc()
    except Exception:
        stt_transcribe_requests_total.labels(endpoint="raw", status="error").inc()
        raise
    finally:
        elapsed = (time.perf_counter() - t0) * 1000
        stt_transcribe_latency_ms.labels(endpoint="raw").observe(elapsed)
    return TranscribeResponse(**result.to_dict())

@app.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket):
    await websocket.accept()
    chunker = StreamingChunker()
    try:
        while True:
            data = await websocket.receive_bytes()
            audio = STTEngine.decode_pcm16(data)
            chunks = chunker.add(audio)
            for chunk in chunks:
                result = engine.transcribe_chunk(chunk)
                await websocket.send_json({
                    "text": result.text,
                    "confidence": result.confidence,
                    "latency_ms": result.latency_ms,
                    "model_used": result.model_used,
                    "is_final": False,
                })
    except WebSocketDisconnect:
        remaining = chunker.flush()
        if remaining is not None and len(remaining) > 0:
            result = engine.transcribe_chunk(remaining)
            await websocket.send_json({
                "text": result.text,
                "confidence": result.confidence,
                "latency_ms": result.latency_ms,
                "model_used": result.model_used,
                "is_final": True,
            })
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

@app.get("/metrics")
async def metrics():
    content = generate_latest()
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")
