"""
Configuration for the TS-14 ablation study.
AI-Powered Complaint Classification & Resolution Recommendation Engine.
All models accessed via OpenCode / OpenRouter unified OpenAI-compatible API.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parent
GENAI_DIR   = BASE_DIR.parent
RESULTS_DIR = BASE_DIR / "results"
GRAPHS_DIR  = BASE_DIR / "graphs"


def _load_local_env() -> None:
    """
    Load key/value pairs from genai/.env into process environment.
    Existing environment variables are not overwritten.
    """
    env_path = GENAI_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()

# ---------------------------------------------------------------------------
# API Keys (set one of these in your environment)
# ---------------------------------------------------------------------------
OPENCODE_API_KEY = (
    os.getenv("OPENCODE_API_KEY")
    or os.getenv("OPENCODE_GO_API_KEY")
    or os.getenv("OPENROUTER_API_KEY")
)
GROQ_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

OPENCODE_BASE_URL = (
    os.getenv("OPENCODE_BASE_URL")
    or os.getenv("OPENCODE_GO_BASE_URL")
    or os.getenv("OPENROUTER_BASE_URL")
    or "https://opencode.ai/zen/go/v1"
)

OPENCODE_MODEL_PREFIX = os.getenv("OPENCODE_MODEL_PREFIX", "")

# ---------------------------------------------------------------------------
# Model definitions
# All accessed via OpenCode / OpenRouter for a unified OpenAI-compatible API.
# ---------------------------------------------------------------------------
MODELS = {
    "groq_llama70b": {
        "provider":     "groq",
        "model_id":     "llama-3.3-70b-versatile",
        "display_name": "Llama 3.3 70B (Groq)",
        "api_key":      GROQ_API_KEY,
        "base_url":     "https://api.groq.com/openai/v1",
        "endpoint":     "/chat/completions",
    },
    "gemini_2_5_flash": {
        "provider":     "google",
        "model_id":     "models/gemini-2.5-flash",
        "display_name": "Gemini 2.5 Flash (Google)",
        "api_key":      GOOGLE_API_KEY,
        "base_url":     None,
    },
    "hf_qwen_72b": {
        "provider":     "huggingface",
        "model_id":     "Qwen/Qwen2.5-72B-Instruct",
        "display_name": "Qwen 2.5 72B (HuggingFace)",
        "api_key":      HUGGINGFACE_API_KEY,
        "base_url":     None,
    },
    "glm_5": {
        "provider":     "openrouter",
        "model_id":     "glm-5",
        "display_name": "GLM 5 (Zhipu)",
        "api_key":      OPENCODE_API_KEY,
        "base_url":     OPENCODE_BASE_URL,
        "endpoint":     "/chat/completions",
    },
    "glm_5_1": {
        "provider":     "openrouter",
        "model_id":     "glm-5.1",
        "display_name": "GLM 5.1 (Zhipu)",
        "api_key":      OPENCODE_API_KEY,
        "base_url":     OPENCODE_BASE_URL,
        "endpoint":     "/chat/completions",
    },
    "mimo_v2_omni": {
        "provider":     "openrouter",
        "model_id":     "mimo-v2-omni",
        "display_name": "MiMo V2 Omni (Xiaomi)",
        "api_key":      OPENCODE_API_KEY,
        "base_url":     OPENCODE_BASE_URL,
        "endpoint":     "/chat/completions",
    },
    "mimo_v2_pro": {
        "provider":     "openrouter",
        "model_id":     "mimo-v2-pro",
        "display_name": "MiMo V2 Pro (Xiaomi)",
        "api_key":      OPENCODE_API_KEY,
        "base_url":     OPENCODE_BASE_URL,
        "endpoint":     "/chat/completions",
    },
    "minimax_m2_5": {
        "provider":     "openrouter",
        "model_id":     "minimax-m2.5",
        "display_name": "MiniMax M2.5",
        "api_key":      OPENCODE_API_KEY,
        "base_url":     OPENCODE_BASE_URL,
        "endpoint":     "/messages",
    },
    "minimax_m2_7": {
        "provider":     "openrouter",
        "model_id":     "minimax-m2.7",
        "display_name": "MiniMax M2.7",
        "api_key":      OPENCODE_API_KEY,
        "base_url":     OPENCODE_BASE_URL,
        "endpoint":     "/messages",
    },
    "qwen3_5_plus": {
        "provider":     "openrouter",
        "model_id":     "qwen3.5-plus",
        "display_name": "Qwen 3.5 Plus (Alibaba)",
        "api_key":      OPENCODE_API_KEY,
        "base_url":     OPENCODE_BASE_URL,
        "endpoint":     "/chat/completions",
    },
}

# ---------------------------------------------------------------------------
# Evaluation settings
# ---------------------------------------------------------------------------
TEMPERATURE        = 0.3
MAX_TOKENS         = 2048
RETRY_ATTEMPTS     = 2

RETRY_DELAY_SECONDS = 5
