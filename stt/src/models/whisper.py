import logging
import time
import numpy as np
from dataclasses import dataclass

import whisper

logger = logging.getLogger(__name__)


@dataclass
class STTResult:
    text: str
    confidence: float
    latency_ms: float


class WhisperTiny:
    def __init__(self, model_path: str = None):
        logger.info("Loading Whisper-tiny model")
        self.model = whisper.load_model("tiny")
        logger.info("Whisper-tiny model loaded")

    def transcribe(self, audio: np.ndarray) -> STTResult:
        start = time.perf_counter()

        result = self.model.transcribe(
            audio,
            language="en",
            task="transcribe",
            fp16=False,
            verbose=False,
        )

        text = result.get("text", "").strip()
        confidence = self._extract_confidence(result)
        latency = (time.perf_counter() - start) * 1000

        return STTResult(text=text, confidence=confidence, latency_ms=latency)

    def _extract_confidence(self, result: dict) -> float:
        segments = result.get("segments", [])
        if not segments:
            return 0.0

        total_conf = 0.0
        total_count = 0
        for seg in segments:
            for word in seg.get("words", []):
                if "probability" in word:
                    total_conf += word["probability"]
                    total_count += 1

        if total_count == 0:
            return result.get("confidence", 0.8)

        return total_conf / total_count
