"""
config.py — Centralized configuration for the GenAI Resolution Microservice.
Loads settings from genai/.env and environment variables.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


def _load_env() -> None:
    """Load key=value pairs from .env into os.environ (no overwrite)."""
    if not ENV_PATH.exists():
        return
    for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()


class Config:
    # --- LLM (Groq Llama 3.3 70B — winner from ablation study) ---
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.25"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # --- NLP Classifier upstream ---
    NLP_SERVICE_URL: str = os.getenv("NLP_SERVICE_URL", "http://localhost:8000")

    # --- Service ---
    HOST: str = os.getenv("GENAI_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("GENAI_PORT", "8001"))
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # --- Security ---
    API_KEY: str = os.getenv("GENAI_API_KEY", "")  # optional bearer token
    RATE_LIMIT_RPM: int = int(os.getenv("RATE_LIMIT_RPM", "60"))
    MAX_COMPLAINT_LENGTH: int = int(os.getenv("MAX_COMPLAINT_LENGTH", "2000"))

    # --- Observability (LangSmith) ---
    LANGCHAIN_TRACING: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "genai-resolution-service")
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

    # --- SLA defaults (hours) ---
    SLA_HIGH: int = 4
    SLA_MEDIUM: int = 24
    SLA_LOW: int = 72

    # --- Reply email HTML output ---
    REPLY_EMAIL_OUTPUT_DIR: str = os.getenv("REPLY_EMAIL_OUTPUT_DIR", "generated_emails")


config = Config()
