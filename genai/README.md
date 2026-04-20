# GenAI Complaint Resolution Microservice — Complete Documentation

> AI-powered resolution recommendation engine for customer complaints in the wellness industry.
> Built for **SOLV.ai — AI-Powered Complaint Classification & Resolution Recommendation Engine** (Tark Shaastra · LDCE Hackathon).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [File-by-File Deep Dive](#file-by-file-deep-dive)
  - [Root-Level Files](#root-level-files)
  - [Comparative Analysis Files](#comparative-analysis-files)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Request & Response Schemas](#request--response-schemas)
- [Prompt Engineering](#prompt-engineering)
- [Security & Guardrails](#security--guardrails)
- [Observability (LangSmith)](#observability-langsmith)
- [SLA Management](#sla-management)
- [Configuration Reference](#configuration-reference)
- [Integration with NLP Classifier](#integration-with-nlp-classifier)
- [Error Handling](#error-handling)
- [Example Scenarios](#example-scenarios)
- [Ablation Study — Comparative Analysis](#ablation-study--comparative-analysis)
  - [Models Evaluated](#models-evaluated)
  - [Test Scenarios](#test-scenarios)
  - [Evaluation Metrics](#evaluation-metrics)
  - [Graph Explanations](#graph-explanations)
    - [Graph 1: Overall Score Comparison](#graph-1-overall-score-comparison)
    - [Graph 2: Multi-Metric Radar Comparison](#graph-2-multi-metric-radar-comparison)
    - [Graph 3: Latency Comparison](#graph-3-latency-comparison)
    - [Graph 4: Per-Task Breakdown](#graph-4-per-task-breakdown)
    - [Graph 5: Score vs Latency](#graph-5-score-vs-latency)
    - [Graph 6: Metric Heatmap](#graph-6-metric-heatmap)
    - [Graph 7: Token Usage](#graph-7-token-usage)
    - [Graph 8: Scenario Accuracy](#graph-8-scenario-accuracy)
  - [ABLATION_REPORT.md](#ablation_reportmd)
  - [Results Directory](#results-directory)
  - [How to Reproduce](#how-to-reproduce)
- [Model Selection](#model-selection)

---

## Overview

This microservice is the **AI Resolution Engine** — the second stage of a two-service pipeline:

1. **NLP Text Classifier** (`text_classifier/`, port 8000) — classifies customer complaints into categories (Product/Packaging/Trade), assigns sentiment scores, and determines priority (High/Medium/Low) using ONNX-accelerated ML models.

2. **GenAI Resolution Service** (`genai/`, port 8001) — takes the classifier output and uses **Groq Llama 3.3 70B** (selected via ablation study across 10 models) to generate empathetic, actionable resolution recommendations with role-tagged steps, SLA tracking, and escalation logic.

### Key Features

| Feature | Description |
|---------|-------------|
| **Empathetic Customer Responses** | AI-generated apologetic messages tailored to complaint severity and sentiment |
| **Role-Tagged Resolution Steps** | Each action step is assigned to a specific team (Support, QA, Logistics, Sales) |
| **Sentiment-Aware Tone** | Response tone adapts based on VADER sentiment score from NLP pipeline |
| **Priority-Based Escalation** | High priority complaints are auto-escalated with 4-hour SLA |
| **Root Cause Hypothesis** | AI generates initial root cause analysis for each complaint |
| **4-Layer Security Guardrails** | Input sanitization, prompt injection detection, output validation, JSON parsing |
| **Rate Limiting** | Per-IP sliding-window rate limiter (60 req/min default) |
| **Optional API Key Auth** | Bearer token authentication for production deployments |
| **LangSmith Observability** | Full LLM call tracing — prompts, outputs, latency, tokens |
| **Structured JSON Output** | Every response is validated Pydantic JSON — never raw LLM text |
| **Branded HTML Email Generation** | solv.ai black+orange themed customer reply emails, Gmail-paste-ready |

---

## Architecture

```
                                                               
    Customer Complaint                                        
          |                                                   
          v                                                   
  +-------------------+         +---------------------------+ 
  |  NLP Classifier   |  HTTP   |  GenAI Resolution Service | 
  |  (port 8000)      | ------> |  (port 8001)              | 
  |                   |         |                           | 
  |  - Zero-shot NLI  |         |  +-----+  +-----------+  | 
  |  - VADER Sentiment|         |  | LLM |  |Guardrails |  | 
  |  - Decision Tree  |         |  |Client|  |(4-layer)  |  |     +----------------+
  |  - ONNX Runtime   |         |  +-----+  +-----------+  |---->| Groq API       |
  +-------------------+         |  +-------+ +---------+   |     | Llama 3.3 70B  |
                                |  |Prompts| |LangSmith|   |     +----------------+
    Output:                     |  +-------+ +---------+   | 
    - category                  +---------------------------+ 
    - sentiment_score                                         
    - priority                  Output:                       
                                - customer_response           
                                - resolution_steps            
                                - escalation_required         
                                - sla_deadline_hours          
                                - root_cause_hypothesis       
```

---

## How It Works

```
1. RECEIVE     Classifier output (complaint_id, text, category, sentiment, priority)
      |
2. SANITIZE    Strip control chars, escape HTML, check length limits
      |
3. DETECT      Scan for prompt injection patterns (13 regex rules)
      |
4. VALIDATE    Verify category/priority/sentiment are in valid ranges
      |
5. BUILD       Construct system + user prompt with all complaint context
      |
6. CALL LLM    Send to Groq Llama 3.3 70B (temp=0.25, max_tokens=2048)
      |
7. PARSE       Extract JSON from LLM response (handles fences, raw JSON)
      |
8. VALIDATE    Cross-check output: required fields, team validity, escalation rules
      |
9. RESPOND     Return structured ResolutionResponse with SLA + metadata
```

---

## Project Structure

```
genai/
├── .env                          # API keys and configuration (gitignored)
├── config.py                     # Centralized configuration loader
├── llm.py                        # Provider-agnostic LLM client + LangSmith tracing
├── models.py                     # Pydantic request/response schemas
├── prompts.py                    # System + user prompt templates
├── guardrails.py                 # 4-layer security: sanitize, detect, validate, parse
├── email_html.py                 # solv.ai branded HTML email builder
├── main.py                       # FastAPI server, routes, middleware
├── run_server.py                 # Entry point (python run_server.py)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── Problem Statement TS-21-23.pdf
├── generated_emails/             # Persisted HTML reply emails
├── comparative_analysis/         # Ablation study (10 models compared)
│   ├── __init__.py
│   ├── config.py                 # API keys, model IDs, evaluation settings
│   ├── model_clients.py          # OpenAI-compatible client wrappers for all providers
│   ├── prompts.py                # System + user prompts for all 3 tasks
│   ├── test_scenarios.py         # 4 complaint scenarios + prompt builders
│   ├── evaluate.py               # 5-metric scoring engine
│   ├── run_ablation.py           # Main runner (all models × all test cases)
│   ├── generate_report.py        # Graph generation + markdown report
│   ├── test_api_keys.py          # Pre-flight API key verification
│   ├── test_gemini.py            # Standalone Gemini vs Groq comparison test
│   ├── run_additional_three_models.py  # Incremental model addition runner
│   ├── requirements.txt          # Additional dependencies for ablation study
│   ├── README.md                 # Comparative analysis standalone docs
│   ├── ABLATION_REPORT.md        # Auto-generated ranked report with tables and graphs
│   ├── results/                  # JSON result files from ablation runs
│   │   ├── ablation_results_latest.json
│   │   ├── ablation_results_20260418_113320.json
│   │   └── ablation_results_20260418_121141.json
│   └── graphs/                   # PNG graph outputs
│       ├── 01_overall_scores.png
│       ├── 02_radar_comparison.png
│       ├── 03_latency_comparison.png
│       ├── 04_per_task_scores.png
│       ├── 05_score_vs_latency.png
│       ├── 06_metric_heatmap.png
│       ├── 07_token_usage.png
│       └── 08_scenario_accuracy.png
```

---

## File-by-File Deep Dive

### Root-Level Files

#### `config.py` — Centralized Configuration Loader

**Purpose:** Loads all settings from `genai/.env` and environment variables into a single `Config` class.

**How it works:**
- `_load_env()` reads the `.env` file line-by-line, parses `KEY=VALUE` pairs, strips quotes, and injects them into `os.environ` only if the key is not already set (no-overwrite policy).
- The `Config` class exposes typed constants with sensible defaults:
  - **LLM settings:** `LLM_API_KEY`, `LLM_MODEL` (default `llama-3.3-70b-versatile`), `LLM_BASE_URL` (default Groq), `LLM_TEMPERATURE` (0.25), `LLM_MAX_TOKENS` (2048).
  - **Upstream NLP:** `NLP_SERVICE_URL` (default `http://localhost:8000`).
  - **Service binding:** `HOST` (0.0.0.0), `PORT` (8001), `CORS_ORIGINS` (comma-separated, default `*`).
  - **Security:** `API_KEY` (optional bearer token), `RATE_LIMIT_RPM` (60), `MAX_COMPLAINT_LENGTH` (2000).
  - **Observability:** `LANGCHAIN_TRACING`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_ENDPOINT`.
  - **SLA defaults:** `SLA_HIGH` (4h), `SLA_MEDIUM` (24h), `SLA_LOW` (72h).
  - **Email output:** `REPLY_EMAIL_OUTPUT_DIR` (default `generated_emails`).

**Why it matters:** Single source of truth for every tunable parameter. Changing behavior requires only editing `.env` — no code changes.

---

#### `models.py` — Pydantic Request/Response Contracts

**Purpose:** Defines all data schemas using Pydantic for automatic validation, serialization, and Swagger documentation.

**Enums:**
- `Category` — `Product`, `Packaging`, `Trade`
- `Priority` — `High`, `Medium`, `Low`
- `ComplaintStatus` — `Open`, `In Progress`, `Escalated`, `Resolved`

**Request models:**
- `ClassifierOutput` — Input from NLP service with fields: `complaint_id` (int|str), `text` (1-2000 chars), `category` (enum), `sentiment_score` (-1.0 to 1.0), `priority` (enum), `latency_ms` (>=0). Includes an example for Swagger UI.
- `ResolveRequest` — Wraps `ClassifierOutput` with optional metadata: `customer_name` (default "Valued Customer"), `channel` (default "web"), `product_name` (default "Wellness Product").
- `EmailReplyHtmlRequest` — Wraps a `ResolutionResponse` to generate branded HTML email, with optional `customer_name`, `subject`, and `persist_file` flag.

**Response models:**
- `ResolutionResponse` — Full resolution output with 17 fields: complaint echo, classification echo, LLM-generated `customer_response`, `immediate_action`, `resolution_steps` (list), `assigned_team`, `escalation_required`, `follow_up_required`, `follow_up_timeline`, `estimated_resolution_time`, `root_cause_hypothesis`, `sla_deadline_hours`, `status`, `confidence`, `model_used`, `genai_latency_ms`.
- `HealthResponse` — Service health with `status`, `llm_connected`, `nlp_service_url`, `version`.
- `EmailReplyHtmlResponse` — Returns `subject`, `html` (full branded HTML string), `file_path` (when persisted), `model_used`, `genai_latency_ms`.

**Why it matters:** Pydantic enforces type safety at the API boundary. FastAPI auto-generates OpenAPI specs from these models, providing interactive Swagger docs at `/docs`.

---

#### `prompts.py` — Prompt Templates for Resolution

**Purpose:** Defines the system and user prompts that instruct the LLM how to generate resolution plans.

**`SYSTEM_PROMPT_RESOLVE`:**
- Establishes the AI's role as the "AI Resolution Engine for a wellness company."
- Provides domain context (supplements, vitamins, omega-3).
- Defines **resolution guidelines by category:** Product (replacement/refund, QA investigation), Packaging (re-shipment, logistics report), Trade (sales routing, pricing info).
- Defines **priority-based escalation matrix:** High = mandatory immediate escalation (4h SLA), Medium = conditional escalation (24h SLA), Low = standard workflow (72h SLA).
- Defines **sentiment-aware tone calibration:**
  - Score < -0.5: Extremely apologetic, offer compensation/goodwill gesture.
  - Score -0.5 to -0.2: Sincerely apologetic, reassure with concrete steps.
  - Score -0.2 to 0.0: Professional and empathetic.
  - Score > 0.0: Helpful and informative.
- Sets **customer communication rules:** Always start with sincere apology, never use generic phrases, reference exact issue, provide timeline, include reference number, end with quality assurance.
- **Anti-hallucination rules:** Only reference provided information, never fabricate details.
- Forces **strict JSON output schema** with 10 required fields.

**`USER_PROMPT_RESOLVE`:**
- Injects complaint-specific data via format placeholders: `complaint_id`, `customer_name`, `channel`, `product_name`, `category`, `priority`, `sentiment_score`, `complaint_text`.

**Why it matters:** The quality of LLM output is directly determined by prompt quality. This two-part architecture separates behavioral rules (system) from instance data (user), enabling consistent, reproducible generation.

---

#### `guardrails.py` — 4-Layer Security Architecture

**Purpose:** Implements input sanitization, prompt injection detection, output validation, and safe JSON parsing.

**Layer 1: Input Sanitization**
- `sanitize_text()` — Strips null bytes and control characters (`\x00-\x08\x0b\x0c\x0e-\x1f\x7f`), escapes HTML entities (prevents XSS), truncates to `max_length` (2000 chars).
- `validate_input()` — Checks category against `VALID_CATEGORIES`, priority against `VALID_PRIORITIES`, sentiment score range (-1.0 to 1.0), text minimum length (3 chars), and runs injection detection.

**Layer 2: Prompt Injection Detection**
- `check_prompt_injection()` — Scans text against 13 compiled regex patterns:
  - `"ignore all previous instructions"`, `"disregard previous"`, `"forget all previous"`
  - `"system prompt"`, `"you are now"`, `"act as if"`, `"pretend you"`
  - `"new instructions"`, `"override instructions"`
  - `"<script"`, `"javascript:"`, `"on*="` (XSS vectors)
- Returns a list of violation descriptions; any match triggers HTTP 400.

**Layer 3: Output Validation**
- `validate_output()` — Cross-checks LLM output against input data:
  - All 9 required fields must be present.
  - `assigned_team` must be in `VALID_ASSIGNED_TEAMS` (Customer Support, Quality Assurance, Logistics, Sales).
  - High priority complaints must have `escalation_required: true`.
  - `resolution_steps` must be a non-empty list.
  - `customer_response` must be at least 20 characters.

**Layer 4: Safe JSON Parsing**
- `safe_json_parse()` — Three-tier extraction:
  1. Direct `json.loads()` attempt.
  2. Extract from ` ```json ... ``` ` markdown fences via regex.
  3. Find first `{...}` block as fallback.

**Why it matters:** Without guardrails, LLMs can be manipulated via prompt injection, produce malformed output, or generate unsafe content. These four layers ensure production-grade reliability.

---

#### `llm.py` — Provider-Agnostic LLM Client with LangSmith Tracing

**Purpose:** Wraps the OpenAI-compatible API client with LangSmith observability, retry logic, and structured logging.

**LangSmith Bootstrap:**
- `_bootstrap_langsmith()` reads config, sets 4 environment variables (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_ENDPOINT`), and returns a config dict or `None` if disabled.
- `_ls_log_run()` uses `RunTree.post()` and `RunTree.patch()` to log each LLM call to the LangSmith dashboard with inputs, outputs, token counts, and timing. Includes a force-flush of the internal buffer to ensure traces appear immediately in long-running server processes.

**`LLMClient` class:**
- `__init__()` — Creates an `OpenAI` client with the provided API key and base URL. Logs whether LangSmith tracing is on or off.
- `generate()` — Sends system + user prompts to the LLM with configurable temperature and max tokens. Records start/end timestamps, extracts token usage from the response, logs to LangSmith, and emits a structured JSON log line to stdout. Raises on failure.
- `health_check()` — Sends a minimal "Say OK" test prompt to verify connectivity.

**Why it matters:** This client abstracts away the LLM provider, making it trivial to switch between Groq, OpenRouter, or any OpenAI-compatible endpoint. LangSmith integration provides production-grade observability for debugging and monitoring.

---

#### `email_html.py` — Branded HTML Email Builder

**Purpose:** Generates solv.ai branded (black + orange theme) customer reply emails from resolution data. No extra LLM call needed — all content comes from the `/resolve` response.

**`build_solvai_reply_html_from_resolution()`:**
- Returns a Gmail-paste-ready HTML `<table>` with full inline styles (no `<html>/<head>/<body>` wrapper).
- Sections built: Header (solv.ai branding), Reference line (complaint ID, category, priority, status), Subject, Greeting, Original complaint quote (left-bordered block), Body paragraphs (from `customer_response`), Resolution steps (bulleted list in orange-tinted card), Escalation notice (if applicable), Timeline table (follow-up, ETA, team, SLA), Sign-off ("Warm regards, Tanya"), Footer.
- All text is HTML-escaped to prevent injection.

**`write_reply_html_file()`:**
- Wraps the paste-ready table in a full HTML document with a "How to paste into Gmail" instruction banner.
- Saves to the configured output directory with a sanitized filename stem.

**Why it matters:** Turns structured JSON resolution data into a professional, branded customer-facing email that can be directly pasted into Gmail or any email client.

---

#### `main.py` — FastAPI Server

**Purpose:** The main application server exposing all API endpoints with middleware, security, and business logic.

**Initialization:**
- Configures structured logging (`%(asctime)s | %(levelname)s | %(name)s | %(message)s`).
- Sets up an in-memory sliding-window rate limiter (`_rate_store`) keyed by client IP.
- Defines `SLA_MAP` mapping priority levels to deadline hours.
- Creates the `LLMClient` during app lifespan startup.

**Middleware:**
- `rate_limit_middleware` — Checks each request against the per-IP sliding window (60 req/min). Returns HTTP 429 with `retry_after_seconds` if exceeded.
- `verify_api_key` — Optional Bearer token authentication. Only active if `GENAI_API_KEY` is set in config.

**Endpoints:**
- `GET /health` — Returns service status, LLM connectivity, and NLP service URL. Status is "healthy" if LLM responds, "degraded" otherwise.
- `POST /resolve` — Primary endpoint. Accepts `ResolveRequest`, runs through all 4 guardrail layers, calls the LLM, parses and validates output, returns `ResolutionResponse`. Handles critical issues gracefully (e.g., forces escalation for High priority even if LLM missed it).
- `POST /resolve/quick` — Shorthand that accepts raw `ClassifierOutput` directly, wraps it in `ResolveRequest` with defaults, delegates to `/resolve`.
- `POST /reply/email-html` — Takes a `ResolutionResponse` and generates a solv.ai branded HTML email. Validates input length, checks for prompt injection, builds the HTML, optionally persists to disk. Returns `EmailReplyHtmlResponse`.

**Why it matters:** This is the entry point for all external traffic. It orchestrates the entire resolution pipeline from input validation through LLM generation to structured output.

---

#### `run_server.py` — Entry Point

**Purpose:** Minimal bootstrap script that starts the Uvicorn ASGI server.

**How it works:** Calls `uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True, log_level="info")`. The `reload=True` enables hot-reloading during development.

**Why it matters:** Single-command startup: `python run_server.py`.

---

#### `requirements.txt` — Root Dependencies

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
openai==1.51.0
pydantic>=2.0.0
httpx>=0.27.0
langsmith>=0.1.0
```

---

### Comparative Analysis Files

#### `comparative_analysis/__init__.py`

**Purpose:** Marks the directory as a Python package. Contains a 3-line comment identifying it as the Comparative Analysis / Ablation Study for SOLV.ai, comparing 10 LLM models via OpenCode/OpenRouter for wellness-industry complaint management.

---

#### `comparative_analysis/config.py` — Ablation Study Configuration

**Purpose:** Centralized configuration for the ablation study, including API keys for multiple providers, model definitions, and evaluation settings.

**Path management:**
- `BASE_DIR` — Points to `comparative_analysis/`.
- `GENAI_DIR` — Points to parent `genai/`.
- `RESULTS_DIR` — `comparative_analysis/results/`.
- `GRAPHS_DIR` — `comparative_analysis/graphs/`.
- `_load_local_env()` — Loads `genai/.env` into process environment (no-overwrite).

**API Key resolution (fallback chain):**
- `OPENCODE_API_KEY` — Checks `OPENCODE_API_KEY`, `OPENCODE_GO_API_KEY`, `OPENROUTER_API_KEY`.
- `GROQ_API_KEY` — Checks `LLM_API_KEY`, `GROQ_API_KEY`.
- `GOOGLE_API_KEY` — Checks `GOOGLE_API_KEY`.
- `HUGGINGFACE_API_KEY` — Checks `HUGGINGFACE_API_KEY`.
- `OPENCODE_BASE_URL` — Checks `OPENCODE_BASE_URL`, `OPENCODE_GO_BASE_URL`, `OPENROUTER_BASE_URL`, defaults to `https://opencode.ai/zen/go/v1`.

**Model definitions (10 models across 4 providers):**

| Key | Provider | Model ID | Display Name |
|-----|----------|----------|-------------|
| `groq_llama70b` | groq | `llama-3.3-70b-versatile` | Llama 3.3 70B (Groq) |
| `gemini_2_5_flash` | google | `models/gemini-2.5-flash` | Gemini 2.5 Flash (Google) |
| `hf_qwen_72b` | huggingface | `Qwen/Qwen2.5-72B-Instruct` | Qwen 2.5 72B (HuggingFace) |
| `glm_5` | openrouter | `glm-5` | GLM 5 (Zhipu) |
| `glm_5_1` | openrouter | `glm-5.1` | GLM 5.1 (Zhipu) |
| `mimo_v2_omni` | openrouter | `mimo-v2-omni` | MiMo V2 Omni (Xiaomi) |
| `mimo_v2_pro` | openrouter | `mimo-v2-pro` | MiMo V2 Pro (Xiaomi) |
| `minimax_m2_5` | openrouter | `minimax-m2.5` | MiniMax M2.5 |
| `minimax_m2_7` | openrouter | `minimax-m2.7` | MiniMax M2.7 |
| `qwen3_5_plus` | openrouter | `qwen3.5-plus` | Qwen 3.5 Plus (Alibaba) |

**Evaluation settings:** `TEMPERATURE` (0.3), `MAX_TOKENS` (2048), `RETRY_ATTEMPTS` (2), `RETRY_DELAY_SECONDS` (5).

**Why it matters:** This is the single configuration hub for the entire ablation study. Adding a new model requires only adding an entry to the `MODELS` dict.

---

#### `comparative_analysis/model_clients.py` — Unified Model Client Wrappers

**Purpose:** Provides a common interface (`generate()` → dict) for all LLM providers, handling API differences transparently.

**`BaseLLMClient` (abstract base):**
- Common interface with `model_id`, `display_name`, `api_key`.
- `generate()` — Abstract method returning dict with `response`, `latency_seconds`, `input_tokens`, `output_tokens`, `error`.
- `health_check()` — Abstract method returning `{"ok": bool, "message": str}`.
- `_retry_generate()` — Retry wrapper with exponential backoff (5s, 10s delays).

**`OpenAICompatibleClient` (OpenCode/OpenRouter/Groq):**
- Works with any OpenAI-compatible endpoint.
- Handles two API formats: `/chat/completions` (standard OpenAI format with `messages` array including system role) and `/messages` (Anthropic-compatible format with separate `system` field).
- Sets headers: `Authorization`, `X-API-Key`, `anthropic-version`, `Content-Type`, plus `HTTP-Referer` and `X-Title` for OpenRouter tracking.
- Parses response differently based on endpoint: `/messages` extracts from `content` array, `/chat/completions` extracts from `choices[0].message.content`.

**`GeminiClient` (Google):**
- Uses `google-generativeai` SDK.
- Configures model with `system_instruction` and `GenerationConfig` (temperature, max_output_tokens).
- Extracts token counts from `usage_metadata` (`prompt_token_count`, `candidates_token_count`).

**`HuggingFaceClient` (HF Inference API):**
- Uses `https://router.huggingface.co/v1/chat/completions` endpoint.
- Standard OpenAI-compatible format.
- Health check treats HTTP 503 (model loading) as "key valid."

**`create_client()` factory:**
- Routes to the appropriate client class based on `provider` field in model config.
- For `openrouter`/`opencode`/`groq`, optionally prepends `OPENCODE_MODEL_PREFIX` to model ID.

**Why it matters:** This abstraction allows the ablation study to benchmark models across 4 different providers (Groq, Google, HuggingFace, OpenRouter) with a single unified call interface.

---

#### `comparative_analysis/prompts.py` — Task-Specific Prompts

**Purpose:** Defines system and user prompts for all 3 ablation study tasks: Classify, Resolve, and Ticket.

**Task 1: Classify**
- `SYSTEM_PROMPT_CLASSIFY` — Defines 3 complaint categories (Product, Packaging, Trade) with detailed descriptions, 3 priority levels (High, Medium, Low) with criteria, SLA guidelines (4h/24h/72h), and forces JSON output with fields: `category`, `priority`, `justification`, `keywords`, `sla_hours`, `confidence`.
- `USER_PROMPT_CLASSIFY` — Injects `channel`, `received_at`, `customer_name`, `product_name`, `complaint_text`.

**Task 2: Resolve**
- `SYSTEM_PROMPT_RESOLVE` — Defines resolution guidelines: immediate action (15 min), role-tagged resolution steps, mandatory escalation for High priority, empathetic customer communication draft, SLA mapping. Forces JSON with fields: `immediate_action`, `resolution_steps`, `assigned_team`, `escalation_required`, `follow_up_required`, `follow_up_timeline`, `customer_communication`, `estimated_resolution_time`.
- `USER_PROMPT_RESOLVE` — Injects `category`, `priority`, `channel`, `customer_name`, `product_name`, `complaint_text`.

**Task 3: Ticket**
- `SYSTEM_PROMPT_TICKET` — Forces JSON support ticket with fields: `title` (max 100 chars), `category`, `priority`, `description` (2-4 sentences), `root_cause_hypothesis`, `recommended_actions`, `assigned_team`, `sla_deadline_hours`, `tags`, `status` ("Open").
- `USER_PROMPT_TICKET` — Injects `channel`, `received_at`, `customer_name`, `product_name`, `complaint_text`.

**Why it matters:** Each task has a purpose-built prompt that forces the LLM into a specific output schema, enabling automated evaluation against ground truth.

---

#### `comparative_analysis/test_scenarios.py` — Test Scenario Definitions

**Purpose:** Defines 4 realistic wellness-industry customer complaints covering all category/priority combinations, plus prompt builders and test case generators.

**4 Scenarios:**

| ID | Scenario | Category | Priority | Channel |
|----|----------|----------|----------|---------|
| CPL-001 | Severe allergic reaction to collagen supplement (Priya Sharma) | Product | High | Email |
| CPL-002 | Immunity tablets ineffective, colour change noticed (Rajesh Kumar) | Product | Medium | Call Centre |
| CPL-003 | Fish oil capsules arrive with broken tamper seal (Sneha Patel) | Packaging | Medium | Email |
| CPL-004 | Pharmacy chain bulk pricing & distribution inquiry (HealthPlus Pharmacy) | Trade | Low | Email |

Each scenario includes: `scenario_id`, `category`, `priority`, `channel`, `received_at`, `customer_name`, `product_name`, and a detailed `complaint_text` (100-200 words of realistic complaint content).

**Prompt builders:**
- `build_classify_prompts()` — Returns (system, user) prompt tuple for classification.
- `build_resolve_prompts()` — Returns (system, user) prompt tuple for resolution.
- `build_ticket_prompts()` — Returns (system, user) prompt tuple for ticket generation.

**`get_all_test_cases()`:**
- Generates 12 test case dicts (4 scenarios × 3 tasks), each with: `task`, `scenario_name`, `category`, `priority`, `system_prompt`, `user_prompt`.

**Why it matters:** These scenarios are the ground truth against which all 10 models are evaluated. They cover the full spectrum of complaint types the production system will encounter.

---

#### `comparative_analysis/evaluate.py` — 5-Metric Scoring Engine

**Purpose:** Scores each model response on 5 weighted dimensions relevant to the complaint classification and resolution use case.

**Constants:**
- `VALID_CATEGORIES` — `{"product", "packaging", "trade"}`
- `VALID_PRIORITIES` — `{"high", "medium", "low"}`
- `PRIORITY_PROXIMITY` — Partial credit matrix: exact match = 1.0, adjacent level = 0.5, skip level = 0.0.
- `RESOLUTION_KEYWORDS` — 25 keywords indicating actionable resolution language (replace, refund, escalate, investigate, etc.).
- `REQUIRED_FIELDS` — Per-task required JSON field sets.
- `WEIGHTS` — classification_accuracy (30%), priority_accuracy (25%), resolution_quality (25%), format_compliance (10%), response_quality (10%).

**`_extract_json()` — JSON extraction helper:**
- Strips markdown fences, attempts direct parse, falls back to first `{...}` block.

**Metric 1: `score_format_compliance()`**
- 0.4 points for valid JSON + up to 0.6 points for required fields present (proportional to field coverage).
- Returns score, `valid_json` bool, `has_required_fields` bool, and details.

**Metric 2: `score_classification_accuracy()`**
- Binary: 1.0 if category matches expected, 0.0 otherwise.
- N/A for resolve task (auto-scores 1.0).

**Metric 3: `score_priority_accuracy()`**
- 1.0 for exact match, 0.5 for adjacent level, 0.0 otherwise.
- Uses `PRIORITY_PROXIMITY` lookup table.
- N/A for resolve task (auto-scores 1.0).

**Metric 4: `score_resolution_quality()`**
- For resolve task: 6 checks — has immediate action, has 3+ steps, uses action verbs, has customer message (>20 chars), has resolution timeline, escalation logic correct.
- For ticket task: 7 checks — has title, has description (>30 chars), has root cause, has 2+ actions, actions actionable, has assigned team, has SLA deadline.
- Score = passed / total checks.
- N/A for classify task (auto-scores 1.0).

**Metric 5: `score_response_quality()`**
- Penalizes refusals ("i cannot", "as an ai", etc.), too short (<30 words), or excessively long (>2000 words).
- Score = max(0.0, 1.0 - issues × 0.35).

**`evaluate_response()` — Aggregate scorer:**
- Runs all 5 metrics, computes weighted sum, returns dict with `overall_score` and per-metric detail dicts plus `latency_seconds`.

**Why it matters:** This is the core evaluation engine that determines which model wins. The weighted scoring system balances accuracy, quality, and format compliance to produce a fair, multi-dimensional ranking.

---

#### `comparative_analysis/run_ablation.py` — Main Ablation Study Runner

**Purpose:** Orchestrates the full benchmark: runs all test cases across all models, evaluates each response, and saves raw results.

**`_get_selected_models()`:**
- Optionally filters models via `RUN_MODEL_KEYS` environment variable (comma-separated keys). If not set, runs all models.

**`_merge_with_latest()`:**
- When `MERGE_WITH_LATEST=1`, merges current run results into `ablation_results_latest.json`, allowing incremental model additions without re-running everything.

**`run_ablation()` main loop:**
1. Creates `RESULTS_DIR` if needed.
2. Gets test cases (12 per model) and selected models.
3. For each model:
   - Creates client via factory.
   - Runs health check; skips model if failed.
   - For each test case (12):
     - Calls `client.generate()` with system + user prompts.
     - On error: scores all metrics as 0.0.
     - On success: runs `evaluate_response()` and prints score/latency/tokens.
     - Sleeps 1.5s between calls (rate-limit buffer).
   - Sleeps 3s before next model.
4. Saves results to timestamped JSON and `ablation_results_latest.json`.
5. Prints summary table with overall score, latency, and per-metric averages.

**Why it matters:** This is the orchestrator that executes the entire benchmark. It handles errors gracefully, respects rate limits, and produces the raw data that feeds into report generation.

---

#### `comparative_analysis/generate_report.py` — Graph Generation + Markdown Report

**Purpose:** Reads `ablation_results_latest.json`, generates 8 comparative visualization graphs as PNGs, and produces the `ABLATION_REPORT.md` markdown file.

**Helpers:**
- `load_results()` — Loads latest results JSON, exits with error if not found.
- `get_model_metrics()` — Aggregates per-metric averages for every model, including per-task breakdowns.

**8 Graph generators:**

1. `plot_overall_scores()` — Horizontal bar chart of average overall scores (0-100%), with 70% threshold line.
2. `plot_radar_chart()` — Polar radar chart comparing all 5 metrics across all models.
3. `plot_latency()` — Horizontal bar chart of average response latency in seconds.
4. `plot_per_task_scores()` — Grouped bar chart showing classify/resolve/ticket scores per model.
5. `plot_score_vs_latency()` — Scatter plot: quality vs speed (top-left = best).
6. `plot_metric_heatmap()` — Color-coded heatmap (RdYlGn colormap) of all 5 metrics × all models.
7. `plot_token_usage()` — Grouped bar chart of input vs output tokens per model.
8. `plot_category_priority_accuracy()` — Dual-panel grouped bar chart showing classification and priority accuracy per scenario.

**`generate_markdown_report()`:**
- Builds a complete markdown document with: models evaluated table, evaluation criteria, test scenarios, overall rankings (with medals), all 8 graph embeds, per-task breakdown tables, detailed metric scores, recommendation section, and reproduction instructions.
- Saves to `ABLATION_REPORT.md`.

**`main()`:**
- Entry point that calls all 8 graph generators and the markdown report generator in sequence.

**Why it matters:** Transforms raw JSON benchmark data into publication-ready visualizations and a comprehensive written report, enabling data-driven model selection decisions.

---

#### `comparative_analysis/test_api_keys.py` — Pre-flight API Key Verification

**Purpose:** Tests all configured API keys before running the ablation study to catch connectivity issues early.

**How it works:**
- Iterates through all models in `MODELS` config.
- For each model: displays provider, model ID, masked API key.
- Creates client, runs health check.
- Treats HTTP 429 (rate-limited) as "key valid but temporarily throttled."
- Sleeps 4s between checks to avoid rate limiting.
- Prints summary: count of connected models, list of failed models.

**Why it matters:** Saves 10-15 minutes of wasted ablation run time by catching missing/invalid API keys upfront.

---

#### `comparative_analysis/test_gemini.py` — Standalone Gemini vs Groq Comparison

**Purpose:** Independent test script comparing Google Gemini models against Groq Llama 3.3 70B using a solar-plant diagnostic prompt (LUMIN.AI use case).

**How it works:**
- Tests Gemini models in order: `gemini-2.0-flash`, `gemini-2.5-flash`, `gemma-3-27b-it` (falls through on quota exhaustion).
- Tests Groq `llama-3.3-70b-versatile` as baseline.
- Uses a solar inverter prediction prompt with SHAP feature importance data.
- Compares latency and outputs a speed ratio.

**Why it matters:** This was an early exploration script used to evaluate Gemini as a candidate before it was integrated into the main ablation study. It demonstrates the cross-provider testing methodology.

---

#### `comparative_analysis/run_additional_three_models.py` — Incremental Model Addition Runner

**Purpose:** Runs only 3 specific models (Groq Llama 70B, Gemini 2.5 Flash, Qwen 2.5 72B) and merges results with existing `ablation_results_latest.json`.

**How it works:**
- Sets `RUN_MODEL_KEYS=groq_llama70b,gemini_2_5_flash,hf_qwen_72b`.
- Sets `MERGE_WITH_LATEST=1`.
- Calls `run_ablation()` then `generate_report()`.

**Why it matters:** Enables incremental benchmark expansion without re-running all models. Useful when new models are added to the study after the initial run.

---

#### `comparative_analysis/requirements.txt` — Ablation Study Dependencies

```
google-generativeai>=0.8.0
matplotlib>=3.8.0
numpy>=1.26.0
requests>=2.31.0
openai>=1.51.0
```

---

## Quick Start

### 1. Install dependencies

```bash
cd genai
pip install -r requirements.txt
pip install -r comparative_analysis/requirements.txt
```

### 2. Configure environment

Add your API keys to `genai/.env`:

```bash
# Required
LLM_API_KEY=gsk_your_groq_api_key_here

# Optional — LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_your_langsmith_key_here
LANGCHAIN_PROJECT=genai-resolution-service
```

### 3. Start the server

```bash
python run_server.py
```

The service starts on `http://localhost:8001`. Visit `http://localhost:8001/docs` for the interactive Swagger UI.

### 4. Test with a sample request

```bash
curl -X POST http://localhost:8001/resolve/quick \
  -H "Content-Type: application/json" \
  -d '{
    "complaint_id": 1,
    "text": "Box was broken",
    "category": "Packaging",
    "sentiment_score": -0.4767,
    "priority": "High",
    "latency_ms": 206.8
  }'
```

---

## API Endpoints

### GET /health

Health check endpoint. Returns service status, LLM connectivity, and upstream NLP service URL.

**Response (200):**
```json
{
  "status": "healthy",
  "llm_connected": true,
  "nlp_service_url": "http://localhost:8000",
  "version": "1.0.0"
}
```

### POST /resolve

Primary endpoint. Accepts classified complaint data with optional customer metadata and returns a full AI-generated resolution plan.

**Request Body:**
```json
{
  "classifier_output": { "complaint_id": 2, "text": "...", "category": "Product", "sentiment_score": -0.8, "priority": "High", "latency_ms": 150.3 },
  "customer_name": "Rahul Sharma",
  "channel": "email",
  "product_name": "Omega-3 Fish Oil Capsules"
}
```

**Response (200):** Full `ResolutionResponse` with 17 fields including empathetic customer message, role-tagged resolution steps, SLA deadline, root cause hypothesis, and metadata.

### POST /resolve/quick

Shorthand endpoint — accepts raw `ClassifierOutput` directly. Uses defaults for `customer_name` ("Valued Customer"), `channel` ("web"), `product_name` ("Wellness Product").

### POST /reply/email-html

Turns the JSON from `POST /resolve` into a black & orange solv.ai HTML email document. No extra LLM call — the email content comes from the resolution payload.

**Request Body:**
```json
{
  "resolution": { ... ResolutionResponse object ... },
  "customer_name": "Priya Sharma",
  "subject": "Re: Your complaint #1",
  "persist_file": true
}
```

---

## Request & Response Schemas

### ClassifierOutput (Input from NLP service)

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `complaint_id` | `int | str` | Yes | — | Unique complaint identifier |
| `text` | `str` | Yes | 1-2000 chars | Original complaint text |
| `category` | `str` | Yes | `Product | Packaging | Trade` | NLP-classified category |
| `sentiment_score` | `float` | Yes | -1.0 to 1.0 | VADER sentiment score |
| `priority` | `str` | Yes | `High | Medium | Low` | NLP-assigned priority |
| `latency_ms` | `float` | No | >= 0 | NLP inference latency |

### ResolutionResponse (Output)

| Field | Type | Description |
|-------|------|-------------|
| `complaint_id` | `int | str` | Echoed from input |
| `original_text` | `str` | Original complaint text |
| `category` | `str` | Complaint category |
| `priority` | `str` | Priority level |
| `sentiment_score` | `float` | Sentiment score |
| `customer_response` | `str` | AI-generated empathetic customer-facing message |
| `immediate_action` | `str` | What support executive must do within 15 minutes |
| `resolution_steps` | `list[str]` | Role-tagged ordered action steps |
| `assigned_team` | `str` | Primary responsible team |
| `escalation_required` | `bool` | Whether escalation to senior management is needed |
| `follow_up_required` | `bool` | Whether follow-up is needed |
| `follow_up_timeline` | `str` | When to follow up (e.g., "24 hours") |
| `estimated_resolution_time` | `str` | Expected time to resolve |
| `root_cause_hypothesis` | `str` | AI-generated root cause analysis |
| `sla_deadline_hours` | `int` | SLA deadline (4/24/72 hours) |
| `status` | `str` | Complaint status (Open/Escalated) |
| `confidence` | `str` | AI confidence level (high/medium/low) |
| `model_used` | `str` | LLM model that generated the response |
| `genai_latency_ms` | `float` | End-to-end GenAI processing time |

---

## Prompt Engineering

The system uses a two-part prompt architecture defined in `prompts.py`:

### System Prompt (`SYSTEM_PROMPT_RESOLVE`)

Defines the AI's role, domain context, and strict behavioral rules:

- **Domain grounding** — Wellness company context (supplements, vitamins, omega-3)
- **Category-specific resolution guidelines** — Different strategies for Product vs Packaging vs Trade
- **Priority-based escalation matrix** — High=mandatory escalation, Medium=conditional, Low=standard
- **Sentiment-aware tone calibration:**

| Sentiment Range | Tone |
|-----------------|------|
| < -0.5 | Extremely apologetic, offer compensation/goodwill gesture |
| -0.5 to -0.2 | Sincerely apologetic, reassure with concrete steps |
| -0.2 to 0.0 | Professional and empathetic |
| > 0.0 | Helpful and informative |

- **Anti-hallucination rules** — Never fabricate details not in the input
- **Strict JSON output schema** — Forces structured, parseable output

### User Prompt (`USER_PROMPT_RESOLVE`)

Injects all complaint-specific data via format placeholders.

### LLM Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Model | `llama-3.3-70b-versatile` | Winner from 10-model ablation study |
| Provider | Groq | Fastest inference for Llama models |
| Temperature | 0.25 | Low = deterministic, consistent output |
| Max Tokens | 2048 | Sufficient for detailed resolutions |

---

## Security & Guardrails

The service implements a 4-layer security architecture in `guardrails.py`:

### Layer 1: Input Sanitization

- **HTML escaping** — Prevents XSS via complaint text
- **Control character stripping** — Removes null bytes and non-printable chars
- **Length truncation** — Max 2000 characters (configurable)
- **Field validation** — Category, priority, sentiment checked against allowed values

### Layer 2: Prompt Injection Detection

13 regex patterns detect common injection attempts:

```
- "ignore all previous instructions"
- "disregard previous"
- "you are now"
- "act as if"
- "pretend you"
- "system prompt"
- "override instructions"
- "<script" / "javascript:" / "on*="
```

Requests matching any pattern are rejected with HTTP 400.

### Layer 3: Output Validation

Cross-checks LLM output against input data:

- **Required fields** — All 9 resolution fields must be present
- **Team validation** — `assigned_team` must be a known team
- **Escalation enforcement** — High priority forces `escalation_required: true`
- **Step validation** — `resolution_steps` must be a non-empty list
- **Response quality** — `customer_response` must be at least 20 characters

### Layer 4: Safe JSON Parsing

Robust extraction handles:
- Direct JSON parsing
- JSON inside ` ```json ... ``` ` markdown fences
- First `{...}` block extraction as fallback

### Additional Security

| Measure | Implementation |
|---------|---------------|
| **Rate limiting** | Sliding-window per-IP, 60 req/min (configurable) |
| **API key auth** | Optional Bearer token via `GENAI_API_KEY` env var |
| **CORS** | Configurable origins (default: `*` for dev) |
| **Input length limits** | Pydantic max_length on all string fields |
| **No PII logging** | Customer data is never logged at INFO level |

---

## Observability (LangSmith)

The service integrates with [LangSmith](https://smith.langchain.com/) for full LLM observability.

### Setup

1. Install the dependency (included in `requirements.txt`):
   ```bash
   pip install langsmith
   ```

2. Add your LangSmith API key to `genai/.env`:
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=lsv2_pt_your_key_here
   LANGCHAIN_PROJECT=genai-resolution-service
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   ```

3. Restart the server. You'll see in the logs:
   ```
   LangSmith tracing enabled — wrapping OpenAI client
   ```

### What Gets Traced

Every LLM call is automatically traced with:

| Data | Description |
|------|-------------|
| **Full system prompt** | The complete system prompt sent to the LLM |
| **Full user prompt** | The constructed user prompt with complaint data |
| **Complete LLM output** | Raw response from the model |
| **Token counts** | Prompt tokens + completion tokens |
| **Latency** | Time from request to response |
| **Model info** | Model name, provider, temperature |
| **Success/error status** | Whether the call succeeded |

### Local Logging Fallback

When LangSmith is not configured, every LLM call is still logged as structured JSON to stdout.

---

## SLA Management

SLA deadlines are automatically assigned based on priority:

| Priority | Response SLA | Resolution SLA | Escalation |
|----------|-------------|----------------|------------|
| **High** | 1 hour | 4 hours | Mandatory — immediate to senior management |
| **Medium** | 4 hours | 24 hours | If unresolved within 12 hours |
| **Low** | 24 hours | 72 hours | Only if complaint is repeated |

The `sla_deadline_hours` field in the response reflects the resolution SLA. The `status` field is automatically set to `"Escalated"` when `escalation_required` is true.

---

## Configuration Reference

All configuration is managed via environment variables in `genai/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | (required) | Groq API key |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | LLM model ID |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | LLM provider base URL |
| `LLM_TEMPERATURE` | `0.25` | Generation temperature |
| `LLM_MAX_TOKENS` | `2048` | Max output tokens |
| `NLP_SERVICE_URL` | `http://localhost:8000` | Upstream NLP classifier URL |
| `GENAI_HOST` | `0.0.0.0` | Server bind host |
| `GENAI_PORT` | `8001` | Server bind port |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `GENAI_API_KEY` | (empty) | Optional Bearer token for auth |
| `RATE_LIMIT_RPM` | `60` | Max requests per minute per IP |
| `MAX_COMPLAINT_LENGTH` | `2000` | Max complaint text length |
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | (empty) | LangSmith API key |
| `LANGCHAIN_PROJECT` | `genai-resolution-service` | LangSmith project name |
| `LANGCHAIN_ENDPOINT` | `https://api.smith.langchain.com` | LangSmith endpoint |
| `REPLY_EMAIL_OUTPUT_DIR` | `generated_emails` | Output directory for HTML reply emails |

---

## Integration with NLP Classifier

### Full Pipeline Flow

```bash
# Step 1: Classify the complaint (NLP service on port 8000)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"complaint_id": 1, "text": "Box was broken"}'

# Step 2: Pipe the output directly to the GenAI service (port 8001)
curl -X POST http://localhost:8001/resolve/quick \
  -H "Content-Type: application/json" \
  -d '{
    "complaint_id": 1,
    "text": "Box was broken",
    "category": "Packaging",
    "sentiment_score": -0.4767,
    "priority": "High",
    "latency_ms": 206.8
  }'
```

---

## Error Handling

| HTTP Code | Error | Cause |
|-----------|-------|-------|
| `400` | `input_validation_failed` | Invalid category/priority/sentiment, prompt injection detected, text too short |
| `401` | `Missing Authorization header` | API key required but not provided |
| `403` | `Invalid API key` | API key provided but incorrect |
| `422` | Validation Error | Pydantic schema validation failed (FastAPI auto) |
| `429` | `rate_limited` | Too many requests from this IP |
| `502` | `llm_output_parse_error` | LLM returned non-JSON response |
| `503` | `llm_unavailable` | LLM provider is down or unresponsive |

All error responses follow a consistent format:
```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "violations": ["detail1", "detail2"]
}
```

---

## Example Scenarios

### Scenario 1: Packaging / High Priority / Negative Sentiment

**Input:**
```json
{
  "complaint_id": 1,
  "text": "Box was broken",
  "category": "Packaging",
  "sentiment_score": -0.4767,
  "priority": "High",
  "latency_ms": 206.8
}
```

**Result:** Escalated to senior management, 4h SLA, logistics team arranges re-shipment, QA inspects warehouse procedures.

### Scenario 2: Product / High Priority / Very Negative Sentiment

**Input:**
```json
{
  "complaint_id": 2,
  "text": "Product stopped working after just 2 days. This is completely unacceptable quality!",
  "category": "Product",
  "sentiment_score": -0.8,
  "priority": "High",
  "latency_ms": 150.3
}
```

**Result:** Extremely apologetic tone (sentiment < -0.5), replacement/refund offered, QA investigation triggered, batch records checked, 4h SLA.

### Scenario 3: Trade / Low Priority / Neutral Sentiment

**Input:**
```json
{
  "complaint_id": 3,
  "text": "Need bulk order details for vitamin supplements",
  "category": "Trade",
  "sentiment_score": 0.0,
  "priority": "Low",
  "latency_ms": 98.5
}
```

**Result:** Helpful and informative tone, routed to Sales team, pricing/availability info provided, 72h SLA, no escalation.

---

## Ablation Study — Comparative Analysis

The `comparative_analysis/` directory contains a complete LLM benchmarking framework that evaluated **10 models** across **4 complaint scenarios** and **3 tasks** (120 total API calls) to determine the best model for production deployment.

### Models Evaluated

| # | Model | Provider | Model ID |
|---|-------|----------|----------|
| 1 | **GLM 5 (Zhipu)** | openrouter | `glm-5` |
| 2 | **GLM 5.1 (Zhipu)** | openrouter | `glm-5.1` |
| 3 | **MiMo V2 Omni (Xiaomi)** | openrouter | `mimo-v2-omni` |
| 4 | **MiMo V2 Pro (Xiaomi)** | openrouter | `mimo-v2-pro` |
| 5 | **MiniMax M2.5** | openrouter | `minimax-m2.5` |
| 6 | **MiniMax M2.7** | openrouter | `minimax-m2.7` |
| 7 | **Qwen 3.5 Plus (Alibaba)** | openrouter | `qwen3.5-plus` |
| 8 | **Llama 3.3 70B (Groq)** | groq | `llama-3.3-70b-versatile` |
| 9 | **Gemini 2.5 Flash (Google)** | google | `models/gemini-2.5-flash` |
| 10 | **Qwen 2.5 72B (HuggingFace)** | huggingface | `Qwen/Qwen2.5-72B-Instruct` |

All models accessed via OpenCode / OpenRouter (OpenAI-compatible API) except Groq (direct), Google (google-generativeai SDK), and HuggingFace (router endpoint).

### Test Scenarios

| Scenario | Category | Priority | Channel | Description |
|----------|----------|----------|---------|-------------|
| CPL-001: Allergic Reaction | Product | **High** | Email | Severe allergic reaction to collagen supplement with ER visit |
| CPL-002: Product Efficacy | Product | Medium | Call Centre | Immunity tablets ineffective, colour change noticed |
| CPL-003: Packaging Damage | Packaging | Medium | Email | Fish oil capsules with broken tamper seal |
| CPL-004: Trade Inquiry | Trade | Low | Email | Pharmacy chain bulk pricing & distribution inquiry |

Each scenario is tested on **3 tasks** (classify / resolve / ticket) → **12 API calls per model**, **120 total API calls**.

### Evaluation Metrics

| Metric | Weight | What it measures |
|--------|--------|-----------------|
| **Classification Accuracy** | 30% | Correct complaint category (Product / Packaging / Trade) |
| **Priority Accuracy** | 25% | Correct urgency level (High / Medium / Low); adjacent = 50% credit |
| **Resolution Quality** | 25% | Completeness & actionability of resolution steps / ticket |
| **Format Compliance** | 10% | Valid JSON with all required schema fields |
| **Response Quality** | 10% | Appropriate length, no refusals, coherent output |

### Graph Explanations

All 8 graphs are generated by `comparative_analysis/generate_report.py` from the raw JSON results in `comparative_analysis/results/ablation_results_latest.json`. Each graph serves a specific analytical purpose in the model selection process.

#### Graph 1: Overall Score Comparison

**File:** `graphs/01_overall_scores.png`

**What it shows:** A horizontal bar chart ranking all 10 models by their average overall score (0-100%). The overall score is the weighted sum of all 5 evaluation metrics. A dashed gray line marks the 70% quality threshold.

**Why it matters:** This is the primary ranking visualization. It immediately identifies which models meet the production quality bar. Models above 70% are viable candidates; models below are disqualified. The color-coded bars use a distinct palette for each model, making it easy to track performance across all visualizations.

**Key insight from results:** Llama 3.3 70B (Groq) and Qwen 2.5 72B (HuggingFace) tie at 96.9%, followed by MiniMax M2.5 at 96.0%. The bottom performers (MiMo V2 Omni at 32.4%, GLM 5.1 at 45.4%) fail to produce valid JSON consistently.

---

#### Graph 2: Multi-Metric Radar Comparison

**File:** `graphs/02_radar_comparison.png`

**What it shows:** A polar radar chart with 5 axes (Category Accuracy, Priority Accuracy, Resolution Quality, Format Compliance, Response Quality). Each model is plotted as a colored polygon — the larger the area, the better the model performs across all dimensions simultaneously.

**Why it matters:** The overall score can mask weaknesses in specific areas. The radar chart reveals multi-dimensional performance profiles. A model with a high overall score but a "dent" in one axis has a specific weakness that could be problematic in production. For example, a model might have perfect format compliance but poor resolution quality — it produces valid JSON but with useless content.

**Reading the chart:** Ideal models have polygons that extend to the outer edge (1.0) on all axes. Asymmetric shapes indicate uneven performance. Overlapping polygons show models with similar profiles.

---

#### Graph 3: Latency Comparison

**File:** `graphs/03_latency_comparison.png`

**What it shows:** A horizontal bar chart of average response latency in seconds across all 12 API calls per model. Lower is better.

**Why it matters:** Real-time complaint intake requires sub-5-second responses (SOLV.ai SLA requirement). A model with 96.9% accuracy but 50-second latency is unusable for real-time processing, even if it produces better quality output. This graph identifies which models meet the latency constraint.

**Key insight from results:** Llama 3.3 70B (Groq) dominates at 1.4s average — 10x faster than most competitors. Qwen 3.5 Plus at 51.7s is disqualified despite decent quality. Gemini 2.5 Flash at 7.4s is viable but borderline.

---

#### Graph 4: Per-Task Breakdown

**File:** `graphs/04_per_task_scores.png`

**What it shows:** A grouped bar chart with 3 groups (Classify, Resolve, Ticket Generation). Within each group, bars represent each model's average score for that specific task.

**Why it matters:** Some models excel at classification but fail at ticket generation, or vice versa. This graph reveals task-specific strengths and weaknesses. For the SOLV.ai pipeline, all 3 tasks matter — the model must perform well across the board, not just in one area.

**Key insight from results:** Top models (Llama 3.3 70B, Qwen 2.5 72B, MiniMax M2.5) score near 100% on Classify and Resolve but drop slightly on Ticket Generation (90.6%). Bottom models collapse completely on Ticket Generation (0-3.4%), indicating they cannot produce structured support tickets.

---

#### Graph 5: Score vs Latency

**File:** `graphs/05_score_vs_latency.png`

**What it shows:** A scatter plot with latency on the X-axis (seconds) and overall score on the Y-axis (percentage). Each model is a labeled point. The top-left corner represents the ideal: high score, low latency.

**Why it matters:** This is the **efficiency frontier** visualization. It combines quality and speed into a single view, making it trivial to identify the Pareto-optimal models. Any model in the bottom-right quadrant (low score, high latency) is strictly dominated and should never be selected.

**Reading the chart:** Draw an imaginary line from top-left to bottom-right. Models closest to the top-left corner offer the best quality-speed tradeoff. Models in the top-right are high-quality but too slow. Models in the bottom-left are fast but low-quality.

**Key insight from results:** Llama 3.3 70B (Groq) sits in the top-left corner — best score AND fastest. Qwen 2.5 72B is top-right — same score but 8x slower. MiMo V2 Omni is bottom-middle — slow AND low-quality (worst of both worlds).

---

#### Graph 6: Metric Heatmap

**File:** `graphs/06_metric_heatmap.png`

**What it shows:** A color-coded matrix with models as rows and 5 metrics as columns. Green cells indicate strong performance, red cells indicate weak performance, yellow is moderate. Each cell displays the exact percentage.

**Why it matters:** The heatmap provides an at-a-glance comparison of all metrics across all models. It's the densest information visualization — you can see every metric score for every model in a single glance. The color gradient (RdYlGn colormap) makes patterns immediately visible: vertical bands of red indicate metrics that all models struggle with; horizontal bands of red indicate models that fail across the board.

**Reading the chart:** Green = good (>75%), yellow = moderate (35-75%), red = poor (<35%). White text on dark cells and black text on light cells ensures readability.

**Key insight from results:** Top models show a solid green row across all 5 metrics. Bottom models show predominantly red rows. Format Compliance is the most discriminating metric — it separates models that can follow JSON instructions from those that cannot.

---

#### Graph 7: Token Usage

**File:** `graphs/07_token_usage.png`

**What it shows:** A grouped bar chart with two bars per model: input tokens (blue) and output tokens (red). Shows the average tokens consumed per API call.

**Why it matters:** Token usage directly correlates with cost and rate limits. Models that consume more tokens per call are more expensive to run at scale. Input tokens reflect prompt size (mostly constant across models for the same task), while output tokens reflect verbosity — models that generate unnecessarily long responses waste tokens and increase latency.

**Key insight from results:** Input tokens are relatively consistent across models (same prompts), but output tokens vary significantly. Models that produce empty or truncated responses show near-zero output tokens (but also score 0 on quality). The ideal model uses moderate output tokens — enough to be thorough, not so many as to be wasteful.

---

#### Graph 8: Scenario Accuracy

**File:** `graphs/08_scenario_accuracy.png`

**What it shows:** A dual-panel grouped bar chart. Left panel shows category classification accuracy per scenario (Allergic Reaction, Product Quality, Packaging Damage, Trade Inquiry). Right panel shows priority assignment accuracy per scenario.

**Why it matters:** This graph reveals whether models perform consistently across different complaint types or have scenario-specific weaknesses. A model might correctly classify all Product complaints but fail on Trade inquiries. This is critical for production because real-world complaints arrive in unpredictable distributions — the model must handle all types reliably.

**Reading the chart:** Each scenario is a group of bars (one per model). The left panel tests whether the model identified the correct category (Product/Packaging/Trade). The right panel tests whether it assigned the correct priority (High/Medium/Low). 100% means perfect accuracy; 0% means complete failure.

**Key insight from results:** Top models achieve 100% category accuracy across all 4 scenarios. Bottom models show erratic performance — they might correctly classify the Allergic Reaction (obvious Product/High case) but fail on the Trade Inquiry (subtler case). Priority accuracy is generally harder than category accuracy, as evidenced by lower scores in the right panel.

---

### ABLATION_REPORT.md

**File:** `comparative_analysis/ABLATION_REPORT.md`

This is the **auto-generated comprehensive report** produced by `generate_report.py`. It consolidates all benchmark findings into a single markdown document with the following sections:

1. **Models Evaluated** — Table of all 10 models with provider and model ID.
2. **Evaluation Criteria** — Detailed description of the 5 weighted metrics and what each measures, including the scoring logic (binary, partial credit, checklist-based).
3. **Test Scenarios** — The 4 complaint scenarios with category, priority, and channel.
4. **Overall Rankings** — Ranked table with medals (gold/silver/bronze) showing overall score, latency, and per-metric percentages for all 10 models.
5. **Graphs** — Embedded references to all 8 PNG visualizations with captions.
6. **Per-Task Breakdown** — Three sub-tables (Classify, Resolve, Ticket Generation) showing each model's score and latency per task.
7. **Detailed Metric Scores** — Full 5-metric breakdown table for all models.
8. **Recommendation** — Data-driven conclusion identifying the best model (Llama 3.3 70B at 96.9%), runner-up (Qwen 2.5 72B at 96.9%), and fastest model (Llama 3.3 70B at 1.4s). Includes production selection criteria: ≥90% category accuracy, ≥85% priority accuracy, valid resolution steps, ≤5s response time.
9. **How to Reproduce** — Step-by-step bash commands to run the entire ablation study.

**Why it matters:** This report is the definitive document for model selection decisions. It provides the evidence trail for why Llama 3.3 70B on Groq was chosen for production — not based on intuition, but on 120 API calls of empirical data across 5 metrics, 4 scenarios, and 3 tasks.

---

### Results Directory

**Path:** `comparative_analysis/results/`

Contains timestamped JSON files from each ablation run:

| File | Description |
|------|-------------|
| `ablation_results_latest.json` | The most recent complete run — always updated by `run_ablation.py`. This is the source file for `generate_report.py`. Contains raw scores, responses, token counts, and evaluation details for all 120 API calls across all 10 models. |
| `ablation_results_20260418_113320.json` | Timestamped snapshot from the initial 7-model run (GLM 5, GLM 5.1, MiMo V2 Omni, MiMo V2 Pro, MiniMax M2.5, MiniMax M2.7, Qwen 3.5 Plus). |
| `ablation_results_20260418_121141.json` | Timestamped snapshot from the incremental 3-model addition run (Llama 3.3 70B, Gemini 2.5 Flash, Qwen 2.5 72B), merged with the initial run via `run_additional_three_models.py`. |

**JSON structure per model:**
```json
{
  "glm_5": {
    "display_name": "GLM 5 (Zhipu)",
    "provider": "openrouter",
    "model_id": "glm-5",
    "results": [
      {
        "task": "classify",
        "scenario_name": "allergic_reaction",
        "category": "Product",
        "priority": "High",
        "response": "{... raw LLM output ...}",
        "latency_seconds": 14.027,
        "input_tokens": 642,
        "output_tokens": 875,
        "error": null,
        "evaluation": {
          "overall_score": 1.0,
          "classification_accuracy": { "score": 1.0, "predicted": "product", "expected": "product", "details": "Correct: 'product'" },
          "priority_accuracy": { "score": 1.0, "predicted": "high", "expected": "high", "details": "Correct: 'high'" },
          "resolution_quality": { "score": 1.0, "checks": {}, "details": "Not evaluated for classify task" },
          "format_compliance": { "score": 1.0, "valid_json": true, "has_required_fields": true, "details": "All required fields present" },
          "response_quality": { "score": 1.0, "word_count": 48, "details": "Good quality" },
          "latency_seconds": 14.027
        }
      }
      // ... 11 more test cases
    ]
  }
}
```

**Why it matters:** These JSON files are the raw experimental data. They can be re-analyzed, re-scored with different metrics, or used to generate new visualizations without re-running the expensive API calls. The timestamped files provide an audit trail of the benchmarking process.

---

### How to Reproduce

```bash
cd genai

# Set your API key
export OPENCODE_API_KEY=your_key_here

# 1. Test API connectivity
python -m comparative_analysis.test_api_keys

# 2. Run the ablation study  (~10-15 minutes for 10 models × 12 calls)
python -m comparative_analysis.run_ablation

# 3. Generate graphs and markdown report
python -m comparative_analysis.generate_report
```

Results are saved to `results/` and graphs to `graphs/`.

---

## Model Selection

The Llama 3.3 70B model on Groq was selected after a comprehensive **ablation study** comparing 10 models across 3 task types (Classify, Resolve, Ticket) on metrics including JSON validity, hallucination rate, completeness, response quality, and latency. Full results are in `comparative_analysis/`.

| Model | Provider | Result |
|-------|----------|--------|
| Llama 3.3 70B | Groq | **Selected** — best score/latency ratio (96.9%, 1.4s) |
| Qwen 2.5 72B | HuggingFace | Runner-up — same score but 8x slower (96.9%, 11.6s) |
| MiniMax M2.5 | OpenRouter | Strong third (96.0%, 13.5s) |
| Qwen 3.5 Plus | OpenRouter | Good quality but too slow (92.3%, 51.7s) |
| Gemini 2.5 Flash | Google | Solid but borderline latency (89.9%, 7.4s) |
| MiniMax M2.7 | OpenRouter | Moderate quality (89.3%, 15.1s) |
| GLM 5 | OpenRouter | Poor JSON compliance (49.2%, 19.1s) |
| GLM 5.1 | OpenRouter | Poor JSON compliance (45.4%, 14.9s) |
| MiMo V2 Pro | OpenRouter | Poor JSON compliance (45.4%, 15.0s) |
| MiMo V2 Omni | OpenRouter | Worst overall (32.4%, 13.0s) |

---

*Built for Tark Shaastra · LDCE Hackathon — SOLV.ai — AI-Powered Complaint Classification & Resolution Recommendation Engine*
