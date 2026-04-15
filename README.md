# Actuator AI

Event-driven, production-grade multi-agent platform utilizing the **OpenAI Agents SDK**. Orchestrated via **FastAPI** with continuous context management over a deep **PostgreSQL** topology. Designed around a Supervisor-Specialist graph pattern for secure, isolated domain handling.

---

## Technical Architecture & Agent Graph

The platform operates using a directed acyclic graph (DAG) routing model where a central **Supervisor Router** acts as the primary ingress node.

### Ingress & State Management
When an HTTP POST hits `/api/v1/chat/`, the FastAPI backend resolves the `conversation_id`. Before passing control to the agent runtime, the core service constructs the entire conversational history dynamically directly from PostgreSQL. This ensures that the OpenAI Agents runtime `Runner` executes statelessly, while maintaining perfect contextual persistence across distinct temporal boundaries.

### Multi-Agent Handoff Pattern
The **Supervisor Router** runs strict classification algorithms on incoming payloads to determine domain intent. Upon identifying a domain mismatch, it invokes a handoff payload to transfer context, instructions, and execution loop control over to one of 7 isolated specialists.

| Specialist Node | Domain Coverage | Read/Write Access Clearance |
|---|---|---|
| **Technical Specialist** | SDK/API diagnostics, incident routing | Selects from `knowledge_base`, creates `tickets` |
| **Account Security** | Password resets, 2FA workflows | Reads `users`, writes to `audit_logs` |
| **Billing & Finance** | Invoicing, subscription upgrades | Joins `invoices` & `usage_logs`. **Interrupts** on refunds |
| **Success & Retention**| Health checks, NPS | Queries `telemetry_logs`, `renewals` |
| **Operations Sync** | Internal CRM ticket scraping | Bi-directional API tooling |
| **Linguistic** | NLP QA, semantic sentiment | Local LLM transformation tasks |
| **Audit** | Policy QA constraint checking | Verifies hallucination parameters |

---

## Infrastructure & Code Topology

```
actuator-ai/
│
├── actuator_agents/                 # Isolated Agent Execution Contexts
│   ├── supervisor_router/           # Ingress Node & Handoff Map
│   ├── billing_finance/             # Target Node (HITL restricted)
│   ├── technical_specialist/        # Target Node (RAG enabled)
│   ├── ... 
│
├── backend/                         # FastAPI Orchestration Layer
│   ├── api/routes/chat.py           # HTTP Request Handlers
│   ├── core/                        # System configurations / environment bindings 
│   ├── models/                      # SQLModel ORM classes corresponding to PG tables
│   ├── services/agent_service.py    # Hydrates `EasyInputMessageParam` from DB records
│   └── static/                      # Minimal React/Vanilla integration endpoints
│
├── shared/                          # Universal Context & Constraints
│   ├── models/                      # LiteLLM/Ollama abstraction wrappers
│   ├── tools/                       # 60+ unified tools wrapped in `@function_tool`
│   └── guardrails/                  # Injection/PII regex middleware validators
│
├── README.md
├── pyproject.toml
└── .env
```

---

## Component Integration Details

### Database Layer (PostgreSQL)
Driven by **SQLModel**, the relational schema comprises 26 tables.
Primary groupings:
1. `conversations` & `messages` (Agent Memory)
2. `customers`, `products`, `invoices` (Operational Data)
3. `knowledge_base`, `support_tickets` (RAG Context)

### Tools Array (`@function_tool` Abstraction)
The platform ships with 61 native deterministic functions. These tools directly execute SQL parameterized queries using psycopg3 under the hood. All tools specify strict Pydantic typed input constraints to ensure the LLM generates valid JSON schemas prior to execution.

### Security Guardrails
Input requests are pipelined through `InputGuardrailTripwireTriggered` middleware.
- **`detect_sql_injection`**: Blocks standard boolean-based or UNION-based injection prompts targeting internal DB tools.
- **`detect_jailbreak`**: System prompt override detection.
- **`detect_pii`**: Redacts unencrypted SSN / CC strings before inference execution.

### Human-in-the-Loop (HITL) Execution
Methods tagged with `@function_tool(needs_approval=True)` automatically trap the continuous agent running state. When an agent attempts an execution on this tool (e.g. `process_refund`), the SDK yields an interruption tuple to FastAPI. The execution is forcibly paused pending a cryptographic/authorization handshake from a human manager. Overages below strict limits (e.g., $15 credit) bypass the authorization constraint.

---

## Deployment & Quick Start

1. **Clone the Repo:**
   ```bash
   git clone https://github.com/the-schoolofai/actuator-ai.git
   cd actuator-ai
   ```

2. **Setup Dependencies:**
   Built firmly with `uv` for sub-second virtualenv resolution.
   ```bash
   uv sync
   ```

3. **Database Setup:**
   Ensure PostgreSQL is running locally on port `5432` with a database named `actuator_ai`.

4. **Environment Variables:**
   Update `.env` locally. Ensure `OLLAMA_MODEL` points to an aggressive parameter tool-calling model (e.g., `qwen3.5:cloud` or an equivalent proxy).

5. **Start Application Server:**
   Starts the ASGI Uvicorn workers bindings on the specified port.
   ```bash
   uv run uvicorn backend.main:app --port 8000
   ```

6. **Access Execution UI:**
   Navigate to [http://localhost:8000](http://localhost:8000) to trace standard POST requests to the conversational API.

---

## Tech Stack Deep Dive

| Component | Technology | Why |
|---|---|---|
| Agent Orchestration | **OpenAI Agents SDK v0.13+** | Supports strict JSON schema execution, typed tool constraints, and async context tracking natively. |
| API Layer | **FastAPI** | Uvicorn-backed asynchronous event loops are required so parallel agent executions do not block the main IO thread. |
| Memory Persistence | **PostgreSQL + SQLModel** | Pydantic validation directly mapped natively into SQLAlchemy execution statements prevents ORM mapping overhead. |
| Inference Engine | **Ollama** | Seamless execution wrapper for LLM swapping without modifying inference APIs. |
| Extensibility | **MCP Readiness** | Architecture allows swapping Python ORM tools for direct `@modelcontextprotocol/server-postgres` binding dynamically. |
