# TS-14 AI Complaint Resolution Engine — Orchestration Plan

## Project Overview
AI-Powered Complaint Classification & Resolution Recommendation Engine for Tark Shaastra · Lakshya 2.0 Hackathon. A 3-dashboard system (Admin, QA, Call Attender) with real-time SSE updates, AI classification, and SLA tracking.

**Team Size**: 2-4 members | **Timebox**: 24 hours | **Stack**: Next.js + FastAPI + Supabase PostgreSQL

---

## The 4-Wave Execution Framework

### Wave 1 — Architecture (BLOCKING)
**Assigned to**: Architect Agent (Orchestrator)

Before any code is written, produce these deliverables:

| Deliverable | Purpose | Status |
|-------------|---------|--------|
| `API_CONTRACTS.md` | All endpoints, request/response schemas — the single source of truth | PENDING |
| `DATA_MODELS.md` | Database schemas, entity relationships, indexes | PENDING |
| `TECH_STACK.md` | Language, framework, DB, auth method, hosting decisions | PENDING |
| `ENV.md` | All environment variables for frontend and backend | PENDING |

**Why sequential**: Frontend and backend agents cannot work in parallel until they agree on the API contract.

**Rules for Wave 1**:
- API contracts must include: method, path, auth required, request schema, response schema (success + errors), example request/response
- Data models must include: table names, column types, indexes, foreign keys
- Tech stack must address: language, framework, DB, cache, queue, auth method, hosting

---

### Wave 2 — Parallel Build
**Assigned to**: Two separate sub-agents spawned in parallel

Both agents receive: `API_CONTRACTS.md` + `DATA_MODELS.md` + `TECH_STACK.md` + `ENV.md`

| Sub-Agent | Scope | Tech | Status |
|-----------|-------|------|--------|
| **frontend-dev** | Next.js project, auth flow, 3 dashboards, GSAP landing page, SSE client | Next.js 14 + shadcn/ui + GSAP + Recharts | PENDING |
| **backend-dev** | FastAPI, database models, all API endpoints, SSE server, Brevo email integration | FastAPI + SQLAlchemy + Supabase PostgreSQL | PENDING |

**Frontend Scope**:
1. Project scaffold with Next.js 14 (App Router)
2. Auth flow: login/register with Supabase Auth
3. 3 dashboards: Admin, QA, Call Attender (role-based access)
4. Landing page with GSAP animations (horizontal scrolls, scroll-triggered)
5. API client with error handling, retry logic
6. SSE client for real-time updates
7. State management (Zustand or React Context)
8. Recharts for analytics
9. Responsive design + theme toggle
10. Demo mode toggle in admin dashboard

**Backend Scope**:
1. FastAPI project structure
2. Database schema + migrations (SQLAlchemy + Alembic)
3. All endpoints from API contract
4. Authentication: JWT + refresh tokens via Supabase Auth
5. Input validation and error responses
6. SSE endpoint for real-time complaint updates
7. ML bridge service (calls friend's model endpoint)
8. Brevo email integration (inbound webhook + outbound)
9. SLA calculation and breach detection
10. Seed script for 1000 demo rows from CSV

**Constraints for Both**:
- Frontend must mock API responses for independent development
- Backend must include `.env.example` with all required variables
- Both must use environment variables, no hardcoded values
- Response shapes must match the contract exactly

---

### Wave 3 — Verification
**Assigned to**: Verifier Agent

**Receives**: Frontend code + Backend code + `API_CONTRACTS.md`

**Three-Tier Test Protocol**:

| Tier | Test Type | Pass Criteria |
|------|-----------|---------------|
| 1 | Happy Paths | Every API endpoint returns expected 200/201 response |
| 2 | Failure Modes | Auth failures, validation errors, 404s handled gracefully |
| 3 | Performance | < 500ms response time, SSE updates within 2 seconds |

**Deliverable**: `VERIFICATION_REPORT.md`

Format:
```markdown
- SEVERITY: [CRITICAL/WARNING/INFO]
- COMPONENT: [frontend/backend]
- DESCRIPTION: What is wrong
- FIX: What needs to change
```

**Orchestrator Action**: Review report, triage findings, dispatch CRITICAL fixes back to appropriate sub-agent.

---

### Wave 4 — DevOps
**Assigned to**: DevOps Agent

**Receives**: Final frontend code + final backend code + `TECH_STACK.md`

**Deliverables**:

| Deliverable | Purpose |
|-------------|---------|
| `Dockerfile` (backend) | Containerized FastAPI |
| `Dockerfile` (frontend) | Containerized Next.js |
| `docker-compose.yml` | Local development stack |
| GitHub Actions CI/CD | Auto-deploy on push |
| Railway/Render config | Free tier deployment |
| `.env.production.example` | Production environment variables |
| `DEPLOYMENT.md` | Step-by-step deploy guide |

**Deployment Stack**:
- Frontend: Vercel (free tier, auto-deploy from GitHub)
- Backend: Railway (free tier, PostgreSQL included)
- Database: Supabase PostgreSQL
- Email: Brevo API

---

## Chunked TODO List

### Phase 1: Wave 1 — Architecture (Hours 0-2)

#### 1.1 Define Tech Stack
- [ ] Lock frontend framework: Next.js 14 with App Router
- [ ] Lock UI library: shadcn/ui with theme toggle
- [ ] Lock animation library: GSAP with ScrollTrigger
- [ ] Lock chart library: Recharts
- [ ] Lock state management: Zustand
- [ ] Lock backend framework: FastAPI
- [ ] Lock database: Supabase PostgreSQL
- [ ] Lock auth: Supabase Auth (JWT)
- [ ] Lock real-time: Server-Sent Events (SSE)
- [ ] Lock email: Brevo API (Sendinblue)
- [ ] Lock deployment: Vercel (frontend) + Railway (backend)

#### 1.2 Design API Contracts
- [ ] Define authentication endpoints (register, login, refresh, logout)
- [ ] Define complaint CRUD endpoints
- [ ] Define SSE streaming endpoint
- [ ] Define email webhook endpoint
- [ ] Define analytics aggregation endpoints
- [ ] Define demo mode toggle endpoints
- [ ] Write request/response schemas for each
- [ ] Write error response schemas
- [ ] Create example requests/responses

#### 1.3 Design Data Models
- [ ] Design `profiles` table (extends Supabase Auth)
- [ ] Design `customers` table
- [ ] Design `complaints` table with all fields
- [ ] Design `complaint_timeline` table
- [ ] Design `sla_config` table
- [ ] Design `daily_metrics` cache table
- [ ] Define column types, indexes, foreign keys
- [ ] Define enums (role, category, priority, status, submitted_via)

#### 1.4 Define Environment Variables
- [ ] List all frontend env vars
- [ ] List all backend env vars
- [ ] Create `.env.example` templates
- [ ] Document each variable's purpose

---

### Phase 2: Wave 2 — Parallel Build (Hours 2-20)

#### 2.1 Frontend Sub-Agent Tasks

**Setup & Auth (Hours 2-5)**:
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Install and configure shadcn/ui
- [ ] Install GSAP, ScrollTrigger, Recharts, Zustand
- [ ] Create project folder structure
- [ ] Set up environment variables handling
- [ ] Create Supabase client configuration
- [ ] Build login page with form validation
- [ ] Build register page with role selection
- [ ] Implement JWT token storage and refresh logic
- [ ] Create protected route middleware

**Landing Page (Hours 5-9)**:
- [ ] Create hero section with GSAP text reveal
- [ ] Create horizontal scroll section (How It Works)
- [ ] Add staggered card reveal animations
- [ ] Add live stats counter animation
- [ ] Create dashboard preview section with parallax
- [ ] Add CTA buttons with pulse animation
- [ ] Implement theme toggle (light/dark)
- [ ] Ensure mobile responsiveness

**Dashboard Layouts (Hours 9-12)**:
- [ ] Create sidebar navigation component
- [ ] Create header with user info and logout
- [ ] Build Admin dashboard layout
- [ ] Build QA dashboard layout
- [ ] Build Call Attender dashboard layout
- [ ] Implement role-based route guards

**Admin Dashboard Features (Hours 12-15)**:
- [ ] Build complaint feed table with filters
- [ ] Implement search functionality
- [ ] Add blinking red SLA breach indicator
- [ ] Build complaint detail view with timeline
- [ ] Build analytics panel with 4 charts
- [ ] Implement user management panel
- [ ] Add demo mode toggle button

**QA Dashboard Features (Hours 15-17)**:
- [ ] Build product complaint count bar chart
- [ ] Build trend analysis line chart
- [ ] Add category deep dive filters
- [ ] Implement export to CSV/PDF

**Call Attender Dashboard (Hours 17-19)**:
- [ ] Build active call panel (STT display placeholder)
- [ ] Create AI output display (numbered resolution steps)
- [ ] Implement quick action buttons (Share, Escalate, Log)
- [ ] Build recent complaints list
- [ ] Integrate SSE client for real-time updates

**Final Frontend Polish (Hours 19-20)**:
- [ ] Add loading states and skeletons
- [ ] Add error boundaries
- [ ] Create API client with retry logic
- [ ] Mock API responses for development
- [ ] Write frontend README

#### 2.2 Backend Sub-Agent Tasks

**Setup & Database (Hours 2-5)**:
- [ ] Initialize FastAPI project structure
- [ ] Install SQLAlchemy, Alembic, Pydantic
- [ ] Configure Supabase PostgreSQL connection
- [ ] Create database models from DATA_MODELS.md
- [ ] Generate initial Alembic migration
- [ ] Run migrations
- [ ] Create seed script for 1000 demo rows

**Authentication (Hours 5-7)**:
- [ ] Integrate Supabase Auth
- [ ] Implement JWT validation middleware
- [ ] Create register endpoint
- [ ] Create login endpoint
- [ ] Create token refresh endpoint
- [ ] Create logout endpoint
- [ ] Add password validation rules

**Complaint API (Hours 7-11)**:
- [ ] Create POST /complaints endpoint
- [ ] Implement ML bridge service
- [ ] Integrate with friend's model endpoint
- [ ] Implement SLA calculation logic
- [ ] Create GET /complaints with filters
- [ ] Create GET /complaints/:id endpoint
- [ ] Create PATCH /complaints/:id/status endpoint
- [ ] Create complaint timeline logging
- [ ] Add input validation

**Real-Time SSE (Hours 11-13)**:
- [ ] Implement SSE endpoint
- [ ] Add complaint change detection
- [ ] Push updates to connected clients
- [ ] Handle client disconnections
- [ ] Add heartbeat mechanism

**Email Integration (Hours 13-15)**:
- [ ] Set up Brevo API client
- [ ] Create inbound email webhook handler
- [ ] Parse incoming emails
- [ ] Auto-create complaints from emails
- [ ] Auto-create customers from new emails
- [ ] Implement outbound email for resolutions

**Analytics & Demo (Hours 15-17)**:
- [ ] Create analytics aggregation endpoints
- [ ] Implement daily metrics calculation
- [ ] Create demo mode seed endpoint
- [ ] Create demo mode clear endpoint
- [ ] Add SLA breach detection job
- [ ] Implement notification triggers

**Final Backend Polish (Hours 17-20)**:
- [ ] Add health check endpoint
- [ ] Add CORS configuration
- [ ] Create `.env.example`
- [ ] Write API documentation
- [ ] Write backend README with curl examples
- [ ] Test all endpoints locally

---

### Phase 3: Wave 3 — Verification (Hours 20-22)

#### 3.1 Tier 1 — Happy Paths
- [ ] Test user registration flow
- [ ] Test user login flow
- [ ] Test complaint creation via API
- [ ] Test complaint creation via email webhook
- [ ] Test SSE connection and updates
- [ ] Test all dashboard pages load correctly
- [ ] Verify charts display data
- [ ] Test demo mode toggle

#### 3.2 Tier 2 — Failure Modes
- [ ] Test invalid login credentials
- [ ] Test unauthorized access to protected routes
- [ ] Test invalid complaint data validation
- [ ] Test email webhook with malformed data
- [ ] Test SSE reconnection after disconnect
- [ ] Test database connection failure handling

#### 3.3 Tier 3 — Performance
- [ ] Measure API response times (< 500ms target)
- [ ] Test SSE update latency (< 2 seconds target)
- [ ] Verify dashboard loads with 1000 rows
- [ ] Test concurrent SSE connections
- [ ] Verify no memory leaks in long-running SSE

#### 3.4 Cross-Reference
- [ ] Verify frontend calls correct backend endpoints
- [ ] Verify response shapes match API contracts
- [ ] Verify database models match DATA_MODELS.md
- [ ] Check all env vars are documented

#### 3.5 Verification Report
- [ ] Create VERIFICATION_REPORT.md
- [ ] Document all findings
- [ ] Triage CRITICAL vs WARNING vs INFO
- [ ] Dispatch CRITICAL fixes to sub-agents

---

### Phase 4: Wave 4 — DevOps (Hours 22-24)

#### 4.1 Containerization
- [ ] Create backend Dockerfile
- [ ] Create frontend Dockerfile
- [ ] Create docker-compose.yml for local dev
- [ ] Test containers locally

#### 4.2 CI/CD Pipeline
- [ ] Create GitHub Actions workflow for frontend
- [ ] Create GitHub Actions workflow for backend
- [ ] Set up auto-deploy on push to main
- [ ] Add build status badges

#### 4.3 Deployment Configuration
- [ ] Create Vercel configuration (vercel.json)
- [ ] Create Railway configuration (railway.yaml)
- [ ] Set up production environment variables
- [ ] Create `.env.production.example`

#### 4.4 Documentation
- [ ] Write DEPLOYMENT.md
- [ ] Document step-by-step deploy process
- [ ] Add troubleshooting section
- [ ] Add rollback procedures

#### 4.5 Final Checks
- [ ] Verify production deployment works
- [ ] Test all features on production URL
- [ ] Verify email integration in production
- [ ] Verify SSE works through Vercel/Railway
- [ ] Create demo video script
- [ ] Prepare hackathon presentation

---

## Sub-Agent Instructions

### Frontend Sub-Agent

```
You are a senior frontend engineer building the TS-14 complaint resolution system.

CONTEXT:
- Project: TS-14 AI Complaint Classification Engine
- Stack: Next.js 14 + TypeScript + shadcn/ui + Tailwind + GSAP + Recharts + Zustand
- Auth: Supabase Auth with JWT
- API Base: http://localhost:8000 (will be env var)

BUILD IN ORDER:
1. Project scaffold with Next.js 14 App Router
2. Auth flow: login/register pages, token storage, protected routes
3. Landing page: GSAP hero, horizontal scroll, stats counter, dashboard preview
4. Admin dashboard: complaint table, filters, SLA breach indicator, analytics charts
5. QA dashboard: product complaint count, trend analysis, export
6. Call Attender: STT panel, resolution display, quick actions, SSE integration
7. Theme toggle, responsive design, loading states

CONSTRAINTS:
- Use shadcn/ui components, customize as needed
- All API calls must use environment variable for base URL
- Mock API responses for development (provide mock data files)
- GSAP animations must respect theme (detect dark mode)
- Dashboards must be responsive (mobile, tablet, desktop)

OUTPUT:
- Complete /app directory with all pages
- /components for reusable UI
- /lib for utilities and API client
- /hooks for custom React hooks
- /store for Zustand state management
- README.md with setup and run instructions
- List of API endpoints consumed (for verifier)
```

### Backend Sub-Agent

```
You are a senior backend engineer building the TS-14 complaint resolution API.

CONTEXT:
- Project: TS-14 AI Complaint Classification Engine
- Stack: FastAPI + SQLAlchemy + Alembic + Supabase PostgreSQL
- Auth: Supabase Auth (JWT validation)
- Email: Brevo API integration
- Real-time: Server-Sent Events (SSE)

BUILD IN ORDER:
1. Project structure: /app, /models, /routes, /services, /migrations
2. Database models: profiles, customers, complaints, timeline, sla_config, metrics
3. Alembic migrations
4. Auth integration with Supabase
5. Complaint CRUD endpoints
6. ML bridge service (HTTP client to friend's model)
7. SSE endpoint for real-time updates
8. Brevo email webhook handler
9. Analytics aggregation endpoints
10. Demo mode seed/clear endpoints
11. SLA calculation and breach detection

CONSTRAINTS:
- Every endpoint must match API_CONTRACTS.md exactly
- Include request/response validation with Pydantic
- All database operations use SQLAlchemy with proper sessions
- Include .env.example with all required variables
- Create seed script for 1000 demo complaints
- Add health check endpoint at /health

OUTPUT:
- Complete FastAPI application
- Alembic migration files
- /services for business logic
- /routes for API endpoints
- /models for database schemas
- /scripts for seeding
- README.md with setup, migration, and run instructions
- curl examples for all endpoints
```

### Verifier Sub-Agent

```
You are a verification engineer testing the TS-14 complaint resolution system.

CONTEXT:
- Frontend: Next.js running on localhost:3000
- Backend: FastAPI running on localhost:8000
- API Contract: See API_CONTRACTS.md

TEST PROTOCOL:
1. Start both services locally
2. Run three-tier tests:
   - Tier 1: All happy paths (register, login, create complaint, view dashboards, SSE)
   - Tier 2: Failure modes (invalid auth, bad data, 404s, disconnections)
   - Tier 3: Performance (response times, SSE latency, load with 1000 rows)
3. Cross-check frontend API calls against backend endpoints
4. Verify all API contract endpoints are implemented
5. Test auth flow end-to-end

REPORT FORMAT:
Create VERIFICATION_REPORT.md with:
- Summary (tests passed/failed)
- For each finding:
  - SEVERITY: CRITICAL / WARNING / INFO
  - COMPONENT: frontend / backend
  - TEST: What was tested
  - EXPECTED: What should happen
  - ACTUAL: What happened
  - FIX: Suggested fix

CRITICAL FIXES:
If CRITICAL findings exist, list them separately with:
- Exact file to modify
- Expected code change
- Verification steps after fix
```

### DevOps Sub-Agent

```
You are a DevOps engineer deploying the TS-14 complaint resolution system.

CONTEXT:
- Frontend: Next.js 14
- Backend: FastAPI
- Database: Supabase PostgreSQL (external)
- Deployment: Vercel (frontend) + Railway (backend)

DELIVERABLES:
1. Dockerfile for backend (Python 3.11 slim, multi-stage)
2. Dockerfile for frontend (if needed, or use Vercel native)
3. docker-compose.yml for local development stack
4. GitHub Actions workflow:
   - Frontend: Deploy to Vercel on push to main
   - Backend: Deploy to Railway on push to main
5. Railway configuration (railway.yaml)
6. Vercel configuration (vercel.json)
7. .env.production.example with all prod variables
8. DEPLOYMENT.md with:
   - Prerequisites
   - Step-by-step deploy instructions
   - Environment variable setup
   - Troubleshooting guide
   - Rollback procedure

CONSTRAINTS:
- Use free tiers only (Vercel Hobby, Railway Starter)
- Ensure SSE works through proxies
- Document any manual steps required
- Test the complete deploy flow

OUTPUT:
- All Docker files
- All CI/CD configs
- All deployment manifests
- Complete deployment documentation
```

---

## Context Management Rules

- **Orchestrator (this plan)**: Plan, decide, delegate, review. Never implement.
- **Sub-agents**: Implement, never plan.
- **Wave 1 documents**: Single source of truth. Both Wave 2 agents work from identical copies.
- **Blockers**: If a sub-agent is blocked by contract ambiguity, the orchestrator resolves it and updates both agents.
- **CRITICAL fixes**: Spawn a new sub-agent per CRITICAL with the failing code and expected behavior. Never self-implement.

---

## Out of Scope (Explicit)

- Actual STT implementation (handled by ML teammate)
- ML model training (friend's responsibility)
- Gujarati language support in UI (English only for hackathon demo)
- Mobile native apps (web-only)
- Advanced caching (Redis) — use in-memory if needed
- Complex queuing (Celery) — synchronous processing acceptable for demo
- Payment integration
- Multi-tenant architecture

---

## Winning Strategy

✅ **Epic Visuals**: GSAP horizontal scrolls, scroll-triggered animations on landing page  
✅ **Real-time**: SSE live updates across all dashboards  
✅ **Role Separation**: 3 distinct dashboards with proper RBAC  
✅ **AI Integration**: ML classification + Gen AI resolution steps  
✅ **SLA Intelligence**: Auto-calculation, breach alerts, visual indicators  
✅ **Real Email**: Brevo inbound/outbound integration  
✅ **Demo Ready**: Toggle mode with 1000 seeded rows  
✅ **Theme Switching**: Light/dark mode with shadcn  
✅ **Fast Deploy**: Vercel + Railway, zero-config  

**Hackathon Demo Flow**:
1. Landing page → GSAP animations impress judges
2. Demo mode → 1000 complaints instantly populate dashboards
3. Admin dashboard → Show analytics, SLA breaches, user management
4. QA dashboard → Show product complaint trends
5. Call attender → Simulate live call with STT placeholder
6. Real-time → Open two browsers, show SSE updates

---

*Generated by Auto-GSD Orchestration Skill*  
*For Tark Shaastra · Lakshya 2.0 | TS-14 AI Complaint Resolution Engine*
