# TS-14 AI Complaint Resolution Engine — Feature List

## Authentication

- [ ] User registration with email, password, name, and role (admin, qa, call_attender)
- [ ] User login with JWT access + refresh tokens
- [ ] Token refresh endpoint
- [ ] Logout endpoint
- [ ] Protected route middleware (role-based access control)
- [ ] Password validation (min 8 chars, uppercase, lowercase, number)

## Complaint Management

- [ ] Create complaint with raw text, customer info, and submission channel
- [ ] AI auto-classification of complaint category (Product, Packaging, Trade)
- [ ] AI auto-assignment of priority (High, Medium, Low)
- [ ] AI-generated resolution steps (numbered action items)
- [ ] Sentiment scoring on complaint text
- [ ] SLA deadline auto-calculation based on priority
- [ ] List complaints with pagination and filters (status, category, priority, submitted_via, search)
- [ ] View single complaint with full detail and timeline
- [ ] Update complaint status with state machine (open → in_progress → resolved, escalated)
- [ ] Escalate complaint with reason
- [ ] Complaint timeline logging (who did what, when)

## Real-Time Updates (SSE)

- [ ] SSE endpoint for live complaint updates
- [ ] Push new complaint events to connected clients
- [ ] Push status change events
- [ ] Push SLA breach alerts
- [ ] 30-second heartbeat / ping
- [ ] Handle client disconnections gracefully

## Email Integration (Brevo)

- [ ] Inbound email webhook handler (Brevo signature verification)
- [ ] Auto-create complaint from incoming email
- [ ] Auto-create customer from new email sender
- [ ] Outbound email for resolution notifications

## Dashboards

### Admin Dashboard
- [ ] Complaint feed table with sorting and filtering
- [ ] Search complaints by text
- [ ] Blinking red SLA breach indicator on overdue complaints
- [ ] Complaint detail view with full timeline
- [ ] Analytics panel with 4 charts (by category, priority, status, resolution time trend)
- [ ] User management panel
- [ ] Demo mode toggle (seed 1000 rows / clear demo data)
- [ ] Complaints by hour chart

### QA Dashboard
- [ ] Product complaint count bar chart
- [ ] Trend analysis line chart over time
- [ ] Category deep-dive filters
- [ ] Export to CSV/PDF

### Call Attender Dashboard
- [ ] Active call panel (speech-to-text display placeholder)
- [ ] AI resolution steps display (numbered list)
- [ ] Quick action buttons (Share, Escalate, Log)
- [ ] Recent complaints list
- [ ] Real-time SSE updates integration
- [ ] Limited view (no category/priority visible — just resolution steps and status)

## Analytics

- [ ] Dashboard summary (total, open, resolved, escalated counts)
- [ ] Average resolution time
- [ ] SLA compliance rate percentage
- [ ] Breakdown by category (Product, Packaging, Trade)
- [ ] Breakdown by priority (High, Medium, Low)
- [ ] Breakdown by status
- [ ] Resolution time trend over days
- [ ] Complaints by hour of day
- [ ] Product-level analytics (complaint count, top issues, avg resolution time per product)

## Landing Page

- [ ] Hero section with GSAP text reveal animation
- [ ] Horizontal scroll section (How It Works)
- [ ] Staggered card reveal animations
- [ ] Live stats counter animation
- [ ] Dashboard preview section with parallax
- [ ] CTA buttons with pulse animation
- [ ] Theme toggle (light/dark mode)
- [ ] Mobile responsive design

## Demo Mode

- [ ] Seed 1000 demo complaints from CSV data
- [ ] Clear all demo data
- [ ] Admin-only access to demo controls

## General / Cross-Cutting

- [ ] Health check endpoint (database + ML service status)
- [ ] CORS configuration
- [ ] Error response standard format (code, message, fields)
- [ ] Loading states and skeleton screens
- [ ] Error boundaries
- [ ] API client with retry logic
- [ ] Environment variable configuration (no hardcoded values)
- [ ] Mobile responsive design across all dashboards
- [ ] Theme toggle (light/dark) across entire app