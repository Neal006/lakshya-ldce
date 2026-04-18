# Lakshya — AI-Powered Voice Complaint Management System

A lightweight, edge-deployable multi-agent voice complaint system that handles phone calls, classifies complaints, generates resolution steps, and creates tickets — all running locally on 4GB RAM with no internet dependency.

## Architecture

```
                        PHONE CALL
                            │
                    ┌───────▼───────┐
                    │    TWILIO     │  Cloud (telephony only)
                    │  Media Stream │  WebSocket PCM16 audio
                    └───────┬───────┘
                            │
        ┌───────────────────▼──────────────────────┐
        │          ORCHESTRATOR  (:8003)            │
        │                                          │
        │  ┌─────────────────────────────────────┐  │
        │  │  Telephony Layer                    │  │
        │  │  • Twilio webhook + media WS        │  │
        │  │  • μ-law ↔ PCM16 conversion        │  │
        │  │  • Barge-in detection              │  │
        │  └──────────────┬────────────────────┘  │
        │                 │                        │
        │  ┌──────────────▼────────────────────┐   │
        │  │  Pipeline Coordinator              │   │
        │  │  greeting → collecting →          │   │
        │  │  confirming → classifying →       │   │
        │  │  resolving → ticket_created        │   │
        │  └──────────────┬────────────────────┘   │
        │                 │                        │
        │  ┌──────────────▼────────────────────┐   │
        │  │  Agent Router (fallback chain)     │   │
        │  │                                     │   │
        │  │  LLM: Ollama (local) → Groq       │   │
        │  │  TTS: Piper (local) → Edge TTS     │   │
        │  └────────────────────────────────────┘   │
        └───────────────────┬────────────────────┘
                            │
          ┌─────────────────┼─────────────┐
          │                 │             │
    ┌─────▼─────┐   ┌──────▼──────┐  ┌───▼───────┐
    │    STT     │   │ Classifier  │  │  Backend   │
    │  :8001     │   │   :8002     │  │  :8000     │
    │ Whisper-   │   │ DistilBERT+ │  │ FastAPI    │
    │ tiny + VAD │   │ MiniLM+VADER│  │ SQLite+SLA │
    └───────────┘   └─────────────┘  └────────────┘

         + Ollama :11434 (phi3.5:1.5B or qwen2.5:1.5b)
         + Piper TTS (local, offline)
         + Twilio (cloud, for telephony only)
```

## Call Flow

```
1. User dials Twilio number
2. Twilio opens WebSocket to Orchestrator
3. Greeting TTS plays: "Welcome to the complaint helpline"
4. User speaks → STT transcribes → Dialog Agent extracts structured data
5. User confirms → Classify Agent runs ONNX ensemble → Resolve Agent generates steps
6. Ticket Agent creates ticket via Backend API → TTS confirms ticket number
7. Dashboard shows live ticket with resolution steps

Full perceived latency: ~2-4 seconds per turn on CPU
```

## Features

- **Offline-first**: All AI runs locally (Ollama LLM, Whisper STT, ONNX classifier, Piper TTS)
- **Cloud acceleration**: Groq API and Edge TTS used when internet is available, automatic fallback to local
- **FMCG domain correction**: 40+ Indian brand name corrections (Parle-G, Kurkure, Maggi, etc.)
- **FMCG-optimized classifier**: DistilBERT-MNLI + MiniLM ensemble for Trade/Product/Packaging
- **Edge-deployable**: Runs on 4GB RAM, ~2.8GB total memory usage
- **Role-based dashboards**: 3 views (Support, QA, Operations) via lightweight static HTML
- **SLA tracking**: Auto-calculated deadlines (High=4h, Medium=8h, Low=24h)
- **Barge-in support**: Detects user speech during TTS playback via VAD

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama (for local LLM)
- 4GB+ RAM
- Twilio account (for phone calls)

### Local Development

```bash
# 1. Install Ollama and pull a model
ollama pull phi3.5:latest

# 2. Start STT service (port 8001)
cd stt && python run_server.py --port 8001

# 3. Start Classifier service (port 8002)
cd text_classifier && python run_server.py --port 8002

# 4. Start Backend service (port 8000)
cd website/backend && python -m uvicorn app.main:app --port 8000

# 5. Start Orchestrator (port 8003)
cd voice-agent/orchestrator && python -m uvicorn main:app --port 8003

# 6. Open Dashboard
# http://localhost:8000/dashboard
```

### Docker Deployment

```bash
# Cloud mode (with Twilio telephony)
cd voice-agent
cp .env.example .env
# Edit .env with your Twilio credentials
docker-compose up -d

# Edge mode (fully offline, no telephony)
cd voice-agent
docker-compose -f docker-compose.edge.yml up -d
```

### Test the Pipeline

```bash
# Test with text input (no phone needed)
curl -X POST http://localhost:8003/test/pipeline \
  -H "Content-Type: application/json" \
  -d '{"text": "My Parle-G biscuit packet was torn and the biscuits were all broken"}'

# Run all integration tests
cd voice-agent/orchestrator
python tests/test_phase2.py   # Session, FSM, audio utils
python tests/test_phase3.py   # Full pipeline with real services
python tests/test_phase5_6.py  # Edge hardening, LLM routing, FMCG corrections
```

## Project Structure

```
voice-agent/
├── orchestrator/                  # Main orchestration service
│   ├── main.py                   # FastAPI app + health + test endpoints
│   ├── config.py                 # All configuration and environment variables
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── agents/
│   │   ├── dialog.py             # LLM-based complaint extraction
│   │   ├── classify_client.py    # HTTP client to classifier /predict
│   │   ├── resolve.py            # LLM-based resolution step generation
│   │   ├── ticket_client.py      # HTTP client to backend /complaints
│   │   ├── stt_client.py         # HTTP client to STT /transcribe/raw
│   │   └── llm_router.py         # Smart routing: Ollama ↔ Groq fallback
│   ├── telephony/
│   │   ├── twilio_handler.py     # Twilio webhook + WebSocket media handler
│   │   ├── audio_utils.py        # μ-law ↔ PCM16 ↔ float32 conversions
│   │   └── barge_in.py          # VAD-based interrupt detection
│   ├── pipeline/
│   │   ├── session.py            # CallSession FSM + SessionManager
│   │   ├── coordinator.py        # Orchestrates all agent calls
│   │   └── confidence.py         # Confidence cascade thresholds
│   ├── tts/
│   │   ├── __init__.py           # TTS router (Piper primary, Edge TTS fallback)
│   │   ├── piper_tts.py          # Local Piper TTS (offline, ~50ms)
│   │   ├── edge_tts_client.py    # Cloud Edge TTS (online, ~200ms)
│   │   └── audio_convert.py     # MP3/WAV → PCM16 conversion
│   ├── prompts/
│   │   ├── extraction.py         # Dialog extraction prompt template
│   │   ├── resolution.py         # Resolve resolution prompt template
│   │   └── corrections.py         # 40+ FMCG brand name corrections
│   └── tests/
│       ├── test_phase2.py        # Unit + integration tests
│       ├── test_phase3.py        # Full pipeline tests with real services
│       └── test_phase5_6.py      # Edge hardening + E2E tests
├── dashboard/                     # Lightweight static dashboard
│   ├── index.html                # Login + overview + complaints + analytics
│   ├── app.js                    # Vanilla JS, no framework, ~5KB
│   ├── styles.css                # Dark theme, responsive
│   └── lib/                      # Chart.js for charts
├── docker-compose.yml            # Cloud deployment (with Twilio)
├── docker-compose.edge.yml       # Edge deployment (fully offline)
├── .env.example                  # Environment variable template
├── start.sh                      # Cloud startup script
├── start-edge.sh                 # Edge offline startup script
└── stop.sh                       # Stop all services
```

## Configuration

All configuration is in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PRIMARY_LLM` | `auto` | `auto`, `ollama`, or `groq` |
| `PRIMARY_TTS` | `auto` | `auto`, `piper`, or `edge_tts` |
| `NETWORK_MODE` | `auto` | `auto`, `online`, or `offline` |
| `OLLAMA_MODEL` | `phi3.5:latest` | Ollama model for Dialog/Resolve agents |
| `GROQ_API_KEY` | — | Required for cloud LLM (optional) |
| `TWILIO_ACCOUNT_SID` | — | Required for phone calls |
| `STT_SERVICE_URL` | `http://localhost:8001` | STT service URL |
| `CLASSIFIER_SERVICE_URL` | `http://localhost:8002` | Classifier service URL |
| `BACKEND_SERVICE_URL` | `http://localhost:8000` | Backend API URL |

### Dual-Mode Operation

| Mode | LLM | TTS | Telephony | Dashboard |
|------|-----|-----|-----------|-----------|
| **Online** | Groq (fast) → Ollama fallback | Edge TTS → Piper fallback | Twilio | Full |
| **Offline** | Ollama only | Piper only | Unavailable | Works on LAN |

## API Endpoints

### Orchestrator (:8003)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (checks all dependent services) |
| GET | `/metrics` | Prometheus metrics |
| POST | `/test/pipeline` | Test pipeline with text input |
| POST | `/twilio/voice` | Twilio voice webhook |
| WS | `/twilio/media` | Twilio media stream |

### Backend (:8000)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | JWT authentication |
| POST | `/auth/register` | User registration |
| GET | `/complaints` | List complaints (paginated, filtered) |
| POST | `/complaints` | Create complaint (used by voice pipeline) |
| GET | `/complaints/{id}` | Get complaint detail |
| PATCH | `/complaints/{id}/status` | Update complaint status |
| POST | `/complaints/{id}/escalate` | Escalate complaint |
| GET | `/analytics/dashboard` | KPI analytics |
| GET | `/analytics/export/csv` | CSV export |
| GET | `/dashboard` | Static dashboard HTML |

### STT (:8001)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/transcribe` | Transcribe audio file |
| POST | `/transcribe/raw` | Transcribe raw PCM16 |
| WS | `/ws/transcribe` | Streaming transcription |
| GET | `/metrics` | Prometheus metrics |

### Classifier (:8002)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/predict` | Classify complaint text |
| GET | `/metrics` | Prometheus metrics |

## Session State Machine

```
greeting → collecting → confirming → classifying → resolving → ticket_created → done
                ↑           │
                └───────────┘ (user says "no")
```

- **greeting**: Welcome message plays
- **collecting**: Dialog Agent extracts structured data (max 4 turns)
- **confirming**: User confirms extracted complaint
- **classifying**: Classifier runs ONNX ensemble + VADER sentiment
- **resolving**: Resolve Agent generates 2-3 action steps via LLM
- **ticket_created**: Ticket persisted in backend DB, confirmation message plays

## FMCG Domain Corrections

The system corrects 40+ common misrecognitions from Indian-accented speech:

| Misrecognized | Corrected |
|--------------|-----------|
| parley g | Parle-G |
| curry cure | Kurkure |
| maggy | Maggi |
| surf excell | Surf Excel |
| dairy milk | Dairy Milk |

Full list in `orchestrator/prompts/corrections.py`.

## Resource Requirements

| Component | RAM (estimated) | Disk | Offline |
|-----------|----------------|------|---------|
| STT (Whisper-tiny) | ~300MB | ~50MB | Yes |
| Classifier (ONNX) | ~200MB | ~200MB | Yes |
| Backend (FastAPI+SQLite) | ~100MB | ~10MB | Yes |
| Orchestrator (FastAPI) | ~100MB | ~5MB | Yes |
| Ollama (phi3.5) | ~1.5GB | ~1GB | Yes |
| Piper TTS | ~100MB | ~30MB | Yes |
| **Total** | **~2.8GB** | **~1.3GB** | |

## Performance (CPU-only, x86)

| Component | Latency |
|-----------|---------|
| STT (Whisper-tiny) | 300-500ms |
| Classifier (ONNX) | 10-30ms |
| LLM (Ollama phi3.5) | 2-4s |
| LLM (Groq cloud) | 0.5-1.5s |
| Piper TTS | 10-50ms |
| Edge TTS (cloud) | ~200ms |
| **End-to-end (offline)** | **~4-6s per turn** |
| **End-to-end (online)** | **~2-3s per turn** |

## Cost (Cloud Deployment)

| Item | Monthly Cost |
|------|-------------|
| Cloud VM (4 vCPU, 8GB) | $20-40 |
| Twilio India number | ~$35 |
| Twilio per-minute | ~$0.0085/min |
| Groq API | Free tier |
| Edge TTS | Free |
| Ollama | Free (self-hosted) |
| STT/Classifier | Free (self-hosted) |
| **Total** | **~$55-75/month** |

Edge/offline mode: **$0 API fees** (hardware cost only).

## Testing

```bash
# Run unit + integration tests
cd voice-agent/orchestrator
python tests/test_phase2.py    # Session, FSM, audio, corrections
python tests/test_phase3.py    # Full pipeline with real services
python tests/test_phase5_6.py # Edge hardening, LLM routing, FMCG
```

### Test Coverage

| Phase | Tests | What's Verified |
|-------|-------|----------------|
| Phase 2 | 11 tests | Session creation, FSM transitions, coordinator, FMCG corrections, audio utils, barge-in, config |
| Phase 3 | 8 tests | STT health, classifier health, backend health, Ollama health, classifier predictions, Dialog extraction, full E2E pipeline, orchestrator health |
| Phase 5+6 | 8 tests | LLM routing (Ollama/Groq fallback), TTS routing (Piper/Edge), offline mode config, service availability, E2E pipeline, FMCG corrections, security, resource budget |

## Production Checklist

- [ ] Set `JWT_SECRET` in backend `.env`
- [ ] Set `GROQ_API_KEY` in orchestrator `.env` (optional, for cloud LLM)
- [ ] Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- [ ] Set `PUBLIC_HOST` to your public domain for Twilio webhooks
- [ ] Configure Twilio voice URL to `https://your-domain/twilio/voice`
- [ ] Download Piper voice models to `piper/voices/`
- [ ] Pull Ollama model: `ollama pull phi3.5:latest`
- [ ] Run `docker-compose up -d` and verify all health checks
- [ ] Create service account: POST `/auth/register` with role `admin`
- [ ] Seed SLA config or run `/demo/seed`

## License

Internal project — Lakshya LDCE.