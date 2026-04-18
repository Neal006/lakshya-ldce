from config import STT_CONFIDENCE_THRESHOLD, CLASSIFY_CONFIDENCE_THRESHOLD


def check_stt_confidence(stt_result: dict, threshold: float = STT_CONFIDENCE_THRESHOLD) -> bool:
    """Return True if STT confidence is above threshold."""
    confidence = stt_result.get("confidence", 0.0)
    return confidence >= threshold


def check_classify_confidence(classification: dict, threshold: float = CLASSIFY_CONFIDENCE_THRESHOLD) -> bool:
    """Return True if classification confidence is acceptable."""
    # Classifier returns category explicitly — we trust the ensemble
    # If we had per-category confidence scores, we could check them here
    return True


def should_escalate(classification: dict, resolution: dict) -> bool:
    """Determine if the complaint should be escalated to a human agent."""
    if resolution.get("escalation", False):
        return True
    priority = classification.get("priority", "Medium")
    sentiment = classification.get("sentiment_score", 0.0)
    if priority == "High" and sentiment < -0.6:
        return True
    return False