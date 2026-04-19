"""
GenAI Microservice client — calls the genai /resolve/quick endpoint
instead of making direct LLM calls for resolution generation.
"""

import httpx
import time
import logging
from config import GENAI_SERVICE_URL
from agents.http_pool import get_client

logger = logging.getLogger(__name__)


async def call_genai_resolve(
    text: str,
    category: str,
    priority: str,
    sentiment_score: float,
    customer_name: str = "Voice Caller",
    complaint_id: str = "voice",
) -> dict | None:
    """
    Call the GenAI microservice /resolve/quick endpoint.
    Returns the full resolution response dict, or None on failure.
    """
    payload = {
        "complaint_id": complaint_id,
        "text": text[:2000],
        "category": category,
        "sentiment_score": max(-1.0, min(1.0, sentiment_score)),
        "priority": priority,
        "latency_ms": 0.0,
    }

    start = time.time()
    try:
        client = get_client()
        response = await client.post(
            f"{GENAI_SERVICE_URL}/resolve/quick",
            json=payload,
            timeout=20.0,
        )
        response.raise_for_status()
        result = response.json()
        elapsed = round((time.time() - start) * 1000, 1)
        logger.info(f"GenAI /resolve/quick OK in {elapsed}ms | category={category} priority={priority}")
        return result
    except httpx.TimeoutException:
        logger.error(f"GenAI service timeout after {round((time.time() - start)*1000)}ms")
    except httpx.HTTPStatusError as e:
        logger.error(f"GenAI HTTP {e.response.status_code}: {e.response.text[:300]}")
    except httpx.ConnectError:
        logger.error(f"GenAI service unreachable at {GENAI_SERVICE_URL}")
    except Exception as e:
        logger.error(f"GenAI client error: {e}")

    return None


async def check_genai_health() -> bool:
    """Quick health check for the GenAI service."""
    try:
        client = get_client()
        r = await client.get(f"{GENAI_SERVICE_URL}/health", timeout=5.0)
        data = r.json()
        return data.get("status") == "healthy"
    except Exception:
        return False
