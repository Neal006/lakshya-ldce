import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST

from src.config import Config
from src.pipeline.orchestrator import STTPipeline, StreamingSTTPipeline
from src.api.websocket import websocket_endpoint

logger = logging.getLogger(__name__)

TRANSCRIBE_LATENCY = Histogram(
    "stt_transcribe_latency_ms", "Transcription latency in ms", buckets=[50, 100, 200, 500, 1000, 2000, 5000]
)
TRANSCRIBE_REQUESTS = Counter("stt_transcribe_requests_total", "Total transcription requests")
TRANSCRIBE_ERRORS = Counter("stt_transcribe_errors_total", "Total transcription errors")

pipeline: STTPipeline | None = None
streaming_pipeline: StreamingSTTPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, streaming_pipeline
    logger.info("Starting STT service...")
    pipeline = STTPipeline()
    streaming_pipeline = StreamingSTTPipeline(pipeline)
    logger.info("STT pipelines ready")
    yield
    logger.info("Shutting down STT service")


app = FastAPI(title="STT Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": "whisper-tiny",
        "sample_rate": Config.SAMPLE_RATE,
    }


@app.get("/metrics")
async def metrics():
    return generate_latest(), 200, {"content-type": CONTENT_TYPE_LATEST}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    format: str = Form(default="wav"),
):
    TRANSCRIBE_REQUESTS.inc()
    start = time.perf_counter()

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        result = pipeline.transcribe_bytes(content, format=format.lower())
        TRANSCRIBE_LATENCY.observe(result.latency_ms)
        return result.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        TRANSCRIBE_ERRORS.inc()
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Transcription failed")


@app.post("/transcribe/raw")
async def transcribe_raw(
    file: UploadFile = File(...),
    sample_rate: int = Form(default=16000),
):
    TRANSCRIBE_REQUESTS.inc()

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        import numpy as np
        samples = np.frombuffer(content, dtype=np.int16).astype(np.float32) / 32768.0

        if sample_rate != Config.SAMPLE_RATE:
            import librosa
            samples = librosa.resample(samples, orig_sr=sample_rate, target_sr=Config.SAMPLE_RATE)

        result = pipeline.transcribe_audio_array(samples)
        TRANSCRIBE_LATENCY.observe(result.latency_ms)
        return result.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        TRANSCRIBE_ERRORS.inc()
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Transcription failed")


@app.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket):
    websocket.app.state.pipeline = pipeline
    await websocket_endpoint(websocket)
