"""
main.py — FastAPI server for the GenAI Resolution Microservice.

Endpoints:
    GET  /health              → Service health check
    POST /resolve             → Generate resolution from classifier output
    POST /reply/email-html    → Generate solv.ai branded HTML for a customer reply email
    GET  /metrics             → Prometheus metrics

Start with:
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload
"""

import time
import logging
import uuid
from collections import defaultdict
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import config
from llm import LLMClient
from models import (
    ClassifierOutput,
    ResolveRequest,
    ResolutionResponse,
    HealthResponse,
    ComplaintStatus,
    EmailReplyHtmlRequest,
    EmailReplyHtmlResponse,
)
from prompts import SYSTEM_PROMPT_RESOLVE, USER_PROMPT_RESOLVE
from guardrails import (
    sanitize_text,
    validate_input,
    validate_output,
    safe_json_parse,
    check_prompt_injection,
)
from email_html import build_solvai_reply_html_from_resolution, write_reply_html_file

# ─── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("genai")

_GENAI_ROOT = Path(__file__).resolve().parent

# ─── Rate Limiter (in-memory, per-IP) ────────────────────────────────

_rate_store: dict[str, list[float]] = defaultdict(list)


def _reply_email_output_dir() -> Path:
    p = Path(config.REPLY_EMAIL_OUTPUT_DIR)
    return p.resolve() if p.is_absolute() else (_GENAI_ROOT / p).resolve()


def _check_rate_limit(client_ip: str) -> bool:
    """Simple sliding-window rate limiter. Returns True if allowed."""
    now = time.time()
    window = 60.0  # 1 minute
    max_requests = config.RATE_LIMIT_RPM

    # Prune old entries
    _rate_store[client_ip] = [
        ts for ts in _rate_store[client_ip] if now - ts < window
    ]

    if len(_rate_store[client_ip]) >= max_requests:
        return False

    _rate_store[client_ip].append(now)
    return True


# ─── SLA Mapping ────────────────────────────────────────────────────

SLA_MAP = {
    "High": config.SLA_HIGH,
    "Medium": config.SLA_MEDIUM,
    "Low": config.SLA_LOW,
}

# ─── App Lifespan ───────────────────────────────────────────────────

llm_client: LLMClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_client
    logger.info("Initializing GenAI Resolution Microservice...")
    logger.info(f"LLM Model: {config.LLM_MODEL}")
    logger.info(f"LLM Base URL: {config.LLM_BASE_URL}")

    llm_client = LLMClient(
        api_key=config.LLM_API_KEY,
        base_url=config.LLM_BASE_URL,
        model=config.LLM_MODEL,
    )
    logger.info("GenAI Resolution Microservice ready.")
    yield
    logger.info("Shutting down GenAI Resolution Microservice.")


# ─── FastAPI App ────────────────────────────────────────────────────

app = FastAPI(
    title="SOLV.ai — GenAI Complaint Resolution Service",
    description=(
        "AI-powered resolution recommendation engine for customer complaints. "
        "Consumes classified complaints from the NLP text_classifier and generates "
        "empathetic, actionable resolution plans using Groq Llama 3.3 70B."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Security: API Key Auth (optional) ──────────────────────────────

async def verify_api_key(request: Request):
    """Optional Bearer token authentication."""
    if not config.API_KEY:
        return  # no auth configured
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth[7:]
    if token != config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


# ─── Middleware: Rate Limiting ──────────────────────────────────────

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "message": f"Rate limit exceeded. Max {config.RATE_LIMIT_RPM} requests/minute.",
                "retry_after_seconds": 60,
            },
        )
    return await call_next(request)


# ─── Endpoints ──────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — returns service status and LLM connectivity."""
    llm_ok = False
    if llm_client:
        try:
            llm_ok = llm_client.health_check()
        except Exception:
            llm_ok = False

    return HealthResponse(
        status="healthy" if llm_ok else "degraded",
        llm_connected=llm_ok,
        nlp_service_url=config.NLP_SERVICE_URL,
    )


@app.post("/resolve", response_model=ResolutionResponse, dependencies=[Depends(verify_api_key)])
async def resolve(request: ResolveRequest):
    """
    Generate an AI-powered resolution for a classified customer complaint.

    Accepts the output from the NLP text_classifier service and returns
    a structured resolution plan with an empathetic customer response.
    """
    if llm_client is None:
        raise HTTPException(status_code=503, detail="LLM client not initialized")

    start = time.time()
    data = request.classifier_output
    request_id = str(uuid.uuid4())[:8]

    # ─── Layer 1: Input Validation ──────────────────────────────
    sanitized_text = sanitize_text(data.text, config.MAX_COMPLAINT_LENGTH)
    input_dict = {
        "complaint_id": data.complaint_id,
        "text": sanitized_text,
        "category": data.category.value,
        "priority": data.priority.value,
        "sentiment_score": data.sentiment_score,
    }

    violations = validate_input(input_dict)
    if violations:
        logger.warning(f"[{request_id}] Input validation failed: {violations}")
        raise HTTPException(
            status_code=400,
            detail={"error": "input_validation_failed", "violations": violations},
        )

    # ─── Layer 2: Build Prompt ──────────────────────────────────
    user_prompt = USER_PROMPT_RESOLVE.format(
        complaint_id=data.complaint_id,
        customer_name=request.customer_name,
        channel=request.channel,
        product_name=request.product_name,
        category=data.category.value,
        priority=data.priority.value,
        sentiment_score=data.sentiment_score,
        complaint_text=sanitized_text,
    )

    # ─── Layer 3: Call LLM ──────────────────────────────────────
    try:
        raw_output = llm_client.generate(
            system_prompt=SYSTEM_PROMPT_RESOLVE,
            user_prompt=user_prompt,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )
    except Exception as e:
        logger.error(f"[{request_id}] LLM call failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": "llm_unavailable", "message": "AI service temporarily unavailable. Please retry."},
        )

    # ─── Layer 4: Parse + Validate Output ───────────────────────
    parsed = safe_json_parse(raw_output)
    if parsed is None:
        logger.error(f"[{request_id}] LLM output not valid JSON: {raw_output[:200]}")
        raise HTTPException(
            status_code=502,
            detail={"error": "llm_output_parse_error", "message": "AI response was malformed. Please retry."},
        )

    output_violations = validate_output(parsed, input_dict)
    if output_violations:
        logger.warning(f"[{request_id}] Output validation issues: {output_violations}")
        # Fix critical issues rather than failing
        if data.priority.value == "High":
            parsed["escalation_required"] = True

    # ─── Layer 5: Build Response ────────────────────────────────
    latency_ms = round((time.time() - start) * 1000, 2)

    return ResolutionResponse(
        complaint_id=data.complaint_id,
        original_text=data.text,
        category=data.category.value,
        priority=data.priority.value,
        sentiment_score=data.sentiment_score,
        customer_response=parsed.get("customer_response", ""),
        immediate_action=parsed.get("immediate_action", ""),
        resolution_steps=parsed.get("resolution_steps", []),
        assigned_team=parsed.get("assigned_team", "Customer Support"),
        escalation_required=parsed.get("escalation_required", data.priority.value == "High"),
        follow_up_required=parsed.get("follow_up_required", True),
        follow_up_timeline=parsed.get("follow_up_timeline", "24 hours"),
        estimated_resolution_time=parsed.get("estimated_resolution_time", f"{SLA_MAP.get(data.priority.value, 72)} hours"),
        root_cause_hypothesis=parsed.get("root_cause_hypothesis", ""),
        sla_deadline_hours=SLA_MAP.get(data.priority.value, 72),
        status=ComplaintStatus.ESCALATED if parsed.get("escalation_required") else ComplaintStatus.OPEN,
        confidence=parsed.get("confidence", "medium"),
        model_used=config.LLM_MODEL,
        genai_latency_ms=latency_ms,
    )


@app.post("/resolve/quick", dependencies=[Depends(verify_api_key)])
async def resolve_quick(data: ClassifierOutput):
    """
    Shorthand endpoint — accepts raw classifier output directly (no wrapper).
    Uses defaults for customer_name, channel, product_name.
    """
    request = ResolveRequest(classifier_output=data)
    return await resolve(request)


@app.post("/reply/email-html", response_model=EmailReplyHtmlResponse, dependencies=[Depends(verify_api_key)])
async def reply_email_html(body: EmailReplyHtmlRequest):
    """
    Turn the JSON from **POST /resolve** into a black & orange solv.ai HTML email document.
    No extra LLM call — the email content comes from `resolution` (e.g. `customer_response`, steps, SLA).
    Optional `customer_name` fills the greeting (same field you use on `/resolve`).
    """
    start = time.time()
    request_id = str(uuid.uuid4())[:8]
    r = body.resolution

    for label, text in (
        ("original_text", r.original_text),
        ("customer_response", r.customer_response),
    ):
        if len((text or "").strip()) < 3:
            raise HTTPException(status_code=400, detail=f"resolution.{label} is missing or too short")

    inj: list[str] = []
    for text in (r.original_text, r.customer_response):
        inj.extend(check_prompt_injection(text))
    if inj:
        logger.warning(f"[{request_id}] Email HTML request blocked: {inj}")
        raise HTTPException(
            status_code=400,
            detail={"error": "input_validation_failed", "violations": inj},
        )

    subject = (body.subject or "").strip() or f"Re: Your request #{r.complaint_id} — {r.category}"
    status_label = r.status.value if hasattr(r.status, "value") else str(r.status)

    html_doc = build_solvai_reply_html_from_resolution(
        subject=subject,
        customer_name=body.customer_name,
        complaint_id=r.complaint_id,
        category=r.category,
        priority=r.priority,
        status=status_label,
        original_text=r.original_text,
        customer_response=r.customer_response,
        resolution_steps=r.resolution_steps,
        follow_up_timeline=r.follow_up_timeline,
        estimated_resolution_time=r.estimated_resolution_time,
        assigned_team=r.assigned_team,
        escalation_required=r.escalation_required,
        sla_deadline_hours=r.sla_deadline_hours,
    )

    file_path: str | None = None
    if body.persist_file:
        stem = f"reply_{r.complaint_id}_{request_id}_{int(time.time())}"
        path = write_reply_html_file(_reply_email_output_dir(), stem, html_doc)
        file_path = str(path)
        logger.info(f"[{request_id}] Wrote reply HTML: {file_path}")

    latency_ms = round((time.time() - start) * 1000, 2)
    return EmailReplyHtmlResponse(
        subject=subject,
        html=html_doc,
        file_path=file_path,
        model_used=r.model_used,
        genai_latency_ms=latency_ms,
    )
