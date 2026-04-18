Let me design the full architecture — this will have a lot of careful coordinate planning to get right.*(Click any box to go deeper on that component.)*

---

Here's the full architecture plan for your multi-agent voice complaint system.

**The core idea** is a hub-and-spoke orchestration: a single stateful Orchestrator owns every session from the moment the user speaks to the moment the ticket is closed, delegating atomically to specialized agents rather than having agents call each other. This keeps it powerful without becoming a tangled mesh.

Here’s a clean, structured description you can give to a text model as reference for the diagram:

---

**System Overview: AI-Powered Voice-Based Complaint Management Architecture**

This system represents a multi-layered AI architecture designed to handle user complaints through voice interaction, automate classification and resolution, and provide operational insights.

### 1. User Layer

* The system begins with the **User**, who interacts via voice input and receives responses.

### 2. Voice I/O Agent (Voice Pipeline)

* Acts as the interface between the user and the system.
* Components:

  * **Speech-to-Text (STT)** using Whisper
  * **Text-to-Speech (TTS)** for responses
  * **Voice Activity Detection (VAD)** for detecting speech segments
* Converts user voice into text and system responses back into voice.

### 3. Orchestrator (Core Intelligence Controller)

* Central brain of the system.
* Responsibilities:

  * Maintains **state machine**
  * Routes tasks to appropriate agents (**agent router**)
  * Manages **session context**
  * Tracks **SLA (Service Level Agreement) timing**
* Ensures smooth coordination between all modules.

### 4. Intelligence Layer (Core Functional Agents)

These modules process and act on the user’s complaint:

* **Dialog Agent**

  * Extracts key information from user input
  * Maintains conversational context

* **Classify Agent**

  * Determines complaint type
  * Ranks severity or priority

* **Resolve Agent**

  * Suggests possible fixes or solutions
  * May use knowledge base or past cases

* **Ticket Agent**

  * Creates and tracks support tickets
  * Monitors SLA compliance

* **Analytics Agent**

  * Generates KPI metrics
  * Tracks performance and trends

### 5. Role-Based Dashboards

Outputs are tailored for different organizational roles:

* **Support Executive**

  * Access to live ticket queue
  * Handles real-time customer issues

* **QA Team**

  * Monitors accuracy and patterns
  * Evaluates system performance

* **Operations Manager**

  * Oversees SLA adherence
  * Reviews KPIs and ticket volume

### 6. Layers Summary

* **Voice Pipeline**: Handles voice input/output
* **Intelligence Layer**: Core AI processing and decision-making
* **Role Dashboards**: End-user views for different stakeholders
* **User Interface Layer**: Connects system outputs to human users

---

**How a complaint flows end-to-end**

The user speaks. The Voice I/O Agent hits your existing STT server (Whisper + Silero VAD), gets clean transcribed text, and hands it to the Orchestrator with a session ID. The Orchestrator checks its state machine — if this is a new session, it kicks the Dialog Agent to drive a short multi-turn conversation that extracts the structured complaint: what happened, which product/trade/package is involved, and any urgency signals. Once the Dialog Agent returns a structured payload, the Orchestrator fires the Classify Agent, which calls your existing FastAPI classifier to get category, VADER sentiment, and DecisionTree priority in one shot. The Resolve Agent then takes that structured + classified complaint and calls the best-ranked LLM from your ablation study to generate 2-3 specific resolution steps (escalate / refund / follow-up / exchange — not generic text). The Ticket Agent persists everything to SQLite with a created timestamp and SLA countdown ticking. Finally, the Orchestrator synthesizes a response, the Voice I/O Agent converts it to TTS, and the user hears a confirmation with their ticket number and next action.

All five agents publish their outputs onto the results bus simultaneously, and the Analytics Agent aggregates these into live KPI state that all three dashboards consume.

---

**The five agents and your existing infrastructure**

The Dialog Agent is a lightweight LLM call (3-4 turns max) with a fixed extraction schema — it returns `{complaint_type, description, channel, customer_id}`. The Classify Agent is just an HTTP client to your existing `/predict` endpoint; no new ML needed. The Resolve Agent calls the top model from your ablation (Gemini 2.5 Flash was likely your winner given the task mix) with a structured prompt templated around the classified complaint. The Ticket Agent does CRUD against SQLite and manages SLA state transitions: `open → in_progress → resolved → closed`. The Analytics Agent incrementally updates in-memory counters (complaint volume by category, priority distribution, SLA breach count, average resolution time) and pushes them to a WebSocket endpoint that the dashboards poll.

---

**What each role actually sees**

The Customer Support Executive sees a live queue of open tickets ordered by priority (High first), each showing the auto-detected category badge, VADER sentiment indicator, and the 2-3 resolution steps pre-filled by the Resolve Agent. They don't classify anything — they just act on recommendations and update ticket status.

The QA Team's dashboard is about pattern detection: category distribution over time, misclassification flags (where the user corrected the auto-tag), recurring complaint phrases by SKU or trade partner, and resolution consistency scores. This feeds directly from the Analytics Agent which tracks both the Classify Agent's output and any manual overrides.

The Operations Manager gets the KPI view: complaint volume heatmap split by Product / Trade / Packaging, SLA compliance rate (% resolved within threshold by priority tier), average resolution time trending over rolling 7 days, and an alert rail that fires when any category spikes or SLA breach rate crosses a threshold.

---

**What to build next, in order**

The Orchestrator + Ticket Agent is the backbone — build this first as a simple FastAPI service with SQLite and a state machine (three states: `collecting`, `classifying`, `resolved`). Then wire in Classify Agent (just an HTTP call to your existing server). Then add Dialog Agent (a single LLM call with an extraction prompt). Then Resolve Agent (LLM call with resolution prompt using your ablation winner). The KPI Dashboard can be a React frontend polling a `/dashboard` endpoint that the Analytics Agent updates after every ticket event. The Voice I/O Agent wraps your existing STT server and adds a TTS layer (Coqui TTS or ElevenLabs API call). Export (PDF/CSV) is the last feature — just a reporting endpoint on the Ticket Agent.

The whole system can be a single Python monorepo: one `orchestrator/` service, five `agents/` modules, one `dashboard/` React app, and your three existing servers running in parallel.

Want me to start coding the Orchestrator + state machine, or the KPI Dashboard frontend first?