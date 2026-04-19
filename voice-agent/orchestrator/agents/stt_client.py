import httpx
import numpy as np
import logging
from config import STT_SERVICE_URL
from agents.http_pool import get_client

logger = logging.getLogger(__name__)


async def transcribe_audio(audio: np.ndarray) -> dict | None:
    """Send audio to STT service and get transcript."""
    try:
        pcm_bytes = (audio * 32768.0).clip(-32768, 32767).astype(np.int16).tobytes()
        client = get_client()
        response = await client.post(
            f"{STT_SERVICE_URL}/transcribe/raw",
            files={"file": ("audio.raw", pcm_bytes, "application/octet-stream")},
            data={"sample_rate": "16000"},
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        logger.error("STT request timed out")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"STT HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"STT error: {e}")
        return None
