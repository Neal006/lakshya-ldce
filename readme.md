# TS-14 — AI-Powered Complaint Classification & Resolution System


> Built for **Tark Shaastra · Lakshya 2.0 Hackathon**

An end-to-end platform that classifies, prioritizes, and resolves customer complaints in the wellness industry using an ensemble NLP pipeline, a FastAPI backend, and a 10-model LLM ablation study to select the best generative AI for production.

---

## Architecture Overview

```
Customer Complaint (text)
        |
        v
+-----------------------------------------------------+
|                  NLP Pipeline (text_classifier/)    |
|  +------------------+   +------------------------+  |
|  | Category         |   | Sentiment (VADER)       |  |
|  | Ensemble:        |   | Score: [-1.0, +1.0]     |  |
|  |  DistilBERT MNLI |   +------------------------+  |
|  | + MiniLM-L6-v2   |   +------------------------+  |
|  | -> Trade/Product |   | Priority (Decision Tree)|  |
|  |    /Packaging    |   | High / Medium / Low     |  |
|  +------------------+   +------------------------+  |
+-----------------------------------------------------+
        |
        v
+-----------------------------------------------------+
|               FastAPI Backend (website/backend/)     |
|  JWT Auth . Role-Based Access . SLA Tracking        |
|  SSE Real-Time Updates . Brevo Email Webhooks       |
|  SQLAlchemy ORM (SQLite dev / Supabase PostgreSQL)  |
+-----------------------------------------------------+
        |
        +----------------------------------------------
        |          3 Role-Based Dashboards
        +-- Admin         -> Full feed, SLA alerts, analytics
        +-- QA            -> Product trends, export (CSV/PDF)
        +-- Call Attender -> AI resolution steps, live SSE
```

![Workflow Diagram](workflow1.png)

---

## Project Structure

```
lakshya-ldce/
|-- text_classifier/              # Core ML/NLP pipeline
|   |-- nlp.py                    # Ensemble classifier
|   |-- evaluate.py               # Evaluation metrics
|   |-- DOCUMENTATION.md          # Technical deep-dive
|   +-- data/data.csv             # 50,000-complaint training set
|
|-- genai/
|   +-- comparative_analysis/     # 10-model LLM ablation study
|       |-- config.py             # API keys + model definitions
|       |-- test_scenarios.py     # 4 wellness complaint cases
|       |-- prompts.py            # System/user prompts (3 tasks)
|       |-- evaluate.py           # 5-metric scoring engine
|       |-- run_ablation.py       # Main runner
|       |-- generate_report.py    # Graph + markdown report
|       +-- results/              # Raw scores JSON
|
+-- website/
    |-- backend/                  # FastAPI REST API
    |   |-- app/
    |   |   |-- main.py           # App setup, routers, middleware
    |   |   |-- models/models.py  # 8 database tables
    |   |   |-- routes/           # auth, complaints, analytics, SSE, webhooks
    |   |   |-- services/         # Business logic
    |   |   |-- schemas/          # Pydantic models
    |   |   +-- middleware/       # JWT auth, exception handling
    |   |-- alembic/              # Database migrations
    |   +-- tests/                # pytest suite
    +-- markdown/                 # Specs & contracts
        |-- API_CONTRACTS.md
        |-- FEATURES.md
        +-- ROADMAP.md
```

---

## Modules

### 1. NLP Pipeline (`text_classifier/`)

Lightweight, CPU-deployable classifier — no GPU required.

| Task | Method | Output |
|------|--------|--------|
| Category | Ensemble: DistilBERT MNLI (zero-shot) + MiniLM-L6-v2 (semantic similarity) | Trade / Product / Packaging |
| Sentiment | VADER (rule-based, <1 MB) | Continuous score [-1.0, +1.0] |
| Priority | Decision Tree (scikit-learn, max_depth=6) | High / Medium / Low |

**Models used:**
- `typeform/distilbert-base-uncased-mnli` — 66M params, zero-shot NLI
- `all-MiniLM-L6-v2` — 22M params, fast semantic similarity
- VADER — no training required, no GPU needed

See [text_classifier/DOCUMENTATION.md](text_classifier/DOCUMENTATION.md) for full design rationale.

**Quick start:**
```python
from text_classifier.nlp import ComplaintClassifier

clf = ComplaintClassifier()
result = clf.predict("The bottle leaked and damaged my order.")
# {"category": "Packaging", "sentiment": -0.62, "priority": "High"}
```

**Evaluate on full dataset:**
```bash
cd text_classifier
python evaluate.py
# Outputs: accuracy, precision, recall, F1, AUC-ROC, confusion matrix
```

---

### 2. LLM Ablation Study (`genai/comparative_analysis/`)

Benchmarks **10 LLM models** across 4 realistic wellness complaint scenarios and 3 tasks to pick the best model for production resolution generation.

**Models evaluated:**

| Provider | Model |
|----------|-------|
| Zhipu | GLM-5, GLM-5.1 |
| Moonshot | Kimi K2.5 |
| Xiaomi | MiMo V2 Omni, MiMo V2 Pro |
| MiniMax | M2.5, M2.7 |
| Alibaba | Qwen 3.5 Plus, Qwen 2.5 72B |
| Google | Gemini 2.5 Flash |
| Meta (via Groq) | Llama 3.3 70B |

**Evaluation protocol:** 4 scenarios x 3 tasks (classify -> resolve -> ticket) = 12 calls per model

**Scoring metrics:** classification accuracy, priority accuracy, resolution quality, format compliance, response coherence

**Run the study:**
```bash
cd genai/comparative_analysis
pip install -r requirements.txt
python run_ablation.py        # all 10 models x 4 scenarios
python generate_report.py     # graphs + markdown report
```

Results are saved to `results/ablation_results_latest.json`.

---

### 3. Backend API (`website/backend/`)

FastAPI application with async endpoints, role-based access control, SLA tracking, and real-time SSE updates.

**Database schema (8 tables):**

| Table | Purpose |
|-------|---------|
| `profiles` | Users with roles: `admin`, `qa`, `call_attender` |
| `customers` | Customer records (name, email, phone) |
| `complaints` | Core records with AI classification fields |
| `complaint_timeline` | Full audit log of all actions |
| `sla_config` | Deadline rules per priority level |
| `daily_metrics` | Aggregated analytics data |

**API surface** — full schemas in [API_CONTRACTS.md](website/markdown/API_CONTRACTS.md):

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh` |
| Complaints | `GET/POST /complaints`, `GET/PUT/DELETE /complaints/{id}` |
| Analytics | `GET /analytics/dashboard`, `/analytics/trends` |
| Real-time | `GET /sse/complaints` (Server-Sent Events) |
| Email | `POST /webhooks/inbound` (Brevo) |
| Demo | `POST /demo/seed`, `DELETE /demo/clear` |
| Health | `GET /health` |

**Setup:**
```bash
cd website/backend
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
# Interactive docs at http://localhost:8000/docs
```

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| API | Python 3.x, FastAPI, Uvicorn (ASGI) |
| Database | SQLAlchemy ORM, Alembic, SQLite (dev) / PostgreSQL via Supabase (prod) |
| Auth | python-jose (JWT), bcrypt |
| Real-time | sse-starlette |
| Email | Brevo API webhooks |
| NLP | Hugging Face Transformers, Sentence-Transformers, vaderSentiment |
| ML | scikit-learn, pandas, numpy |
| LLM eval | OpenRouter / OpenCode unified API, google-generativeai, matplotlib |
| Testing | pytest, pytest-asyncio |

---

## Environment Variables

**Backend** — copy `website/backend/.env.example` to `.env`:
```env
DATABASE_URL=sqlite:///./complaints.db
JWT_SECRET=<your-secret>
JWT_ALGORITHM=HS256
BREVO_API_KEY=<brevo-key>
ML_SERVICE_URL=http://localhost:8001
SUPABASE_URL=<optional>
SUPABASE_KEY=<optional>
```

**LLM ablation** — `genai/.env`:
```env
OPENROUTER_API_KEY=<key>     # covers most models
GOOGLE_API_KEY=<key>         # Gemini 2.5 Flash
HUGGINGFACE_API_KEY=<key>    # Qwen 2.5 72B
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [text_classifier/DOCUMENTATION.md](text_classifier/DOCUMENTATION.md) | NLP design, model selection rationale, usage examples, evaluation results |
| [website/markdown/API_CONTRACTS.md](website/markdown/API_CONTRACTS.md) | All REST endpoints with request/response schemas |
| [website/markdown/FEATURES.md](website/markdown/FEATURES.md) | Complete feature checklist across all 3 dashboards |
| [website/markdown/ROADMAP.md](website/markdown/ROADMAP.md) | 4-wave execution plan: architecture -> build -> integration -> deploy |
| [genai/comparative_analysis/README.md](genai/comparative_analysis/README.md) | Ablation study methodology and reproduction steps |

---

## Hackathon Context

**Event:** Tark Shaastra · Lakshya 2.0  
**Problem Statement:** TS-14 — AI-powered complaint classification and resolution for the wellness industry

The NLP classification layer and LLM ablation study are fully functional and evaluated. The backend API schema, database models, middleware, and route structure are complete and ready for frontend integration.
