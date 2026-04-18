"""
guardrails.py — Input sanitization, output validation, and security guardrails.
"""

import re
import json
import logging
import html

logger = logging.getLogger("genai.guardrails")

# ─── Layer 1: Input Validation ──────────────────────────────────────

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?previous",
    r"system\s*prompt",
    r"you\s+are\s+now",
    r"act\s+as\s+if",
    r"pretend\s+you",
    r"new\s+instructions",
    r"override\s+instructions",
    r"<\s*script",
    r"javascript:",
    r"on\w+\s*=",
]

_COMPILED_INJECTION = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

VALID_CATEGORIES = {"Product", "Packaging", "Trade"}
VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_CHANNELS = {"web", "email", "phone", "chat", "call", "sms", "direct", "api"}


def sanitize_text(text: str, max_length: int = 2000) -> str:
    """Sanitize complaint text: escape HTML, truncate, strip control chars."""
    # Strip null bytes and control characters (keep newlines/tabs)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Escape HTML entities
    cleaned = html.escape(cleaned, quote=True)
    # Truncate
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned.strip()


def check_prompt_injection(text: str) -> list[str]:
    """Detect common prompt injection patterns. Returns list of violations."""
    violations = []
    for pattern in _COMPILED_INJECTION:
        if pattern.search(text):
            violations.append(f"Prompt injection pattern detected: {pattern.pattern}")
    return violations


def validate_input(data: dict) -> list[str]:
    """Validate classifier output fields. Returns list of violations."""
    violations = []

    if data.get("category") not in VALID_CATEGORIES:
        violations.append(f"Invalid category: {data.get('category')}")

    if data.get("priority") not in VALID_PRIORITIES:
        violations.append(f"Invalid priority: {data.get('priority')}")

    sentiment = data.get("sentiment_score")
    if sentiment is not None and not (-1.0 <= sentiment <= 1.0):
        violations.append(f"Sentiment score out of range: {sentiment}")

    text = data.get("text", "")
    if not text or len(text.strip()) < 3:
        violations.append("Complaint text is too short or empty")

    injection = check_prompt_injection(text)
    violations.extend(injection)

    return violations


# ─── Layer 3: Output Validation ─────────────────────────────────────

REQUIRED_OUTPUT_FIELDS = [
    "customer_response",
    "immediate_action",
    "resolution_steps",
    "assigned_team",
    "escalation_required",
    "follow_up_required",
    "follow_up_timeline",
    "estimated_resolution_time",
    "root_cause_hypothesis",
]

VALID_ASSIGNED_TEAMS = {
    "Customer Support", "Quality Assurance", "Logistics", "Sales",
}


def validate_output(parsed: dict, input_data: dict) -> list[str]:
    """Cross-check LLM output against input data. Returns list of violations."""
    violations = []

    # Check required fields
    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in parsed:
            violations.append(f"Missing required field: {field}")

    # Check assigned_team is valid
    team = parsed.get("assigned_team", "")
    if team and team not in VALID_ASSIGNED_TEAMS:
        violations.append(f"Invalid assigned_team: {team}")

    # High priority must have escalation_required=True
    if input_data.get("priority") == "High" and not parsed.get("escalation_required"):
        violations.append("High priority complaint must have escalation_required=true")

    # Resolution steps must be a non-empty list
    steps = parsed.get("resolution_steps")
    if not isinstance(steps, list) or len(steps) == 0:
        violations.append("resolution_steps must be a non-empty list")

    # Customer response must not be empty
    cr = parsed.get("customer_response", "")
    if not cr or len(cr) < 20:
        violations.append("customer_response is too short or empty")

    return violations


# ─── JSON Parsing ───────────────────────────────────────────────────

def safe_json_parse(text: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown fences."""
    if not text:
        return None

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None
