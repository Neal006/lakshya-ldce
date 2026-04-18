"""
models.py — Pydantic request/response contracts for the GenAI Resolution Microservice.
"""

from pydantic import BaseModel, Field
from enum import Enum


# ─── Enums ──────────────────────────────────────────────────────────

class Category(str, Enum):
    PRODUCT = "Product"
    PACKAGING = "Packaging"
    TRADE = "Trade"


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ComplaintStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    ESCALATED = "Escalated"
    RESOLVED = "Resolved"


# ─── Requests ───────────────────────────────────────────────────────

class ClassifierOutput(BaseModel):
    """Input from the NLP text_classifier service."""
    complaint_id: int | str
    text: str = Field(..., min_length=1, max_length=2000)
    category: Category
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    priority: Priority
    latency_ms: float = Field(default=0.0, ge=0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "complaint_id": 1,
                    "text": "Box was broken",
                    "category": "Packaging",
                    "sentiment_score": -0.4767,
                    "priority": "High",
                    "latency_ms": 206.8,
                }
            ]
        }
    }


class ResolveRequest(BaseModel):
    """Full resolution request — classifier output + optional metadata."""
    classifier_output: ClassifierOutput
    customer_name: str = Field(default="Valued Customer", max_length=200)
    channel: str = Field(default="web", max_length=50)
    product_name: str = Field(default="Wellness Product", max_length=200)


# ─── Responses ──────────────────────────────────────────────────────

class ResolutionResponse(BaseModel):
    complaint_id: int | str
    original_text: str
    category: str
    priority: str
    sentiment_score: float

    # LLM-generated resolution
    customer_response: str = Field(..., description="Apologetic, empathetic customer-facing message")
    immediate_action: str = Field(..., description="What support executive must do within 15 minutes")
    resolution_steps: list[str] = Field(..., description="Ordered role-tagged action steps")
    assigned_team: str
    escalation_required: bool
    follow_up_required: bool
    follow_up_timeline: str
    estimated_resolution_time: str
    root_cause_hypothesis: str

    # SLA + metadata
    sla_deadline_hours: int
    status: ComplaintStatus = ComplaintStatus.OPEN
    confidence: str = "high"
    model_used: str = ""
    genai_latency_ms: float = 0.0


class HealthResponse(BaseModel):
    status: str
    llm_connected: bool
    nlp_service_url: str
    version: str = "1.0.0"
