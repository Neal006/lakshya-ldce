"""
Evaluation metrics for TS-14 ablation study.
Scores each model response on five dimensions relevant to the complaint
classification and resolution recommendation use case.

Metric weights:
  Classification Accuracy  30% – Is the complaint category correct?
  Priority Accuracy        25% – Is the priority level correct?
  Resolution Quality       25% – Are resolution steps specific & actionable?
  Format Compliance        10% – Valid JSON with all required fields?
  Response Quality         10% – Appropriate length, no refusals
"""

import json
import re
from typing import Optional

# ─── Constants ───────────────────────────────────────────────────────────────

VALID_CATEGORIES = {"product", "packaging", "trade"}
VALID_PRIORITIES = {"high", "medium", "low"}

# Partial credit matrix for priority:  (expected, predicted) -> score
PRIORITY_PROXIMITY = {
    ("high",   "high"):   1.0,
    ("high",   "medium"): 0.5,
    ("high",   "low"):    0.0,
    ("medium", "high"):   0.5,
    ("medium", "medium"): 1.0,
    ("medium", "low"):    0.5,
    ("low",    "high"):   0.0,
    ("low",    "medium"): 0.5,
    ("low",    "low"):    1.0,
}

# Keywords that indicate actionable, wellness-context resolution steps
RESOLUTION_KEYWORDS = [
    "replace", "replacement", "refund", "escalat", "investigat", "lab", "test",
    "quality", "safety", "contact", "inspect", "return", "compensat", "apologis",
    "apologi", "recall", "notify", "follow", "check", "recall", "withdraw",
    "ship", "dispatch", "collect", "document", "photograph", "log",
]

# Required JSON fields per task
REQUIRED_FIELDS = {
    "classify": {"category", "priority", "justification", "keywords", "sla_hours"},
    "resolve":  {
        "immediate_action", "resolution_steps", "assigned_team",
        "escalation_required", "follow_up_required",
        "customer_communication", "estimated_resolution_time",
    },
    "ticket": {
        "title", "category", "priority", "description",
        "root_cause_hypothesis", "recommended_actions",
        "assigned_team", "sla_deadline_hours", "tags", "status",
    },
}

# Evaluation weights
WEIGHTS = {
    "classification_accuracy": 0.30,
    "priority_accuracy":       0.25,
    "resolution_quality":      0.25,
    "format_compliance":       0.10,
    "response_quality":        0.10,
}


# ─── Helper ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON from raw LLM output, tolerating markdown fences."""
    if not text:
        return None
    text = text.strip()
    # Strip ```json … ``` fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: grab the first {...} block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ─── Metric 1: Format Compliance ─────────────────────────────────────────────

def score_format_compliance(response: str, task: str) -> dict:
    """
    0.4 for valid JSON + up to 0.6 for required fields present.
    Returns: {"score": float, "valid_json": bool, "has_required_fields": bool, "details": str}
    """
    if not response:
        return {"score": 0.0, "valid_json": False, "has_required_fields": False,
                "details": "Empty response"}

    parsed = _extract_json(response)
    if parsed is None:
        return {"score": 0.0, "valid_json": False, "has_required_fields": False,
                "details": "Not valid JSON"}

    required    = REQUIRED_FIELDS.get(task, set())
    present     = {k.lower() for k in parsed.keys()}
    missing     = {f for f in required if f not in present}
    has_all     = len(missing) == 0
    field_ratio = (len(required) - len(missing)) / len(required) if required else 1.0
    score       = 0.4 + (0.6 * field_ratio)

    return {
        "score":              round(score, 3),
        "valid_json":         True,
        "has_required_fields": has_all,
        "details":            f"Missing fields: {missing}" if missing else "All required fields present",
    }


# ─── Metric 2: Classification Accuracy ───────────────────────────────────────

def score_classification_accuracy(response: str, expected_category: str, task: str) -> dict:
    """
    Binary: 1.0 if category matches, 0.0 otherwise.
    N/A for the resolve task (scores 1.0 automatically).
    Returns: {"score": float, "predicted": str, "expected": str, "details": str}
    """
    if task == "resolve":
        return {"score": 1.0, "predicted": "N/A", "expected": expected_category,
                "details": "Not evaluated for resolve task"}

    parsed = _extract_json(response)
    if parsed is None:
        return {"score": 0.0, "predicted": None, "expected": expected_category,
                "details": "Could not parse JSON"}

    predicted      = str(parsed.get("category", "")).strip().lower()
    expected_lower = expected_category.lower()

    if predicted == expected_lower:
        return {"score": 1.0, "predicted": predicted, "expected": expected_lower,
                "details": f"Correct: '{predicted}'"}
    elif predicted in VALID_CATEGORIES:
        return {"score": 0.0, "predicted": predicted, "expected": expected_lower,
                "details": f"Wrong category: '{predicted}' (expected '{expected_lower}')"}
    else:
        return {"score": 0.0, "predicted": predicted, "expected": expected_lower,
                "details": f"Invalid or missing category value: '{predicted}'"}


# ─── Metric 3: Priority Accuracy ─────────────────────────────────────────────

def score_priority_accuracy(response: str, expected_priority: str, task: str) -> dict:
    """
    1.0 for exact match, 0.5 for adjacent level, 0.0 otherwise.
    N/A for the resolve task (scores 1.0 automatically).
    Returns: {"score": float, "predicted": str, "expected": str, "details": str}
    """
    if task == "resolve":
        return {"score": 1.0, "predicted": "N/A", "expected": expected_priority,
                "details": "Not evaluated for resolve task"}

    parsed = _extract_json(response)
    if parsed is None:
        return {"score": 0.0, "predicted": None, "expected": expected_priority,
                "details": "Could not parse JSON"}

    predicted      = str(parsed.get("priority", "")).strip().lower()
    expected_lower = expected_priority.lower()
    score          = PRIORITY_PROXIMITY.get((expected_lower, predicted), 0.0)

    if predicted == expected_lower:
        details = f"Correct: '{predicted}'"
    elif predicted in VALID_PRIORITIES:
        details = f"Adjacent level: '{predicted}' (expected '{expected_lower}') – partial credit"
    else:
        details = f"Invalid or missing priority value: '{predicted}'"

    return {"score": round(score, 3), "predicted": predicted, "expected": expected_lower,
            "details": details}


# ─── Metric 4: Resolution Quality ────────────────────────────────────────────

def score_resolution_quality(response: str, expected_priority: str, task: str) -> dict:
    """
    Checks whether resolution steps are complete and actionable.
    N/A for classify task (scores 1.0 automatically).
    Returns: {"score": float, "checks": dict, "details": str}
    """
    if task == "classify":
        return {"score": 1.0, "checks": {}, "details": "Not evaluated for classify task"}

    if not response:
        return {"score": 0.0, "checks": {}, "details": "Empty response"}

    parsed     = _extract_json(response)
    text_lower = response.lower()
    checks     = {}

    if task == "resolve":
        steps = (parsed.get("resolution_steps", []) if parsed else [])
        checks["has_immediate_action"]    = (
            parsed is not None and
            bool(str(parsed.get("immediate_action", "")).strip())
        )
        checks["has_3plus_steps"]         = isinstance(steps, list) and len(steps) >= 3
        checks["steps_use_action_verbs"]  = any(kw in text_lower for kw in RESOLUTION_KEYWORDS)
        checks["has_customer_message"]    = (
            parsed is not None and
            len(str(parsed.get("customer_communication", ""))) > 20
        )
        checks["has_resolution_timeline"] = (
            parsed is not None and
            bool(str(parsed.get("estimated_resolution_time", "")).strip())
        )
        checks["escalation_logic_correct"] = (
            parsed is not None and (
                (expected_priority.lower() == "high" and
                 parsed.get("escalation_required") is True)
                or
                (expected_priority.lower() != "high" and
                 isinstance(parsed.get("escalation_required"), bool))
            )
        )

    elif task == "ticket":
        actions = (parsed.get("recommended_actions", []) if parsed else [])
        checks["has_title"]           = (
            parsed is not None and bool(str(parsed.get("title", "")).strip())
        )
        checks["has_description"]     = (
            parsed is not None and len(str(parsed.get("description", ""))) > 30
        )
        checks["has_root_cause"]      = (
            parsed is not None and
            bool(str(parsed.get("root_cause_hypothesis", "")).strip())
        )
        checks["has_2plus_actions"]   = isinstance(actions, list) and len(actions) >= 2
        checks["actions_actionable"]  = any(kw in text_lower for kw in RESOLUTION_KEYWORDS)
        checks["has_assigned_team"]   = (
            parsed is not None and bool(str(parsed.get("assigned_team", "")).strip())
        )
        checks["has_sla_deadline"]    = (
            parsed is not None and
            isinstance(parsed.get("sla_deadline_hours"), (int, float))
        )

    passed = sum(1 for v in checks.values() if v)
    total  = len(checks)
    score  = passed / total if total > 0 else 0.0

    return {
        "score":   round(score, 3),
        "checks":  checks,
        "details": f"{passed}/{total} checks passed",
    }


# ─── Metric 5: Response Quality ──────────────────────────────────────────────

def score_response_quality(response: str) -> dict:
    """
    Penalises refusals, empty responses, and extreme lengths.
    Returns: {"score": float, "word_count": int, "details": str}
    """
    if not response:
        return {"score": 0.0, "word_count": 0, "details": "Empty response"}

    word_count = len(response.split())
    issues     = []

    refusal_patterns = [
        "i cannot", "i'm sorry", "as an ai", "i don't have access",
        "i am unable", "i'm unable", "i cannot assist",
    ]
    if any(p in response.lower() for p in refusal_patterns):
        issues.append("Contains refusal/hedging language")

    if word_count < 30:
        issues.append(f"Too short ({word_count} words)")
    elif word_count > 2000:
        issues.append(f"Excessively long ({word_count} words)")

    score = max(0.0, 1.0 - len(issues) * 0.35)

    return {
        "score":      round(score, 3),
        "word_count": word_count,
        "details":    "; ".join(issues) if issues else "Good quality",
    }


# ─── Aggregate ────────────────────────────────────────────────────────────────

def evaluate_response(
    response:         str,
    task:             str,
    category:         str,
    priority:         str,
    latency_seconds:  float,
) -> dict:
    """
    Run all five metrics and return a weighted aggregate score.
    """
    fmt  = score_format_compliance(response, task)
    cls  = score_classification_accuracy(response, category, task)
    pri  = score_priority_accuracy(response, priority, task)
    res  = score_resolution_quality(response, priority, task)
    qual = score_response_quality(response)

    overall = (
        WEIGHTS["classification_accuracy"] * cls["score"]
        + WEIGHTS["priority_accuracy"]       * pri["score"]
        + WEIGHTS["resolution_quality"]      * res["score"]
        + WEIGHTS["format_compliance"]       * fmt["score"]
        + WEIGHTS["response_quality"]        * qual["score"]
    )

    return {
        "overall_score":           round(overall, 3),
        "classification_accuracy": cls,
        "priority_accuracy":       pri,
        "resolution_quality":      res,
        "format_compliance":       fmt,
        "response_quality":        qual,
        "latency_seconds":         latency_seconds,
    }
