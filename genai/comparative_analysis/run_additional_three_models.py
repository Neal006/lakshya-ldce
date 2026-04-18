"""
Run only the 3 additional models, merge with existing latest results,
and regenerate the aggregated report.

Usage:
    cd genai
    python -m comparative_analysis.run_additional_three_models
"""

import os

from comparative_analysis.run_ablation import run_ablation
from comparative_analysis.generate_report import main as generate_report


THREE_MODEL_KEYS = "groq_llama70b,gemini_2_5_flash,hf_qwen_72b"


def main():
    # Restrict this run to the 3 newly added models only.
    os.environ["RUN_MODEL_KEYS"] = THREE_MODEL_KEYS
    # Merge these model outputs into existing ablation_results_latest.json.
    os.environ["MERGE_WITH_LATEST"] = "1"

    print("=" * 72)
    print("  Running additional 3 models only")
    print(f"  Model keys: {THREE_MODEL_KEYS}")
    print("  Merge mode: ON (MERGE_WITH_LATEST=1)")
    print("=" * 72)

    run_ablation()

    print("\nRegenerating aggregated report from merged latest results...\n")
    generate_report()


if __name__ == "__main__":
    main()

