# Actuator AI

Event-driven, production-grade multi-agent platform utilizing the **OpenAI Agents SDK**. Orchestrated via **FastAPI** with continuous context management over a deep **PostgreSQL** topology. Designed around a Supervisor-Specialist graph pattern for secure, isolated domain handling.

---

## Recent Updates: Premium Experience
We have revamped the platform with a high-performance **React + Vite** frontend featuring:
- **Glassmorphism Design:** A modern, premium interface with backdrop blurs and smooth transitions.
- **Dynamic Theming:** Deep indigo/slate palette optimized for readability and visual comfort.
- **Real-time Agent Tracking:** Live status indicators for the 7 specialists online.
- **Clean Execution:** Removed clutter (like legacy profile boxes) to focus on the conversation flow.

---

## Technical Architecture & Agent Graph

The platform operates using a directed acyclic graph (DAG) routing model where a central **Supervisor Router** acts as the primary ingress node.

### Multi-Agent Handoff Pattern
The **Supervisor Router** runs strict classification algorithms on incoming payloads to determine domain intent. Upon identifying a domain mismatch, it invokes a handoff payload to transfer context, instructions, and execution loop control over to one of 7 isolated specialists.

| Specialist Node | Domain Coverage | Read/Write Access Clearance |
|---|---|---|
| **Technical Specialist** | SDK/API diagnostics, incident routing | Selects from `knowledge_base`, creates `tickets` |
| **Account Security** | Password resets, 2FA workflows | Reads `users`, writes to `audit_logs` |
| **Billing & Finance** | Invoicing, subscription upgrades | Joins `invoices` & `usage_logs`. **Interrupts** on refunds |
| **Success & Retention**| Health checks, renewal offers | Queries `telemetry_logs`, `renewals` |
| **Operations Sync** | CRM sync, Jira ticket creation | Bi-directional API tooling (Jira/HubSpot) |
| **Linguistic** | NLP translation, sentiment analysis | Multilingual support (Urdu, Arabic, etc.) |
| **Audit** | Policy compliance, QA reviews | Hallucination detection & accuracy scoring |

---

## Infrastructure & Code Topology

```
actuator-ai/
│
├── actuator_agents/                 # Isolated Agent Execution Contexts
├── backend/                         # FastAPI Orchestration Layer (Python)
├── frontend/                        # Premium React + Vite + CSS3 UI
├── shared/                          # Universal Context & Tools
├── tests.md                         # Performance & Evaluation Suite
├── pyproject.toml
└── .env
```

---

## Deployment & Quick Start

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/the-schoolofai/actuator-ai.git
   cd actuator-ai
   uv sync
   ```

2. **Frontend Build (Optional for static serving):**
   ```bash
   cd frontend
   npm install && npm run build
   cp -r dist/* ../backend/static/
   ```

3. **Start Application:**
   ```bash
   uv run uvicorn backend.main:app --port 8000
   ```

4. **Testing Suite:**
   Refer to `tests.md` for pre-verified prompts to test specific agent handoffs and tool executions.

---

## Tech Stack Deep Dive

| Component | Technology | Why |
|---|---|---|
| Agent SDK | **OpenAI Agents SDK** | Native handoff support and strict context management. |
| Backend | **FastAPI** | Concurrent async execution for multi-specialist flows. |
| UI | **React + Vite** | Blazing fast rendering with modern premium aesthetics. |
| Database | **PostgreSQL** | Relational integrity for 26-table agent topology. |
| Memory | **Stateless Graph** | Context persisted in PG, allowing horizontal scaling. |
