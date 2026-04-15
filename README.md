# Actuator AI

Actuator AI is an event-driven, production-grade multi-agent platform built on the **OpenAI Agents SDK** and orchestrated via **FastAPI**. It leverages a deep **PostgreSQL** relational topology for continuous context management. The system is designed around a Supervisor-Specialist graph pattern to ensure secure, isolated domain handling for enterprise customer support operations.

---

## Technical Architecture

The platform operates using a directed acyclic graph (DAG) routing model where a central **Supervisor Router** acts as the primary ingress node.

### Ingress & State Management
When an HTTP POST hits `/api/v1/chat/`, the FastAPI backend resolves the `conversation_id`. Before passing control to the agent runtime, the core service dynamically reconstructs the entire conversational history directly from PostgreSQL. This ensures that the OpenAI Agents runtime `Runner` executes statelessly while maintaining perfect contextual persistence across distinct temporal boundaries.

### Multi-Agent Handoff Pattern
The **Supervisor Router** runs strict classification algorithms on incoming payloads to determine domain intent. Upon identifying a domain mismatch, it invokes a handoff payload to transfer context, instructions, and execution loop control over to one of seven isolated specialists.

| Specialist Node | Domain Coverage | Operational Access |
|---|---|---|
| **Technical Specialist** | SDK/API diagnostics, incident routing | Selects from `knowledge_base`, creates `support_tickets` |
| **Account Security** | Password resets, 2FA workflows | Reads `users`, writes to `audit_logs` |
| **Billing & Finance** | Invoicing, subscription upgrades | Joins `invoices` & `usage_logs`. Requires HITL on refunds |
| **Success & Retention**| Health checks, renewal offers | Queries `telemetry_logs`, `renewals` |
| **Operations Sync** | CRM synchronization, Jira ticket creation| Bi-directional API tooling (Jira/HubSpot) |
| **Linguistic** | NLP translation, sentiment analysis | Multilingual support and communication QA |
| **Audit** | Policy compliance, QA reviews | Hallucination detection & accuracy scoring |

---

## Infrastructure & Code Topology

```text
actuator-ai/
├── actuator_agents/                 # Isolated Agent Execution Contexts
├── backend/                         # FastAPI Orchestration Layer (Python)
├── frontend/                        # Premium React + Vite + CSS3 UI
├── shared/                          # Universal Context & Tools
├── tests.md                         # Performance & Evaluation Suite
├── pyproject.toml                   # Python dependencies and metadata
└── .env                             # Environment configuration
```

## Component Integration Details

### Database Layer (PostgreSQL)
Driven by **SQLModel**, the relational schema comprises 26 tables in primary groupings:
1. **Agent Memory:** `conversations`, `messages`
2. **Operational Data:** `customers`, `products`, `invoices`, `audit_logs`
3. **RAG Context:** `knowledge_base`, `support_tickets`

### Tooling Abstraction
The platform ships with 60+ native deterministic functions wrapped via `@function_tool`. These tools execute parameterized SQL queries using `psycopg3`. All tools specify strict Pydantic typed input constraints to ensure the LLM generates valid JSON schemas prior to execution.

### Security Guardrails
Input requests are pipelined through `InputGuardrailTripwireTriggered` middleware:
- **Injection Prevention:** Blocks boolean-based or UNION-based injection prompts.
- **Jailbreak Detection:** System prompt override detection.
- **PII Scrubbing:** Redacts unencrypted SSN and Credit Card strings before inference execution.

### Human-in-the-Loop (HITL) Execution
Functions tagged with `@function_tool(needs_approval=True)` automatically trap the continuous agent running state. When an agent attempts execution (e.g., `process_refund`), the SDK yields an interruption tuple to FastAPI. Execution is forcibly paused pending cryptographic authorization from a human manager. Overages below strict limits bypass the authorization constraint.

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
   npm install
   npm run build
   cp -r dist/* ../backend/static/
   ```

3. **Database Configuration:**
   Ensure PostgreSQL is running locally on port `5432` with a database named `actuator_ai`.

4. **Environment Variables:**
   Update `.env` locally. Ensure `OLLAMA_MODEL` points to an aggressive parameter tool-calling model (e.g., `qwen3.5:cloud`).

5. **Start Application Server:**
   ```bash
   uv run uvicorn backend.main:app --port 8000
   ```

6. **Access Execution UI:**
   Navigate to [http://localhost:8000](http://localhost:8000).

7. **Extensive Testing Suite:**
   Refer to `tests.md` for pre-verified scenarios targeting specific agent handoffs and tool executions.

---

## Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Agent SDK | **OpenAI Agents SDK v0.13+** | Native handoff support and strict context management natively. |
| Backend API | **FastAPI** | Concurrent async execution for multi-specialist flows. |
| User Interface | **React + Vite** | Blazing fast rendering with modern client-side routing. |
| Datastore | **PostgreSQL + SQLModel** | Relational integrity preventing ORM mapping overhead. |
| Inference Engine | **Ollama** | Seamless local execution wrapper for LLM swapping. |
| Extensibility | **MCP Protocol** | Architecture supports dynamic `@modelcontextprotocol` bindings. |
