import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Twilio
# ---------------------------------------------------------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost:8003")

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3.5:latest")

PRIMARY_LLM = os.getenv("PRIMARY_LLM", "auto")  # "auto", "ollama", "groq"

# ---------------------------------------------------------------------------
# TTS Configuration
# ---------------------------------------------------------------------------
PIPER_BINARY = os.getenv("PIPER_BINARY", "piper")
PIPER_VOICES_DIR = os.getenv("PIPER_VOICES_DIR", os.path.join(os.path.dirname(__file__), "..", "piper", "voices"))
TTS_VOICE = os.getenv("TTS_VOICE", "en-IN")
PRIMARY_TTS = os.getenv("PRIMARY_TTS", "auto")  # "auto", "piper", "edge_tts"

EDGE_TTS_VOICE_MAP = {
    "en-IN": "en-IN-NeerjaNeural",
    "hi-IN": "hi-IN-SwaraNeural",
}

Piper_VOICE_FILES = {
    "en-IN": "en_US-lessac-medium.onnx",   # Indian English fallback: US English Lessac voice
    "hi-IN": "en_US-lessac-medium.onnx",   # Hindi fallback: same (no Hindi Piper model available)
}

# ---------------------------------------------------------------------------
# Service URLs
# ---------------------------------------------------------------------------
STT_SERVICE_URL = os.getenv("STT_SERVICE_URL", "http://localhost:8001")
CLASSIFIER_SERVICE_URL = os.getenv("CLASSIFIER_SERVICE_URL", "http://localhost:8002")
BACKEND_SERVICE_URL = os.getenv("BACKEND_SERVICE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Backend Auth
# ---------------------------------------------------------------------------
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL", "system@lakshya.ai")
SERVICE_ACCOUNT_PASSWORD = os.getenv("SERVICE_ACCOUNT_PASSWORD", "")

# ---------------------------------------------------------------------------
# Network Mode
# ---------------------------------------------------------------------------
NETWORK_MODE = os.getenv("NETWORK_MODE", "auto")  # "auto", "online", "offline"

# ---------------------------------------------------------------------------
# Audio Configuration
# ---------------------------------------------------------------------------
AUDIO_SAMPLE_RATE = 8000       # Twilio mu-law: 8kHz
INTERNAL_SAMPLE_RATE = 16000  # Whisper needs 16kHz

# ---------------------------------------------------------------------------
# Confidence Thresholds
# ---------------------------------------------------------------------------
STT_CONFIDENCE_THRESHOLD = float(os.getenv("STT_CONFIDENCE_THRESHOLD", "0.85"))
CLASSIFY_CONFIDENCE_THRESHOLD = float(os.getenv("CLASSIFY_CONFIDENCE_THRESHOLD", "0.70"))
DIALOG_CONFIDENCE_THRESHOLD = float(os.getenv("DIALOG_CONFIDENCE_THRESHOLD", "0.60"))

# ---------------------------------------------------------------------------
# Session Configuration
# ---------------------------------------------------------------------------
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT_SECONDS", "300"))
MAX_TURNS = int(os.getenv("MAX_TURNS", "4"))


_internet_cache: dict = {"available": None, "checked_at": 0.0}


async def is_internet_available() -> bool:
    if NETWORK_MODE == "offline":
        return False
    if NETWORK_MODE == "online":
        return True

    import time
    now = time.time()
    if _internet_cache["checked_at"] + 30 > now and _internet_cache["available"] is not None:
        return _internet_cache["available"]

    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{GROQ_BASE_URL}/models")
            _internet_cache["available"] = response.status_code == 200
    except Exception:
        _internet_cache["available"] = False
    _internet_cache["checked_at"] = now
    return _internet_cache["available"]