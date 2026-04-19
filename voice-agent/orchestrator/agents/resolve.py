"""
Resolution agent — uses the GenAI microservice for generating complaint resolutions.
Falls back to direct Groq LLM call if genai service is unreachable.
"""

import logging
from agents.genai_client import call_genai_resolve

logger = logging.getLogger(__name__)


async def generate_resolution(
    text: str,
    category: str,
    priority: str,
    sentiment: float,
    customer_name: str = "Voice Caller",
) -> dict:
    """Generate resolution via the GenAI microservice."""
    result = await call_genai_resolve(
        text=text,
        category=category,
        priority=priority,
        sentiment_score=sentiment,
        customer_name=customer_name,
    )

    if result:
        return {
            "customer_response": result.get("customer_response", ""),
            "steps": result.get("resolution_steps", []),
            "escalation": result.get("escalation_required", False),
            "estimated_resolution": result.get("estimated_resolution_time", "1-2 business days"),
            "immediate_action": result.get("immediate_action", ""),
            "assigned_team": result.get("assigned_team", "Customer Support"),
            "root_cause": result.get("root_cause_hypothesis", ""),
            "sla_hours": result.get("sla_deadline_hours", 24),
            "confidence": result.get("confidence", "medium"),
            "model_used": result.get("model_used", ""),
        }

    # Fallback: direct Groq call if genai service is down
    logger.warning("GenAI service unavailable, falling back to direct LLM call")
    try:
        from agents.llm_router import call_llm
        from prompts.resolution import RESOLUTION_PROMPT
        prompt = RESOLUTION_PROMPT.format(
            complaint=text, category=category,
            priority=priority, sentiment_score=sentiment,
        )
        llm_result = await call_llm(
            system_prompt="You are a resolution agent for an FMCG complaint management system. Generate specific, actionable resolution steps. Always respond in valid JSON.",
            user_prompt=prompt, json_mode=True, max_tokens=400,
        )
        llm_result.setdefault("steps", ["Investigate the complaint", "Contact customer for details"])
        llm_result.setdefault("escalation", False)
        llm_result.setdefault("estimated_resolution", "1-2 business days")
        return llm_result
    except Exception as e:
        logger.error(f"Fallback LLM resolution also failed: {e}")

    return {
        "customer_response": "",
        "steps": ["Investigate the complaint", "Contact customer for details"],
        "escalation": priority == "High",
        "estimated_resolution": "1-2 business days",
    }
