import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessedResult:
    text: str
    confidence: float
    latency_ms: float


class PostProcessor:
    def __init__(self):
        self.filler_words = {
            "um", "uh", "uhh", "umm", "er", "ah",
        }

    def process(self, text: str, confidence: float, latency_ms: float) -> ProcessedResult:
        text = self._restore_punctuation(text)
        text = self._apply_casing(text)
        text = self._remove_fillers(text)
        text = self._normalize_numbers(text)
        text = self._clean_whitespace(text)

        return ProcessedResult(
            text=text,
            confidence=round(confidence, 4),
            latency_ms=round(latency_ms, 2),
        )

    def _restore_punctuation(self, text: str) -> str:
        if not text:
            return text

        text = text.strip()

        if not re.search(r'[.!?]$', text):
            if text.lower().startswith(('what', 'who', 'where', 'when', 'why', 'how', 'is', 'are', 'do', 'does', 'can', 'could', 'would', 'should')):
                text += '.'
            else:
                text += '.'

        return text

    def _apply_casing(self, text: str) -> str:
        sentences = re.split(r'([.!?]\s*)', text)
        result = []
        for part in sentences:
            if part.strip():
                result.append(part[0].upper() + part[1:] if len(part) > 1 else part.upper())
            else:
                result.append(part)
        return ''.join(result)

    def _remove_fillers(self, text: str) -> str:
        words = text.split()
        filtered = [w for w in words if w.lower().rstrip('.,!?') not in self.filler_words]
        return ' '.join(filtered)

    def _normalize_numbers(self, text: str) -> str:
        number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20',
        }

        pattern = re.compile(r'\b(' + '|'.join(number_words.keys()) + r')\b', re.IGNORECASE)
        return pattern.sub(lambda m: number_words[m.group().lower()], text)

    def _clean_whitespace(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
