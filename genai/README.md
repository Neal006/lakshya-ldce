# GenAI Complaint Resolution Microservice

> AI-powered resolution recommendation engine for customer complaints in the wellness industry.  
> Built for **TS-14: AI-Powered Complaint Classification & Resolution Recommendation Engine** (Lakshya 2.0, LDCE Hackathon).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
  - [GET /health](#get-health)
  - [POST /resolve](#post-resolve)
  - [POST /resolve/quick](#post-resolvequick)
- [Request & Response Schemas](#request--response-schemas)
- [Prompt Engineering](#prompt-engineering)
- [Security & Guardrails](#security--guardrails)
- [Observability (LangSmith)](#observability-langsmith)
- [SLA Management](#sla-management)
- [Configuration Reference](#configuration-reference)
- [Integration with NLP Classifier](#integration-with-nlp-classifier)
- [Error Handling](#error-handling)
- [Example Scenarios](#example-scenarios)

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
├── .env                    # API keys and configuration (gitignored)
├── config.py               # Centralized configuration loader
├── llm.py                  # Provider-agnostic LLM client + LangSmith tracing
├── models.py               # Pydantic request/response schemas
├── prompts.py              # System + user prompt templates
├── guardrails.py           # 4-layer security: sanitize, detect, validate, parse
├── main.py                 # FastAPI server, routes, middleware
├── run_server.py           # Entry point (python run_server.py)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── comparative_analysis/   # Ablation study (10 models compared)
│   ├── config.py
│   ├── prompts.py
│   ├── run_ablation.py
│   ├── evaluate.py
│   ├── results/
│   └── graphs/
└── Problem Statement TS-21-23.pdf
```

---

## Quick Start

### 1. Install dependencies

```bash
cd genai
pip install -r requirements.txt
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

**Request:**
```
GET http://localhost:8001/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "llm_connected": true,
  "nlp_service_url": "http://localhost:8000",
  "version": "1.0.0"
}
```

**Status values:**
| Status | Meaning |
|--------|---------|
| `healthy` | LLM is connected and responding |
| `degraded` | Service is running but LLM is unreachable |

---

### POST /resolve

Primary endpoint. Accepts classified complaint data with optional customer metadata and returns a full AI-generated resolution plan.

**Request:**
```
POST http://localhost:8001/resolve
Content-Type: application/json
Authorization: Bearer <api_key>  (optional, if GENAI_API_KEY is set)
```

**Request Body:**
```json
{
  "classifier_output": {
    "complaint_id": 2,
    "text": "Product stopped working after just 2 days. This is completely unacceptable quality!",
    "category": "Product",
    "sentiment_score": -0.8,
    "priority": "High",
    "latency_ms": 150.3
  },
  "customer_name": "Rahul Sharma",
  "channel": "email",
  "product_name": "Omega-3 Fish Oil Capsules"
}
```

**Response (200):**
```json
{
  "complaint_id": 2,
  "original_text": "Product stopped working after just 2 days. This is completely unacceptable quality!",
  "category": "Product",
  "priority": "High",
  "sentiment_score": -0.8,
  "customer_response": "Dear Rahul Sharma, we sincerely apologize for the issue you're experiencing with our Omega-3 Fish Oil Capsules, which stopped working after just 2 days. We understand that this is not the quality you expected from our product. We are committed to making it right and ensuring your satisfaction. Please allow us to investigate this matter further and provide a suitable resolution. Your reference number for this issue is Complaint ID 2.",
  "immediate_action": "Acknowledge the customer's complaint via email and assign a priority flag for immediate investigation by the Quality Assurance team.",
  "resolution_steps": [
    "[Quality Assurance Team] Investigate the batch records of the Omega-3 Fish Oil Capsules to identify any potential quality control issues.",
    "[Customer Support Team] Offer a replacement or refund to the customer, depending on their preference, and provide a prepaid return shipping label if necessary.",
    "[Quality Assurance Team] Trigger a thorough analysis of the product's formulation and manufacturing process to prevent similar issues in the future."
  ],
  "assigned_team": "Customer Support | Quality Assurance",
  "escalation_required": true,
  "follow_up_required": true,
  "follow_up_timeline": "24 hours",
  "estimated_resolution_time": "4 hours",
  "root_cause_hypothesis": "The issue might be related to a specific batch of the Omega-3 Fish Oil Capsules that did not meet our quality standards, potentially due to a manufacturing defect or an issue with the raw materials used.",
  "sla_deadline_hours": 4,
  "status": "Escalated",
  "confidence": "medium",
  "model_used": "llama-3.3-70b-versatile",
  "genai_latency_ms": 1453.83
}
```

---

### POST /resolve/quick

Shorthand endpoint that accepts raw classifier output directly without the wrapper object. Uses default values for customer_name ("Valued Customer"), channel ("web"), and product_name ("Wellness Product").

**Request:**
```
POST http://localhost:8001/resolve/quick
Content-Type: application/json
```

**Request Body:**
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

**Response:** Same schema as `/resolve`.

---

## Request & Response Schemas

### ClassifierOutput (Input from NLP service)

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `complaint_id` | `int \| str` | Yes | — | Unique complaint identifier |
| `text` | `str` | Yes | 1-2000 chars | Original complaint text |
| `category` | `str` | Yes | `Product \| Packaging \| Trade` | NLP-classified category |
| `sentiment_score` | `float` | Yes | -1.0 to 1.0 | VADER sentiment score |
| `priority` | `str` | Yes | `High \| Medium \| Low` | NLP-assigned priority |
| `latency_ms` | `float` | No | >= 0 | NLP inference latency |

### ResolveRequest (Full request wrapper)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `classifier_output` | `ClassifierOutput` | Yes | — | Output from NLP classifier |
| `customer_name` | `str` | No | "Valued Customer" | Customer name for personalization |
| `channel` | `str` | No | "web" | Complaint channel (web/email/phone/chat) |
| `product_name` | `str` | No | "Wellness Product" | Product involved |

### ResolutionResponse (Output)

| Field | Type | Description |
|-------|------|-------------|
| `complaint_id` | `int \| str` | Echoed from input |
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

Injects all complaint-specific data:
- Complaint ID, customer name, channel, product name
- NLP classification results (category, priority, sentiment score)
- Original complaint text

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

When LangSmith is not configured, every LLM call is still logged as structured JSON to stdout:

```json
{
  "event": "llm_call",
  "model": "llama-3.3-70b-versatile",
  "latency_ms": 1387,
  "prompt_chars": 2456,
  "output_chars": 892,
  "status": "success"
}
```

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

---

## Integration with NLP Classifier

### Full Pipeline Flow

```bash
# Step 1: Classify the complaint (NLP service on port 8000)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"complaint_id": 1, "text": "Box was broken"}'

# Response:
# {
#   "complaint_id": 1,
#   "text": "Box was broken",
#   "category": "Packaging",
#   "sentiment_score": -0.4767,
#   "priority": "High",
#   "latency_ms": 206.8
# }

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

### Integration from Backend Code (Python)

```python
import httpx

async def process_complaint(complaint_id: int, text: str):
    async with httpx.AsyncClient() as client:
        # Step 1: Classify
        classify_resp = await client.post(
            "http://localhost:8000/predict",
            json={"complaint_id": complaint_id, "text": text},
        )
        classifier_output = classify_resp.json()

        # Step 2: Resolve
        resolve_resp = await client.post(
            "http://localhost:8001/resolve/quick",
            json=classifier_output,
        )
        resolution = resolve_resp.json()
        return resolution
```

### Integration from Backend Code (JavaScript/Node.js)

```javascript
async function processComplaint(complaintId, text) {
  // Step 1: Classify
  const classifyResp = await fetch("http://localhost:8000/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ complaint_id: complaintId, text }),
  });
  const classifierOutput = await classifyResp.json();

  // Step 2: Resolve
  const resolveResp = await fetch("http://localhost:8001/resolve/quick", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(classifierOutput),
  });
  return await resolveResp.json();
}
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

---

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

---

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

## Model Selection

The Llama 3.3 70B model on Groq was selected after a comprehensive **ablation study** comparing 10 models across 3 task types (Classify, Resolve, Ticket) on metrics including JSON validity, hallucination rate, completeness, response quality, and latency. Full results are in `comparative_analysis/`.

| Model | Provider | Result |
|-------|----------|--------|
| Llama 3.3 70B | Groq | **Selected** — best score/latency ratio |
| Gemini 2.5 Flash | Google | Strong quality, higher latency |
| Qwen 2.5 72B | HuggingFace | Good quality, slow inference |
| GLM 5 / 5.1 | Zhipu | Competitive, less consistent JSON |
| MiMo V2 | Xiaomi | Fast but lower quality |
| MiniMax M2.5/M2.7 | MiniMax | Variable quality |
| Qwen 3.5 Plus | Alibaba | Good but slower |

---

*Built for Lakshya 2.0 LDCE Hackathon — TS-14: AI-Powered Complaint Classification & Resolution Recommendation Engine*
