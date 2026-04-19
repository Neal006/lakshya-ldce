"""
Test scenarios for the SOLV.ai ablation study.
Four realistic wellness-industry customer complaints covering all three
complaint categories (Product, Packaging, Trade) and all three priority
levels (High, Medium, Low).

Each scenario is tested on three tasks:
  classify  – classify category + priority + produce structured JSON
  resolve   – recommend actionable resolution steps
  ticket    – generate a structured support ticket
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comparative_analysis.prompts import (
    SYSTEM_PROMPT_CLASSIFY, USER_PROMPT_CLASSIFY,
    SYSTEM_PROMPT_RESOLVE,  USER_PROMPT_RESOLVE,
    SYSTEM_PROMPT_TICKET,   USER_PROMPT_TICKET,
)

# ─── Scenarios ───────────────────────────────────────────────────────────────

SCENARIO_ALLERGIC_REACTION = {
    "scenario_id":    "CPL-001",
    "category":       "Product",
    "priority":       "High",
    "channel":        "Email",
    "received_at":    "2026-04-17T09:15:00+05:30",
    "customer_name":  "Priya Sharma",
    "product_name":   "ProWellness Collagen Peptide Supplement (Batch: PW-COL-2024-03)",
    "complaint_text": (
        "I purchased your ProWellness Collagen Peptide Supplement last week from a local pharmacy. "
        "I started taking it three days ago as directed. Yesterday evening, within 30 minutes of "
        "consuming one sachet, I developed severe hives across my arms and face, noticeable lip "
        "swelling, and difficulty breathing. I visited the emergency room and was administered "
        "antihistamines intravenously. My attending physician suspects an allergic reaction "
        "triggered by an undisclosed ingredient in your product. The product label only mentions "
        "'contains fish collagen' with no full allergen panel listed. I am deeply concerned about "
        "safety and believe this could affect other customers. I have retained the remaining sachets "
        "and packaging for any investigation you may require. I demand an immediate response and "
        "want to know what you are doing to protect other consumers."
    ),
}

SCENARIO_PRODUCT_QUALITY = {
    "scenario_id":    "CPL-002",
    "category":       "Product",
    "priority":       "Medium",
    "channel":        "Call Centre",
    "received_at":    "2026-04-17T11:30:00+05:30",
    "customer_name":  "Rajesh Kumar",
    "product_name":   "ImmunoBoost Vitamin C + Zinc Tablets 500 mg (60-tablet pack)",
    "complaint_text": (
        "Call summary transcribed by support agent. "
        "Customer Mr. Rajesh Kumar called to report that he has been taking ImmunoBoost Vitamin C "
        "and Zinc Tablets for the past three months at the recommended dosage of two tablets daily. "
        "Despite consistent use, he has experienced two separate colds during this period, which he "
        "states never happened when he was using a competitor brand. On opening a new pack today, he "
        "noticed the tablets appear noticeably paler than those from his earlier packs of the same "
        "product. He suspects the formulation or manufacturing quality may have changed. He is "
        "requesting a full refund for both packs and is willing to courier the unused tablets back "
        "for quality testing. He expressed frustration that the product is not delivering the "
        "promised immunity benefits."
    ),
}

SCENARIO_PACKAGING_DAMAGE = {
    "scenario_id":    "CPL-003",
    "category":       "Packaging",
    "priority":       "Medium",
    "channel":        "Email",
    "received_at":    "2026-04-17T14:00:00+05:30",
    "customer_name":  "Sneha Patel",
    "product_name":   "OmegaCare Deep Sea Fish Oil 1000 mg Softgels (90-count bottle)",
    "complaint_text": (
        "I placed an order for OmegaCare Fish Oil Softgels through your official website on "
        "12 April 2026. The package arrived today and I was shocked by its condition. The outer "
        "delivery box was visibly crushed at one corner and the product carton inside had a deep "
        "dent. Most critically, the tamper-evident shrink-wrap seal on the bottle was completely "
        "torn, although the cap itself appeared to be on. I am concerned that the softgels may "
        "have been exposed to air, humidity, or external contaminants, which would compromise "
        "their potency and safety. I have documented this with photographs which I can provide on "
        "request. I would like an urgent replacement shipment sent using a protective packaging "
        "method. I also want assurance that your logistics partner has been informed about "
        "these handling failures."
    ),
}

SCENARIO_TRADE_INQUIRY = {
    "scenario_id":    "CPL-004",
    "category":       "Trade",
    "priority":       "Low",
    "channel":        "Email",
    "received_at":    "2026-04-17T10:00:00+05:30",
    "customer_name":  "HealthPlus Pharmacy – Mr. Arvind Mehta (Procurement Manager)",
    "product_name":   "Multiple SKUs: ProWellness, ImmunoBoost, OmegaCare product lines",
    "complaint_text": (
        "Dear Sales Team, "
        "We are HealthPlus Pharmacy, operating a chain of 18 retail outlets across Gujarat. "
        "We have been retailing your ProWellness and ImmunoBoost ranges for the past year and "
        "are pleased with the sell-through rate. We now wish to expand our assortment to include "
        "the full OmegaCare softgel range and are writing to discuss the following commercial terms: "
        "1. Bulk purchase pricing for orders exceeding 500 units per SKU per month. "
        "2. Possibility of exclusive distribution rights for the Surat metropolitan district. "
        "3. Availability of branded point-of-sale materials (shelf talkers, brochures) and "
        "pharmacist product-knowledge training sessions. "
        "4. Current stock levels and estimated lead times for new OmegaCare SKUs. "
        "Please have your regional sales representative contact us. "
        "Preferred contact window: Monday – Friday, 10:00 AM – 5:00 PM IST."
    ),
}

ALL_SCENARIOS = {
    "allergic_reaction": SCENARIO_ALLERGIC_REACTION,
    "product_quality":   SCENARIO_PRODUCT_QUALITY,
    "packaging_damage":  SCENARIO_PACKAGING_DAMAGE,
    "trade_inquiry":     SCENARIO_TRADE_INQUIRY,
}

# ─── Prompt builders ─────────────────────────────────────────────────────────

def build_classify_prompts(scenario: dict) -> tuple:
    """Returns (system_prompt, user_prompt) for the classification task."""
    return SYSTEM_PROMPT_CLASSIFY, USER_PROMPT_CLASSIFY.format(
        channel=scenario["channel"],
        received_at=scenario["received_at"],
        customer_name=scenario["customer_name"],
        product_name=scenario["product_name"],
        complaint_text=scenario["complaint_text"],
    )


def build_resolve_prompts(scenario: dict) -> tuple:
    """Returns (system_prompt, user_prompt) for the resolution recommendation task."""
    return SYSTEM_PROMPT_RESOLVE, USER_PROMPT_RESOLVE.format(
        category=scenario["category"],
        priority=scenario["priority"],
        channel=scenario["channel"],
        customer_name=scenario["customer_name"],
        product_name=scenario["product_name"],
        complaint_text=scenario["complaint_text"],
    )


def build_ticket_prompts(scenario: dict) -> tuple:
    """Returns (system_prompt, user_prompt) for the support ticket generation task."""
    return SYSTEM_PROMPT_TICKET, USER_PROMPT_TICKET.format(
        channel=scenario["channel"],
        received_at=scenario["received_at"],
        customer_name=scenario["customer_name"],
        product_name=scenario["product_name"],
        complaint_text=scenario["complaint_text"],
    )


# ─── Test case list ───────────────────────────────────────────────────────────

def get_all_test_cases() -> list:
    """
    Returns a list of test-case dicts, each with:
      task, scenario_name, category, priority, system_prompt, user_prompt
    Total: 4 scenarios × 3 tasks = 12 test cases per model.
    """
    cases = []
    for name, scenario in ALL_SCENARIOS.items():
        sys_c, usr_c = build_classify_prompts(scenario)
        cases.append({
            "task":          "classify",
            "scenario_name": name,
            "category":      scenario["category"],
            "priority":      scenario["priority"],
            "system_prompt": sys_c,
            "user_prompt":   usr_c,
        })

        sys_r, usr_r = build_resolve_prompts(scenario)
        cases.append({
            "task":          "resolve",
            "scenario_name": name,
            "category":      scenario["category"],
            "priority":      scenario["priority"],
            "system_prompt": sys_r,
            "user_prompt":   usr_r,
        })

        sys_t, usr_t = build_ticket_prompts(scenario)
        cases.append({
            "task":          "ticket",
            "scenario_name": name,
            "category":      scenario["category"],
            "priority":      scenario["priority"],
            "system_prompt": sys_t,
            "user_prompt":   usr_t,
        })

    return cases
