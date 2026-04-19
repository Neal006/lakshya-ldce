"""
Generate comparative analysis report with graphs from SOLV.ai ablation results.

Usage:
    cd genai
    python -m comparative_analysis.generate_report
"""

import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comparative_analysis.config import RESULTS_DIR, GRAPHS_DIR


# ─── Palette & labels ────────────────────────────────────────────────────────

METRIC_LABELS = {
    "avg_classification": "Category\nAccuracy",
    "avg_priority":       "Priority\nAccuracy",
    "avg_resolution":     "Resolution\nQuality",
    "avg_format":         "Format\nCompliance",
    "avg_quality":        "Response\nQuality",
}

TASK_COLORS = {
    "classify": "#4F46E5",
    "resolve":  "#0891B2",
    "ticket":   "#059669",
}

MODEL_COLORS = [
    "#4F46E5", "#E11D48", "#D97706", "#059669",
    "#7C3AED", "#0891B2", "#DC2626", "#B45309",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_results() -> dict:
    path = RESULTS_DIR / "ablation_results_latest.json"
    if not path.exists():
        print(f"✗ No results at {path}")
        print("  Run 'python -m comparative_analysis.run_ablation' first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_model_metrics(data: dict) -> dict:
    """Aggregate per-metric averages for every model."""
    metrics = {}
    for model_key, model_data in data.items():
        results = model_data.get("results", [])
        valid   = [r for r in results if not r.get("error")]
        if not valid:
            continue

        n            = len(valid)
        display_name = model_data.get("display_name", model_key)

        def avg(key):
            return sum(r["evaluation"][key]["score"] for r in valid) / n

        entry = {
            "display_name":       display_name,
            "n_valid":            n,
            "n_total":            len(results),
            "avg_overall":        sum(r["evaluation"]["overall_score"] for r in valid) / n,
            "avg_latency":        sum(r["latency_seconds"] for r in valid) / n,
            "avg_classification": avg("classification_accuracy"),
            "avg_priority":       avg("priority_accuracy"),
            "avg_resolution":     avg("resolution_quality"),
            "avg_format":         avg("format_compliance"),
            "avg_quality":        avg("response_quality"),
            "avg_input_tokens":   sum(r["input_tokens"]  or 0 for r in valid) / n,
            "avg_output_tokens":  sum(r["output_tokens"] or 0 for r in valid) / n,
        }

        # Per-task breakdown
        for task in ("classify", "resolve", "ticket"):
            tr = [r for r in valid if r["task"] == task]
            if tr:
                tn = len(tr)
                entry[f"avg_overall_{task}"] = sum(r["evaluation"]["overall_score"] for r in tr) / tn
                entry[f"avg_latency_{task}"] = sum(r["latency_seconds"] for r in tr) / tn

        metrics[model_key] = entry

    return metrics


# ─── Graph 1: Overall score bar chart ────────────────────────────────────────

def plot_overall_scores(metrics: dict):
    fig, ax = plt.subplots(figsize=(13, 6))
    names  = [m["display_name"] for m in metrics.values()]
    scores = [m["avg_overall"]  for m in metrics.values()]
    colors = MODEL_COLORS[:len(names)]

    bars = ax.barh(names, scores, color=colors, edgecolor="white", height=0.55)
    ax.set_xlim(0, 1.1)
    ax.set_xlabel("Average Overall Score (0–1)", fontsize=11)
    ax.set_title("SOLV.ai – Overall Model Performance Comparison", fontsize=14,
                 fontweight="bold", pad=14)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.axvline(x=0.7, color="gray", linestyle="--", linewidth=1, alpha=0.5,
               label="70% threshold")
    ax.legend(fontsize=9)

    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.012, bar.get_y() + bar.get_height() / 2,
                f"{score:.1%}", va="center", fontsize=10, fontweight="bold")

    ax.invert_yaxis()
    plt.tight_layout()
    out = GRAPHS_DIR / "01_overall_scores.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Graph 2: Radar chart ─────────────────────────────────────────────────────

def plot_radar_chart(metrics: dict):
    cats   = list(METRIC_LABELS.values())
    keys   = list(METRIC_LABELS.keys())
    N      = len(cats)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

    for i, (model_key, m) in enumerate(metrics.items()):
        values  = [m[k] for k in keys]
        values += values[:1]
        color   = MODEL_COLORS[i % len(MODEL_COLORS)]
        ax.plot(angles, values, "o-", linewidth=2, label=m["display_name"], color=color)
        ax.fill(angles, values, alpha=0.07, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.set_title("SOLV.ai – Multi-Metric Radar Comparison", fontsize=14,
                 fontweight="bold", pad=25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.15), fontsize=8)
    plt.tight_layout()
    out = GRAPHS_DIR / "02_radar_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Graph 3: Latency comparison ─────────────────────────────────────────────

def plot_latency(metrics: dict):
    fig, ax = plt.subplots(figsize=(13, 6))
    names    = [m["display_name"] for m in metrics.values()]
    latencies = [m["avg_latency"] for m in metrics.values()]
    colors   = MODEL_COLORS[:len(names)]

    bars = ax.barh(names, latencies, color=colors, edgecolor="white", height=0.55)
    ax.set_xlabel("Average Latency (seconds)", fontsize=11)
    ax.set_title("SOLV.ai – Response Latency Comparison", fontsize=14,
                 fontweight="bold", pad=14)

    for bar, lat in zip(bars, latencies):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{lat:.1f}s", va="center", fontsize=10, fontweight="bold")

    ax.invert_yaxis()
    plt.tight_layout()
    out = GRAPHS_DIR / "03_latency_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Graph 4: Per-task grouped bar ────────────────────────────────────────────

def plot_per_task_scores(metrics: dict):
    tasks        = ["classify", "resolve", "ticket"]
    task_labels  = ["Classify", "Resolve", "Ticket Generation"]
    model_names  = [m["display_name"] for m in metrics.values()]

    x        = np.arange(len(tasks))
    n_models = len(metrics)
    width    = 0.75 / n_models

    fig, ax = plt.subplots(figsize=(13, 6))
    for i, (model_key, m) in enumerate(metrics.items()):
        scores = [m.get(f"avg_overall_{t}", 0) for t in tasks]
        offset = (i - n_models / 2 + 0.5) * width
        ax.bar(x + offset, scores, width, label=m["display_name"],
               color=MODEL_COLORS[i % len(MODEL_COLORS)], edgecolor="white")

    ax.set_ylabel("Average Score", fontsize=11)
    ax.set_title("SOLV.ai – Performance by Task Type", fontsize=14,
                 fontweight="bold", pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(task_labels, fontsize=11)
    ax.set_ylim(0, 1.15)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    plt.tight_layout()
    out = GRAPHS_DIR / "04_per_task_scores.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Graph 5: Score vs latency scatter ────────────────────────────────────────

def plot_score_vs_latency(metrics: dict):
    fig, ax = plt.subplots(figsize=(10, 7))
    for i, (model_key, m) in enumerate(metrics.items()):
        color = MODEL_COLORS[i % len(MODEL_COLORS)]
        ax.scatter(m["avg_latency"], m["avg_overall"], s=220, c=color,
                   edgecolors="white", linewidth=1.5, zorder=5)
        ax.annotate(m["display_name"],
                    (m["avg_latency"], m["avg_overall"]),
                    textcoords="offset points", xytext=(8, 6), fontsize=9)

    ax.set_xlabel("Average Latency (seconds)", fontsize=11)
    ax.set_ylabel("Average Overall Score", fontsize=11)
    ax.set_title("SOLV.ai – Quality vs Speed (top-left is best)", fontsize=14,
                 fontweight="bold", pad=14)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = GRAPHS_DIR / "05_score_vs_latency.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Graph 6: Metric heatmap ──────────────────────────────────────────────────

def plot_metric_heatmap(metrics: dict):
    metric_keys   = ["avg_classification", "avg_priority", "avg_resolution",
                     "avg_format", "avg_quality"]
    metric_labels = ["Category\nAccuracy", "Priority\nAccuracy", "Resolution\nQuality",
                     "Format\nCompliance", "Response\nQuality"]
    model_names   = [m["display_name"] for m in metrics.values()]

    data = np.array([[m[k] for k in metric_keys] for m in metrics.values()])

    fig, ax = plt.subplots(figsize=(13, max(4, len(model_names) * 0.9 + 2)))
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(np.arange(len(metric_labels)))
    ax.set_xticklabels(metric_labels, fontsize=10)
    ax.set_yticks(np.arange(len(model_names)))
    ax.set_yticklabels(model_names, fontsize=10)

    for i in range(len(model_names)):
        for j in range(len(metric_labels)):
            val   = data[i, j]
            color = "white" if val < 0.35 or val > 0.75 else "black"
            ax.text(j, i, f"{val:.0%}", ha="center", va="center",
                    fontsize=11, fontweight="bold", color=color)

    ax.set_title("SOLV.ai – Detailed Metric Heatmap", fontsize=14,
                 fontweight="bold", pad=14)
    fig.colorbar(im, ax=ax, label="Score", shrink=0.8)
    plt.tight_layout()
    out = GRAPHS_DIR / "06_metric_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Graph 7: Token usage ─────────────────────────────────────────────────────

def plot_token_usage(metrics: dict):
    fig, ax    = plt.subplots(figsize=(13, 6))
    names      = [m["display_name"]    for m in metrics.values()]
    inp_tokens = [m["avg_input_tokens"] for m in metrics.values()]
    out_tokens = [m["avg_output_tokens"] for m in metrics.values()]

    x     = np.arange(len(names))
    width = 0.35
    ax.bar(x - width / 2, inp_tokens, width, label="Input Tokens",
           color="#4F46E5", edgecolor="white")
    ax.bar(x + width / 2, out_tokens, width, label="Output Tokens",
           color="#E11D48", edgecolor="white")

    ax.set_ylabel("Average Tokens per Call", fontsize=11)
    ax.set_title("SOLV.ai – Token Usage Comparison", fontsize=14,
                 fontweight="bold", pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9, rotation=20, ha="right")
    ax.legend()
    plt.tight_layout()
    out = GRAPHS_DIR / "07_token_usage.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Graph 8: Category/Priority accuracy per scenario ────────────────────────

def plot_category_priority_accuracy(data: dict, metrics: dict):
    """Grouped bar: classification accuracy across the 4 complaint scenarios."""
    scenario_names = ["allergic_reaction", "product_quality", "packaging_damage", "trade_inquiry"]
    scenario_labels = ["Allergic\nReaction\n(Product/High)", "Product\nQuality\n(Product/Med)",
                       "Packaging\nDamage\n(Packaging/Med)", "Trade\nInquiry\n(Trade/Low)"]

    x        = np.arange(len(scenario_names))
    n_models = len(metrics)
    width    = 0.75 / n_models

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    for ax_idx, metric_key, title in [
        (0, "classification_accuracy", "Category Classification Accuracy by Scenario"),
        (1, "priority_accuracy",       "Priority Assignment Accuracy by Scenario"),
    ]:
        ax = axes[ax_idx]
        for i, (model_key, m_data) in enumerate(data.items()):
            valid   = [r for r in m_data.get("results", []) if not r.get("error")]
            display = m_data.get("display_name", model_key)
            scores  = []
            for sname in scenario_names:
                sc_results = [r for r in valid
                              if r["scenario_name"] == sname and r["task"] == "classify"]
                if sc_results:
                    scores.append(sc_results[0]["evaluation"][metric_key]["score"])
                else:
                    scores.append(0.0)
            offset = (i - n_models / 2 + 0.5) * width
            ax.bar(x + offset, scores, width, label=display,
                   color=MODEL_COLORS[i % len(MODEL_COLORS)], edgecolor="white")

        ax.set_ylabel("Score", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_labels, fontsize=9)
        ax.set_ylim(0, 1.2)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        if ax_idx == 1:
            ax.legend(fontsize=7, ncol=2, loc="upper right")

    plt.suptitle("SOLV.ai – Classification & Priority Accuracy per Scenario",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = GRAPHS_DIR / "08_scenario_accuracy.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─── Markdown report ─────────────────────────────────────────────────────────

def generate_markdown_report(metrics: dict, data: dict) -> Path:
    ranked = sorted(metrics.items(), key=lambda x: x[1]["avg_overall"], reverse=True)

    lines = [
        "# SOLV.ai – Complaint Classification & Resolution Engine",
        "## Ablation Study / Comparative Analysis",
        "",
        "> **Objective:** Identify the best LLM for the SOLV.ai wellness-industry complaint",
        "> management system by benchmarking models across classification, resolution",
        "> recommendation, and ticket generation tasks.",
        "",
        "---",
        "",
        "## Models Evaluated",
        "",
        "| # | Model | Provider | Model ID |",
        "|---|-------|----------|----------|",
    ]

    for i, (mk, m) in enumerate(metrics.items(), 1):
        mdl = data[mk]
        lines.append(f"| {i} | **{m['display_name']}** | {mdl['provider']} | `{mdl['model_id']}` |")

    lines += [
        "",
        "All models accessed via OpenCode / OpenRouter (OpenAI-compatible API).",
        "",
        "---",
        "",
        "## Evaluation Criteria",
        "",
        "Each model response is scored on **five weighted metrics**:",
        "",
        "| Metric | Weight | What it measures |",
        "|--------|--------|-----------------|",
        "| **Classification Accuracy** | 30% | Correct complaint category (Product / Packaging / Trade) |",
        "| **Priority Accuracy** | 25% | Correct urgency level (High / Medium / Low); adjacent = 50% credit |",
        "| **Resolution Quality** | 25% | Completeness & actionability of resolution steps / ticket |",
        "| **Format Compliance** | 10% | Valid JSON with all required schema fields |",
        "| **Response Quality** | 10% | Appropriate length, no refusals, coherent output |",
        "",
        "### Test Scenarios",
        "",
        "| Scenario | Category | Priority | Channel |",
        "|----------|----------|----------|---------|",
        "| Allergic Reaction (Priya Sharma) | Product | **High** | Email |",
        "| Product Efficacy Complaint (Rajesh Kumar) | Product | Medium | Call Centre |",
        "| Packaging / Seal Damage (Sneha Patel) | Packaging | Medium | Email |",
        "| Trade / Bulk Pricing Inquiry (HealthPlus Pharmacy) | Trade | Low | Email |",
        "",
        "Each scenario is tested on **3 tasks** (classify / resolve / ticket) → **12 API calls per model**, "
        f"**{12 * len(metrics)} total API calls**.",
        "",
        "---",
        "",
        "## Overall Rankings",
        "",
        "| Rank | Model | Overall | Latency | Category Acc. | Priority Acc. | Resolution | Format |",
        "|------|-------|:-------:|:-------:|:-------------:|:-------------:|:----------:|:------:|",
    ]

    for rank, (mk, m) in enumerate(ranked, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
        lines.append(
            f"| {medal} | **{m['display_name']}** "
            f"| {m['avg_overall']:.1%} "
            f"| {m['avg_latency']:.1f}s "
            f"| {m['avg_classification']:.0%} "
            f"| {m['avg_priority']:.0%} "
            f"| {m['avg_resolution']:.0%} "
            f"| {m['avg_format']:.0%} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Graphs",
        "",
        "### Overall Score Comparison",
        "",
        "![Overall Scores](graphs/01_overall_scores.png)",
        "",
        "### Multi-Metric Radar",
        "",
        "![Radar Comparison](graphs/02_radar_comparison.png)",
        "",
        "### Response Latency",
        "",
        "![Latency Comparison](graphs/03_latency_comparison.png)",
        "",
        "### Per-Task Breakdown",
        "",
        "![Per-Task Scores](graphs/04_per_task_scores.png)",
        "",
        "### Quality vs Speed",
        "",
        "![Score vs Latency](graphs/05_score_vs_latency.png)",
        "",
        "### Detailed Metric Heatmap",
        "",
        "![Metric Heatmap](graphs/06_metric_heatmap.png)",
        "",
        "### Token Usage",
        "",
        "![Token Usage](graphs/07_token_usage.png)",
        "",
        "### Classification & Priority Accuracy per Scenario",
        "",
        "![Scenario Accuracy](graphs/08_scenario_accuracy.png)",
        "",
        "---",
        "",
        "## Per-Task Breakdown",
        "",
    ]

    for task, label in [("classify", "Classify"), ("resolve", "Resolve"), ("ticket", "Ticket Generation")]:
        lines += [f"### {label} Task", "",
                  "| Model | Score | Latency |", "|-------|:-----:|:-------:|"]
        for mk, m in ranked:
            score   = m.get(f"avg_overall_{task}", 0)
            latency = m.get(f"avg_latency_{task}", 0)
            lines.append(f"| {m['display_name']} | {score:.1%} | {latency:.1f}s |")
        lines.append("")

    lines += [
        "---",
        "",
        "## Detailed Metric Scores",
        "",
        "| Model | Category | Priority | Resolution | Format | Quality |",
        "|-------|:--------:|:--------:|:----------:|:------:|:-------:|",
    ]
    for mk, m in ranked:
        lines.append(
            f"| {m['display_name']} "
            f"| {m['avg_classification']:.0%} "
            f"| {m['avg_priority']:.0%} "
            f"| {m['avg_resolution']:.0%} "
            f"| {m['avg_format']:.0%} "
            f"| {m['avg_quality']:.0%} |"
        )

    # Recommendation section
    best_mk, best_m      = ranked[0]
    runner_mk, runner_m  = ranked[1] if len(ranked) > 1 else (None, None)
    fastest_mk, fastest_m = min(metrics.items(), key=lambda x: x[1]["avg_latency"])

    lines += [
        "",
        "---",
        "",
        "## Recommendation",
        "",
        f"Based on this ablation study across **{12 * len(metrics)} API calls**, "
        f"**{best_m['display_name']}** achieves the highest overall score of "
        f"**{best_m['avg_overall']:.1%}**.",
        "",
    ]

    if runner_m:
        lines.append(
            f"The runner-up is **{runner_m['display_name']}** at **{runner_m['avg_overall']:.1%}**."
        )
        lines.append("")

    lines += [
        f"For latency-critical deployments (real-time complaint intake), "
        f"**{fastest_m['display_name']}** is the fastest at "
        f"**{fastest_m['avg_latency']:.1f}s** average.",
        "",
        "### Selection Criteria for SOLV.ai Production",
        "",
        "The recommended model for SOLV.ai must:",
        "- Classify complaints with **≥ 90% category accuracy** (no misfiled tickets)",
        "- Assign correct priority in **≥ 85% of cases** (SLA compliance depends on this)",
        "- Produce valid, actionable resolution steps for all complaint types",
        "- Respond within **5 seconds** (real-time SLA requirement)",
        "",
        "---",
        "",
        "## How to Reproduce",
        "",
        "```bash",
        "cd genai",
        "",
        "# Set your API key",
        "export OPENCODE_API_KEY=your_key_here",
        "",
        "# 1. Test API connectivity",
        "python -m comparative_analysis.test_api_keys",
        "",
        "# 2. Run the ablation study  (~10-15 minutes for 8 models × 12 calls)",
        "python -m comparative_analysis.run_ablation",
        "",
        "# 3. Generate graphs and markdown report",
        "python -m comparative_analysis.generate_report",
        "```",
        "",
        "Results are saved to `results/` and graphs to `graphs/`.",
        "",
        "---",
        "",
        "*Report auto-generated by SOLV.ai Ablation Study Framework*",
    ]

    report_path = GRAPHS_DIR.parent / "ABLATION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✓ {report_path.name}")
    return report_path


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(GRAPHS_DIR, exist_ok=True)

    print("=" * 65)
    print("  SOLV.ai – Generating Comparative Analysis Report")
    print("=" * 65)

    data    = load_results()
    metrics = get_model_metrics(data)

    if not metrics:
        print("✗ No valid model results found. Run run_ablation.py first.")
        sys.exit(1)

    print(f"\n  Models with valid results : {len(metrics)}\n")
    print("  Generating graphs …")

    plot_overall_scores(metrics)
    plot_radar_chart(metrics)
    plot_latency(metrics)
    plot_per_task_scores(metrics)
    plot_score_vs_latency(metrics)
    plot_metric_heatmap(metrics)
    plot_token_usage(metrics)
    plot_category_priority_accuracy(data, metrics)

    print("\n  Generating markdown report …")
    report_path = generate_markdown_report(metrics, data)

    print(f"\n{'=' * 65}")
    print(f"  Done!  Report : {report_path}")
    print(f"         Graphs : {GRAPHS_DIR}/")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    main()
