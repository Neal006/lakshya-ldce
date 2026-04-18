import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    text: str
    confidence: float
    latency_ms: float
    model_used: str

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "model_used": self.model_used,
        }

    def to_streaming_dict(self, is_final: bool = False) -> dict:
        d = self.to_dict()
        d["is_final"] = is_final
        return d


class ResponseFormatter:
    def __init__(self, model_name: str = "whisper-tiny"):
        self.model_name = model_name

    def format(self, text: str, confidence: float, latency_ms: float) -> APIResponse:
        return APIResponse(
            text=text,
            confidence=confidence,
            latency_ms=latency_ms,
            model_used=self.model_name,
        )
