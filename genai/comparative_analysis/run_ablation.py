"""
Main ablation study runner for TS-14.
AI-Powered Complaint Classification & Resolution Recommendation Engine.

Runs all 12 test cases across all 8 models, evaluates each response,
and saves raw results JSON for downstream report generation.

Usage:
    cd genai
    python -m comparative_analysis.run_ablation
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comparative_analysis.config      import MODELS, RESULTS_DIR
from comparative_analysis.model_clients import create_client
from comparative_analysis.test_scenarios import get_all_test_cases
from comparative_analysis.evaluate    import evaluate_response


def _get_selected_models() -> dict:
    """
    Optionally filter models using RUN_MODEL_KEYS env var.
    Example:
        RUN_MODEL_KEYS=groq_llama70b,gemini_2_5_flash,hf_qwen_72b
    """
    model_keys_raw = os.getenv("RUN_MODEL_KEYS", "").strip()
    if not model_keys_raw:
        return MODELS

    selected_keys = [k.strip() for k in model_keys_raw.split(",") if k.strip()]
    selected = {k: MODELS[k] for k in selected_keys if k in MODELS}
    missing = [k for k in selected_keys if k not in MODELS]

    if missing:
        print(f"  ! Ignoring unknown model keys: {', '.join(missing)}")
    if not selected:
        raise ValueError("RUN_MODEL_KEYS provided, but none matched config MODELS.")
    return selected


def _merge_with_latest(new_results: dict, latest_path: Path) -> dict:
    """
    Merge current run into ablation_results_latest.json when MERGE_WITH_LATEST=1.
    New model keys overwrite old entries for the same model key.
    """
    if os.getenv("MERGE_WITH_LATEST", "0") != "1":
        return new_results

    if latest_path.exists():
        with open(latest_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = {}

    existing.update(new_results)
    return existing


def run_ablation():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    test_cases = get_all_test_cases()
    models_to_run = _get_selected_models()

    print("=" * 72)
    print("  TS-14 – Complaint Classification & Resolution Ablation Study")
    print("=" * 72)
    print(f"  Models  : {len(models_to_run)}")
    print(f"  Tests   : {len(test_cases)}  (4 scenarios × 3 tasks)")
    print(f"  Total   : {len(models_to_run) * len(test_cases)} API calls")
    print(f"  Started : {datetime.utcnow().isoformat()}Z")
    print("=" * 72)

    all_results = {}

    for model_key, model_cfg in models_to_run.items():
        print(f"\n{'─' * 65}")
        print(f"  Model    : {model_cfg['display_name']}")
        print(f"  Provider : {model_cfg['provider']}  |  ID: {model_cfg['model_id']}")
        print(f"{'─' * 65}")

        # Create client
        try:
            client = create_client(model_cfg)
        except Exception as e:
            print(f"  ✗ Failed to create client: {e}")
            all_results[model_key] = {"error": str(e), "results": []}
            continue

        # Health check
        health = client.health_check()
        if not health["ok"]:
            print(f"  ✗ Health check failed: {health['message']}")
            all_results[model_key] = {"error": health["message"], "results": []}
            continue
        print(f"  ✓ Health check passed: {health['message'][:60]}")

        model_results = []

        for i, tc in enumerate(test_cases):
            label = f"[{i+1:02d}/{len(test_cases)}] {tc['task']:8s} | {tc['scenario_name']}"
            print(f"  {label} … ", end="", flush=True)

            result = client.generate(tc["system_prompt"], tc["user_prompt"])

            if result["error"]:
                print(f"✗ {result['error'][:80]}")
                eval_scores = {
                    "overall_score":           0.0,
                    "classification_accuracy": {"score": 0.0, "details": "API error"},
                    "priority_accuracy":       {"score": 0.0, "details": "API error"},
                    "resolution_quality":      {"score": 0.0, "details": "API error"},
                    "format_compliance":       {"score": 0.0, "details": "API error"},
                    "response_quality":        {"score": 0.0, "details": "API error"},
                    "latency_seconds":         0.0,
                }
            else:
                eval_scores = evaluate_response(
                    response=result["response"],
                    task=tc["task"],
                    category=tc["category"],
                    priority=tc["priority"],
                    latency_seconds=result["latency_seconds"],
                )
                print(
                    f"✓  score={eval_scores['overall_score']:.2f}  "
                    f"latency={result['latency_seconds']:.1f}s  "
                    f"tokens={result.get('output_tokens', '?')}"
                )

            model_results.append({
                "task":            tc["task"],
                "scenario_name":   tc["scenario_name"],
                "category":        tc["category"],
                "priority":        tc["priority"],
                "response":        result["response"],
                "latency_seconds": result["latency_seconds"],
                "input_tokens":    result["input_tokens"],
                "output_tokens":   result["output_tokens"],
                "error":           result["error"],
                "evaluation":      eval_scores,
            })

            time.sleep(1.5)   # rate-limit buffer between calls

        all_results[model_key] = {
            "display_name": model_cfg["display_name"],
            "provider":     model_cfg["provider"],
            "model_id":     model_cfg["model_id"],
            "results":      model_results,
        }

        print(f"  → Pausing 3 s before next model …")
        time.sleep(3)

    # ── Save raw results ──────────────────────────────────────────────────────
    timestamp    = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_path = RESULTS_DIR / f"ablation_results_{timestamp}.json"
    latest_path  = RESULTS_DIR / "ablation_results_latest.json"

    final_results = _merge_with_latest(all_results, latest_path)

    for path in (results_path, latest_path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(final_results, f, indent=2, default=str)

    print(f"\n✓ Raw results saved to : {results_path}")
    print(f"✓ Latest copy at       : {latest_path}")

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\n" + "=" * 100)
    print("  SUMMARY")
    print("=" * 100)
    header = (
        f"  {'Model':<32} {'Overall':>8} {'Latency':>9} "
        f"{'Category':>10} {'Priority':>10} {'Resolution':>12} {'Format':>8}"
    )
    print(header)
    print("  " + "─" * 95)

    for model_key, data in all_results.items():
        if not data.get("results"):
            print(f"  {model_key:<32} {'ERROR':>8}")
            continue

        valid = [r for r in data["results"] if not r.get("error")]
        if not valid:
            print(f"  {data.get('display_name', model_key):<32} {'ALL FAILED':>8}")
            continue

        n        = len(valid)
        avg      = lambda key: sum(r["evaluation"][key]["score"] for r in valid) / n
        overall  = sum(r["evaluation"]["overall_score"] for r in valid) / n
        latency  = sum(r["latency_seconds"] for r in valid) / n

        print(
            f"  {data['display_name']:<32} "
            f"{overall:>7.1%} "
            f"{latency:>7.1f}s "
            f"{avg('classification_accuracy'):>10.0%} "
            f"{avg('priority_accuracy'):>10.0%} "
            f"{avg('resolution_quality'):>12.0%} "
            f"{avg('format_compliance'):>8.0%}"
        )

    print("=" * 100)
    print("\nDone! Run:  python -m comparative_analysis.generate_report\n")


if __name__ == "__main__":
    run_ablation()
