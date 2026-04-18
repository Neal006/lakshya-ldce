import httpx
import json
from app.config import ML_SERVICE_URL


async def classify_complaint(raw_text: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/predict",
                json={"complaint_id": "voice", "text": raw_text},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "category": data.get("category", "Product"),
                "priority": data.get("priority", "Medium"),
                "sentiment_score": data.get("sentiment_score", 0.0),
                "resolution_steps": data.get("resolution_steps", []),
            }
    except (httpx.HTTPError, httpx.TimeoutException, json.JSONDecodeError):
        return _fallback_classification(raw_text)


def _fallback_classification(raw_text: str) -> dict:
    text = raw_text.lower()
    category = "Product"
    if any(word in text for word in ["packaging", "box", "wrap", "damaged box", "broken seal"]):
        category = "Packaging"
    elif any(word in text for word in ["trade", "order", "delivery", "shipping", "bulk", "price"]):
        category = "Trade"

    sentiment_score = 0.0
    negative_words = ["angry", "terrible", "worst", "horrible", "furious", "unacceptable", "broken", "stopped working"]
    positive_words = ["great", "good", "excellent", "happy", "satisfied", "fine", "okay"]
    neg_count = sum(1 for w in negative_words if w in text)
    pos_count = sum(1 for w in positive_words if w in text)
    if neg_count > pos_count:
        sentiment_score = -0.5 - (0.1 * neg_count)
    elif pos_count > neg_count:
        sentiment_score = 0.3 + (0.1 * pos_count)

    priority = "Medium"
    if sentiment_score < -0.6 or any(w in text for w in ["urgent", "asap", "immediately", "legal", "safety"]):
        priority = "High"
    elif sentiment_score > 0.3 and not any(w in text for w in ["issue", "problem", "wrong", "error"]):
        priority = "Low"

    resolution_steps = _generate_resolution_steps(category, priority)

    return {
        "category": category,
        "priority": priority,
        "sentiment_score": sentiment_score,
        "resolution_steps": resolution_steps,
    }


def _generate_resolution_steps(category: str, priority: str) -> list[str]:
    steps_map = {
        "Product": [
            "1. Verify product warranty status",
            "2. Check for common troubleshooting steps",
            "3. Initiate replacement if under warranty",
            "4. Schedule pickup for defective unit",
        ],
        "Packaging": [
            "1. Document packaging damage with photos",
            "2. Verify shipping carrier and tracking info",
            "3. Arrange replacement shipment",
            "4. File carrier damage claim if applicable",
        ],
        "Trade": [
            "1. Verify order details and customer account",
            "2. Check inventory and fulfillment status",
            "3. Coordinate with logistics for delivery update",
            "4. Provide resolution timeline to customer",
        ],
    }
    return steps_map.get(category, steps_map["Product"])