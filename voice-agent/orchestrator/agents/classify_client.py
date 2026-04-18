import httpx
import logging
from config import CLASSIFIER_SERVICE_URL
from agents.http_pool import get_client

logger = logging.getLogger(__name__)


async def classify_complaint(text: str) -> dict:
    """Call the classifier service at /predict."""
    try:
        client = get_client()
        response = await client.post(
            f"{CLASSIFIER_SERVICE_URL}/predict",
            json={"complaint_id": "voice", "text": text},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "category": data.get("category", "Product"),
            "priority": data.get("priority", "Medium"),
            "sentiment_score": data.get("sentiment_score", 0.0),
        }
    except httpx.TimeoutException:
        logger.error("Classifier request timed out")
    except httpx.HTTPStatusError as e:
        logger.error(f"Classifier HTTP error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Classification error: {e}")

    return {"category": "Product", "priority": "Medium", "sentiment_score": 0.0}
