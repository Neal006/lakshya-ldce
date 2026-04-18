import httpx
import json
import time
import logging
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL, OLLAMA_BASE_URL, OLLAMA_MODEL, PRIMARY_LLM, NETWORK_MODE
from agents.http_pool import get_client

logger = logging.getLogger(__name__)

_llm_status = {"groq_available": None, "last_check": 0.0}


async def is_groq_available() -> bool:
    if NETWORK_MODE == "offline":
        return False
    if not GROQ_API_KEY:
        return False
    now = time.time()
    if _llm_status["last_check"] + 60 > now and _llm_status["groq_available"] is not None:
        return _llm_status["groq_available"]
    try:
        client = get_client()
        r = await client.get(
            f"{GROQ_BASE_URL}/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=3.0,
        )
        _llm_status["groq_available"] = r.status_code == 200
    except Exception:
        _llm_status["groq_available"] = False
    _llm_status["last_check"] = now
    return _llm_status["groq_available"]


async def call_llm(system_prompt: str, user_prompt: str, json_mode: bool = True, max_tokens: int = 500) -> dict:
    """Call LLM with automatic routing: Groq (cloud) primary, Ollama (local) fallback."""
    if PRIMARY_LLM == "ollama" or not await is_groq_available():
        return await _call_ollama(system_prompt, user_prompt, json_mode, max_tokens)
    try:
        return await _call_groq(system_prompt, user_prompt, json_mode, max_tokens)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
        logger.warning(f"Groq failed, falling back to Ollama: {e}")
        return await _call_ollama(system_prompt, user_prompt, json_mode, max_tokens)


async def _call_groq(system_prompt: str, user_prompt: str, json_mode: bool, max_tokens: int) -> dict:
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    client = get_client()
    response = await client.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json=body,
        timeout=15.0,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content) if json_mode else {"text": content}


async def _call_ollama(system_prompt: str, user_prompt: str, json_mode: bool, max_tokens: int) -> dict:
    body = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": max_tokens},
    }
    if json_mode:
        body["format"] = "json"

    client = get_client()
    response = await client.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=body,
        timeout=30.0,
    )
    response.raise_for_status()
    content = response.json()["message"]["content"]
    return json.loads(content) if json_mode else {"text": content}
