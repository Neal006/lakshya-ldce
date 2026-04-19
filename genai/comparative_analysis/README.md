# SOLV.ai – LLM Ablation Study & Comparative Analysis
## AI-Powered Complaint Classification & Resolution Recommendation Engine

> **Objective:** Determine the best LLM for SOLV.ai's wellness-industry complaint
> management pipeline by benchmarking 8 models on real complaint prompts across
> three tasks, then justify the production selection with data.

---

## Problem Statement

Customer complaints in a wellness business arrive through multiple channels
(call centres, emails, direct communication). They must be:

1. **Classified** into a category: *Product / Packaging / Trade*
2. **Priority-tagged**: *High / Medium / Low* based on urgency and impact
3. **Resolved** with specific, actionable next steps

Manual processing leads to delays, inconsistent tagging, and missed SLAs. This
ablation study identifies the LLM that best automates all three steps in real time.

---

## Models Evaluated

| # | Model | Provider | Notes |
|---|-------|----------|-------|
| 1 | **GLM 5** (Zhipu) | OpenRouter | Zhipu AI general-purpose model |
| 2 | **GLM 5.1** (Zhipu) | OpenRouter | Enhanced flash variant |
| 3 | **Kimi K2.5** (Moonshot) | OpenRouter | Long-context Chinese LLM |
| 4 | **MiMo V2 Omni** (Xiaomi) | OpenRouter | Multimodal reasoning model |
| 5 | **MiMo V2 Pro** (Xiaomi) | OpenRouter | Pro variant |
| 6 | **MiniMax M2.5** | OpenRouter | MiniMax instruction-tuned |
| 7 | **MiniMax M2.7** | OpenRouter | Extended context variant |
| 8 | **Qwen 3.5 Plus** (Alibaba) | OpenRouter | 235B MoE model |

All models share a single **OpenCode / OpenRouter** endpoint — one API key,
zero infrastructure overhead.

---

## Method

Each model receives identical inputs across **4 complaint scenarios × 3 tasks =
12 API calls per model** (96 total).

### Complaint Scenarios

| ID | Scenario | Category | Priority | Channel |
|----|----------|----------|----------|---------|
| CPL-001 | Severe allergic reaction to collagen supplement | **Product** | **High** | Email |
| CPL-002 | Immunity tablets ineffective, colour change noticed | **Product** | Medium | Call Centre |
| CPL-003 | Fish oil capsules arrive with broken tamper seal | **Packaging** | Medium | Email |
| CPL-004 | Pharmacy chain bulk pricing & distribution inquiry | **Trade** | Low | Email |

### Tasks per Scenario

| Task | Description | Expected Output |
|------|-------------|-----------------|
| **classify** | Assign category + priority + SLA | JSON with `category`, `priority`, `justification`, `keywords`, `sla_hours` |
| **resolve** | Recommend resolution steps | JSON with `immediate_action`, `resolution_steps`, `escalation_required`, `customer_communication`, … |
| **ticket** | Generate support ticket | JSON with `title`, `category`, `priority`, `description`, `root_cause_hypothesis`, `recommended_actions`, … |

### Evaluation Metrics

| Metric | Weight | Scoring Logic |
|--------|--------|--------------|
| **Classification Accuracy** | 30% | 1.0 if correct category, 0.0 otherwise |
| **Priority Accuracy** | 25% | 1.0 exact match; 0.5 adjacent level (High↔Medium or Medium↔Low); 0.0 otherwise |
| **Resolution Quality** | 25% | Checklist: immediate action, ≥ 3 steps, action verbs, customer message, escalation logic, timeline |
| **Format Compliance** | 10% | 0.4 for valid JSON + up to 0.6 for all required schema fields |
| **Response Quality** | 10% | Penalty for refusals, empty responses, extreme lengths |

---

## Results

> Run the ablation study to populate this section:
>
> ```bash
> cd genai
> export OPENCODE_API_KEY=your_key_here
> python -m comparative_analysis.run_ablation
> python -m comparative_analysis.generate_report
> ```
>
> The `ABLATION_REPORT.md` file and all graphs below will be generated automatically.

### Overall Rankings

*(populated after run)*

![Overall Scores](graphs/01_overall_scores.png)

---

### Multi-Metric Radar

Five-dimensional comparison across all evaluation axes.

![Radar Comparison](graphs/02_radar_comparison.png)

---

### Latency Comparison

Real-time complaint handling requires sub-5 second responses.

![Latency Comparison](graphs/03_latency_comparison.png)

---

### Per-Task Performance

Classify, Resolve, and Ticket Generation scored independently.

![Per-Task Scores](graphs/04_per_task_scores.png)

---

### Quality vs Speed — The Efficiency Frontier

Top-left corner = best (high score, low latency).

![Score vs Latency](graphs/05_score_vs_latency.png)

---

### Detailed Metric Heatmap

Green = strong, Red = weak, per model and metric.

![Metric Heatmap](graphs/06_metric_heatmap.png)

---

### Token Usage

Tracks input + output tokens per call — relevant for cost and rate limits.

![Token Usage](graphs/07_token_usage.png)

---

### Classification & Priority Accuracy per Scenario

Side-by-side accuracy breakdown across the 4 complaint types.

![Scenario Accuracy](graphs/08_scenario_accuracy.png)

---

## Selection Criteria for Production

The chosen model must meet all of:

| Criterion | Minimum Bar | Why |
|-----------|-------------|-----|
| Category accuracy | ≥ 90% | Mis-classification routes tickets to the wrong team |
| Priority accuracy | ≥ 85% | Incorrect priority breaks SLA compliance |
| Resolution quality | ≥ 75% | Actionable steps drive actual resolution |
| Average latency | ≤ 5 s | Real-time processing requirement (SOLV.ai winning logic) |
| Format compliance | ≥ 80% | Downstream dashboard parsing requires valid JSON |

---

## How to Reproduce

```bash
cd genai

# 1. Install dependencies
pip install openai matplotlib numpy

# 2. Set API key
export OPENCODE_API_KEY=your_key_here
# (or OPENROUTER_API_KEY — both are checked automatically)

# 3. Verify API connectivity
python -m comparative_analysis.test_api_keys

# 4. Run the ablation study  (~10–15 min for 8 models)
python -m comparative_analysis.run_ablation

# 5. Generate graphs + report
python -m comparative_analysis.generate_report
```

**Outputs:**
- `results/ablation_results_latest.json` — raw scores for all 96 calls
- `graphs/*.png` — 8 comparative visualizations
- `ABLATION_REPORT.md` — full ranked report with tables and graphs

---

## File Structure

```
genai/comparative_analysis/
├── config.py           — API keys, model IDs, evaluation settings
├── model_clients.py    — OpenAI-compatible client wrappers
├── prompts.py          — System + user prompts for all 3 tasks
├── test_scenarios.py   — 4 complaint scenarios + prompt builders
├── evaluate.py         — 5-metric scoring engine
├── run_ablation.py     — Main runner (all models × all test cases)
├── generate_report.py  — Graph generation + markdown report
├── test_api_keys.py    — Pre-flight API key verification
├── results/            — JSON result files
└── graphs/             — PNG graph outputs
```
