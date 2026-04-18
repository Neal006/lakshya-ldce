import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"


class Config:
    WHISPER_TINY_PATH = os.getenv("WHISPER_TINY_PATH", str(MODELS_DIR / "whisper_tiny_int8.onnx"))
    VAD_MODEL_PATH = os.getenv("VAD_MODEL_PATH", str(MODELS_DIR / "silero_vad.onnx"))

    SAMPLE_RATE = 16000
    CHUNK_WINDOW_SEC = 4.0
    CHUNK_OVERLAP_SEC = 0.45

    MAX_AUDIO_DURATION_SEC = 120
    MIN_AUDIO_DURATION_SEC = 0.1

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    WS_MAX_MESSAGE_SIZE = int(os.getenv("WS_MAX_MESSAGE_SIZE", "1048576"))  # 1MB
    WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "20"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
