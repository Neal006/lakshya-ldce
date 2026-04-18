import logging
from agents.llm_router import call_llm
from prompts.extraction import EXTRACTION_PROMPT
from prompts.corrections import apply_fmcg_corrections

logger = logging.getLogger(__name__)


async def extract_complaint(transcript: str) -> dict:
    """Extract structured complaint data from transcript using LLM."""
    corrected = apply_fmcg_corrections(transcript)
    prompt = EXTRACTION_PROMPT.format(transcript=corrected)

    try:
        result = await call_llm(
            system_prompt="You are a complaint extraction assistant for an FMCG company. Extract structured data from customer complaint text. Always respond in valid JSON.",
            user_prompt=prompt,
            json_mode=True,
            max_tokens=500,
        )

        result.setdefault("complaint_type", "Product")
        result.setdefault("description", corrected)
        result.setdefault("urgency_signal", "medium")
        result.setdefault("missing_fields", [])
        result.setdefault("customer_name", "")
        result.setdefault("customer_phone", "")
        result.setdefault("confidence", 0.8)
        return result

    except Exception as e:
        logger.error(f"Dialog extraction error: {e}")
        return {
            "complaint_type": "Product",
            "description": transcript,
            "urgency_signal": "medium",
            "missing_fields": ["description"],
            "confidence": 0.3,
            "customer_name": "",
            "customer_phone": "",
        }