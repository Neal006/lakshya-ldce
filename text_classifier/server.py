"""
server.py — FastAPI inference server for complaint classification.

Endpoints:
    GET  /health   → Server health check
    POST /predict  → Classify a single complaint (JSON input/output)
    GET  /metrics  → Prometheus metrics

Start with:
    python run_server.py
    # or
    uvicorn server:app --host 0.0.0.0 --port 8000
"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse

from inference_engine import InferenceEngine

# ─── Logging ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("server")

# ─── Prometheus Metrics ──────────────────────────────────────────

PREDICTION_COUNTER = Counter(
    "predictions_total",
    "Total prediction requests",
    ["status"],
)
LATENCY_HISTOGRAM = Histogram(
    "prediction_latency_seconds",
    "End-to-end prediction latency including network overhead",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# ─── Pydantic Schemas ───────────────────────────────────────────

class PredictRequest(BaseModel):
    complaint_id: int | str = Field(..., description="Unique complaint identifier")
    text: str = Field(..., min_length=1, max_length=1000, description="Complaint text")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"complaint_id": 1, "text": "Box was broken"}
            ]
        }
    }


class PredictResponse(BaseModel):
    complaint_id: int | str
    text: str
    category: str = Field(..., description="Predicted category: Trade, Product, or Packaging")
    sentiment_score: float = Field(..., description="VADER sentiment score in [-1, +1]")
    priority: str = Field(..., description="Predicted priority: High, Medium, or Low")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    gpu_provider: str


# ─── App ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    logger.info("Loading inference engine...")
    start = time.time()
    engine = InferenceEngine()
    elapsed = time.time() - start
    logger.info(f"Inference engine loaded in {elapsed:.1f}s")
    yield

app = FastAPI(
    title="SOLV.ai — Complaint Text Classifier API",
    description="Fastest possible inference server for complaint classification (ONNX + CUDA)",
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

engine: InferenceEngine | None = None


# ─── Endpoints ───────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check — returns server status and model info."""
    if engine is None:
        return HealthResponse(
            status="loading",
            model_loaded=False,
            gpu_provider="none",
        )

    # Check which provider is active
    providers = engine.zs_session.get_providers()
    gpu = "CUDA" if "CUDAExecutionProvider" in providers else "CPU"

    return HealthResponse(
        status="ok",
        model_loaded=True,
        gpu_provider=gpu,
    )


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Classify a single complaint.

    Input JSON:
    ```json
    {
        "complaint_id": 1,
        "text": "Box was broken"
    }
    ```

    Output JSON:
    ```json
    {
        "complaint_id": 1,
        "text": "Box was broken",
        "category": "Packaging",
        "sentiment_score": -0.4767,
        "priority": "High",
        "latency_ms": 12.34
    }
    ```
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="Models still loading")

    try:
        result = engine.predict(request.complaint_id, request.text)

        PREDICTION_COUNTER.labels(status="success").inc()
        LATENCY_HISTOGRAM.observe(result["latency_ms"] / 1000)

        return PredictResponse(**result)

    except Exception as e:
        PREDICTION_COUNTER.labels(status="error").inc()
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()
