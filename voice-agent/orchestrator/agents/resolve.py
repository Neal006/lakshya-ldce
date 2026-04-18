import logging
from agents.llm_router import call_llm
from prompts.resolution import RESOLUTION_PROMPT

logger = logging.getLogger(__name__)


async def generate_resolution(text: str, category: str, priority: str, sentiment: float) -> dict:
    """Generate resolution steps via LLM."""
    prompt = RESOLUTION_PROMPT.format(
        complaint=text,
        category=category,
        priority=priority,
        sentiment_score=sentiment,
    )

    try:
        result = await call_llm(
            system_prompt="You are a resolution agent for an FMCG complaint management system. Generate specific, actionable resolution steps. Always respond in valid JSON.",
            user_prompt=prompt,
            json_mode=True,
            max_tokens=400,
        )
        result.setdefault("steps", ["Investigate the complaint", "Contact customer for details", "Provide resolution"])
        result.setdefault("escalation", False)
        result.setdefault("estimated_resolution", "1-2 business days")
        return result

    except Exception as e:
        logger.error(f"Resolution error: {e}")
        return {
            "steps": ["Investigate the complaint", "Contact customer for details", "Provide resolution"],
            "escalation": False,
            "estimated_resolution": "1-2 business days",
        }