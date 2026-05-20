<div align="center">

# ⚡ Actuator AI

**Enterprise-Grade Multi-Agent Customer Support Orchestration Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135.3+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OpenAI Agents SDK](https://img.shields.io/badge/OpenAI_Agents_SDK-0.13.6+-412991?style=flat&logo=openai&logoColor=white)](https://github.com/openai/openai-agents-python)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=white)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)](LICENSE)

**8 specialized AI agents · Real-time database access via MCP · Human-in-the-loop approvals · Three-layer security guardrails**

</div>

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Request Lifecycle](#request-lifecycle)
3. [Agent Specialization Matrix](#agent-specialization-matrix)
4. [Technology Stack](#technology-stack)
5. [Database Schema](#database-schema)
6. [Security & Guardrail Pipeline](#security--guardrail-pipeline)
7. [MCP Integration](#mcp-model-context-protocol-integration)
8. [Human-in-the-Loop (HITL) Workflows](#human-in-the-loop-hitl-workflows)
9. [Model Inference Architecture](#model-inference-architecture)
10. [Setup & Installation](#setup--installation)
11. [API Reference](#api-reference)
12. [Project Structure](#project-structure)
13. [Development Workflow](#development-workflow)
14. [Production Deployment](#production-deployment)
15. [Monitoring & Observability](#monitoring--observability)

---

## Architecture Overview

Actuator AI is built on a **supervisor-router pattern** using the OpenAI Agents SDK. A central supervisor agent classifies incoming customer requests and routes them to specialized agents, each equipped with domain-specific tools and real-time PostgreSQL access via the Model Context Protocol (MCP).

### Core Architectural Decisions

#### 1. Per-Request MCP Isolation

Each WebSocket request receives a **fresh** `MCPServerStdio` instance. This prevents singleton lifecycle conflicts that manifest as `"Server not initialized"` errors during agent handoffs:

```python
# shared/mcp_config.py
def create_mcp_postgres() -> MCPServerStdio:
    db_url = (
        f"postgres://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )
    return MCPServerStdio(
        params=MCPServerStdioParams(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres", db_url],
            client_session_timeout_seconds=30.0,
        )
    )
```

#### 2. Guardrail Poisoning Prevention

Messages blocked by guardrails are **never persisted** to the conversation history. They are stored with `agent_name = 'Guardrail'` and filtered out during history reconstruction, preventing re-triggering on subsequent clean messages:

```python
# backend/services/agent_service.py
prior_messages = db.exec(
    select(Message)
    .where(Message.conversation_id == conversation_id)
    .where(Message.agent_name != "Guardrail")  # Skip blocked exchanges
    .order_by(Message.created_at)
).all()
```

#### 3. SQL Strictness Enforcement

To prevent local LLMs from hallucinating schema objects and entering retry loops, each agent prompt enforces copy-paste SQL patterns:

```
WARNING: DO NOT WRITE YOUR OWN SQL QUERIES. YOU MUST COPY AND PASTE
THESE EXACT SQL PATTERNS. NEVER INVENT TABLES OR COLUMNS!
```

#### 4. Asynchronous Request Serialization

A module-level `asyncio.Lock` prevents concurrent requests from clashing on shared agent object state:

```python
_run_lock = asyncio.Lock()

async with _run_lock:
    mcp = create_mcp_postgres()
    await mcp.connect()
    for ag in _ALL_AGENTS:
        ag.mcp_servers = [mcp]
    # ... run agent pipeline ...
    for ag in _ALL_AGENTS:
        ag.mcp_servers = []
    await mcp.cleanup()
```

---

## Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             REQUEST LIFECYCLE                               │
└─────────────────────────────────────────────────────────────────────────────┘

Client (React SPA)
    │
    ▼ WebSocket /api/v1/chat/ws
┌────────────────────────────────────────────────┐
│ 1. FastAPI accepts WebSocket connection         │
│ 2. Deserializes: {message, conversation_id,     │
│                   customer_email}               │
│ 3. Creates/retrieves Conversation from DB       │
│ 4. Rebuilds history (filtering Guardrail msgs)  │
└──────────────────┬─────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────┐
│ 5. Creates fresh MCPServerStdio instance        │
│ 6. Acquires _run_lock                          │
│ 7. Assigns MCP to all 8 agents                 │
│ 8. Calls Runner.run_streamed(supervisor, input) │
└──────────────────┬─────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────┐
│ 9. Supervisor.classify_request()                │
│    → Category detection via keyword scoring     │
│    → Priority assignment (urgent signal check)  │
│                                                 │
│ 10. Supervisor transfers to specialist agent    │
│     via handoff (agent_update event emitted)    │
│                                                 │
│ 11. Specialist agent:                           │
│     a. Queries PostgreSQL via MCP 'query' tool  │
│     b. Calls domain function_tools              │
│     c. Streams ResponseTextDelta events         │
│     d. Optionally creates support tickets       │
└──────────────────┬─────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────┐
│ 12. Client UI:                                  │
│     • text events → update streaming message    │
│     • agent_update → split message bubble       │
│     • done → finalize + close WebSocket         │
│     • error → display error message             │
│                                                 │
│ 13. On completion:                              │
│     • Persist user + assistant messages to DB   │
│     • Update conversation.last_agent            │
│     • Clear MCP references                      │
│     • Run mcp.cleanup() in finally block         │
│     • Release _run_lock                         │
└────────────────────────────────────────────────┘
```

### Stream Event Protocol

The WebSocket stream yields JSON events with the following type discriminator:

| Event Type | Direction | Payload | Description |
|---|---|---|---|
| `conv_id` | Server → Client | `{conversation_id}` | Assigned conversation UUID |
| `content` | Server → Client | `{agent_name, content}` | Incremental response tokens |
| `agent_update` | Server → Client | `{agent_name}` | Agent handoff notification |
| `done` | Server → Client | `{needs_approval, approval_items}` | Stream termination signal |
| `error` | Server → Client | `{content, agent_name}` | Processing failure |

---

## Agent Specialization Matrix

### Supervisor Router

The central orchestrator. Every customer message enters through this agent.

| Aspect | Detail |
|---|---|
| **Domain** | Request triage, classification, escalation |
| **Tools** | `classify_request`, `escalate_to_human` |
| **Handoffs** | 7 specialist agents |
| **Guardrails** | Jailbreak, PII, SQL injection |
| **Model** | `qwen2.5:7b` (temp: 0.2, max_tokens: 800) |

The supervisor uses keyword-based intent classification with weighted scoring across 7 categories, then immediately transfers to the matching specialist via the SDK's handoff mechanism.

### Technical Specialist

Diagnoses API errors, SDK issues, and infrastructure problems.

| Aspect | Detail |
|---|---|
| **Domain** | API errors, SDK issues, system diagnostics, knowledge base |
| **Tools** | `diagnose_service`, `check_system_status`, `create_support_ticket`, MCP `query` |
| **DB Access** | `knowledge_articles`, `support_tickets` |
| **Model** | `qwen2.5:7b` (temp: 0.2, max_tokens: 1200) |

Protocol: Search KB first → Check system status → Diagnose error → Create ticket if unresolved.

### Account Security Agent

Handles authentication, 2FA, lockouts, and profile management.

| Aspect | Detail |
|---|---|
| **Domain** | Login issues, 2FA setup/reset, password reset, account unlock, profile updates |
| **Tools** | `unlock_account`, `initiate_2fa_setup`, `reset_2fa`, `initiate_password_reset`, `update_profile`, MCP `query` |
| **DB Access** | `customers`, `customer_contacts`, `security_events` |
| **Model** | `qwen2.5:7b` (temp: 0.2, max_tokens: 1000) |

Protocol: Query account → Check lock/2FA status → Execute tool → Log security event.

### Billing Finance Agent

Manages invoices, payments, refunds, and subscription changes.

| Aspect | Detail |
|---|---|
| **Domain** | Invoices, payments, refunds, plan changes, credits, usage |
| **Tools** | `change_plan`, `process_refund*`, `apply_credit`, MCP `query` |
| **DB Access** | `invoices`, `invoice_line_items`, `subscriptions`, `products`, `payments`, `refunds`, `api_usage` |
| **Model** | `qwen2.5:7b` (temp: 0.2, max_tokens: 1000) |

`*` `process_refund` has `needs_approval=True` — requires human-in-the-loop intervention.

### Success Retention Agent

Monitors customer health, prevents churn, and drives feature adoption.

| Aspect | Detail |
|---|---|
| **Domain** | Health scores, renewal offers, churn intervention, feature adoption |
| **Tools** | `schedule_check_in`, `create_renewal_offer`, `log_churn_intervention`, MCP `query` |
| **DB Access** | `customers`, `api_usage`, `feature_flags`, `feedback`, `support_tickets` |
| **Model** | `qwen2.5:7b` (temp: 0.4, max_tokens: 1200) |

Protocol: Query health → Analyze usage trend → Check feature adoption → Review feedback → Take action.

### Operations Sync Agent

Manages CRM records, support tickets, and Jira integration.

| Aspect | Detail |
|---|---|
| **Domain** | CRM updates, Jira tickets, support tickets, task tracking, notifications |
| **Tools** | `update_crm_note`, `create_support_ticket`, `create_jira_ticket`, `update_jira_ticket`, MCP `query` |
| **DB Access** | `support_tickets`, `ticket_comments`, `notifications_log` |
| **Model** | `qwen2.5:7b` (temp: 0.2, max_tokens: 1000) |

### Linguistic Agent

Handles multi-language support, sentiment analysis, and communication QA.

| Aspect | Detail |
|---|---|
| **Domain** | Language detection, translation, sentiment analysis, communication quality |
| **Tools** | `detect_language`, `translate_text`, `analyze_sentiment`, `assess_communication_quality`, MCP `query` |
| **DB Access** | `feedback` (optional baseline lookup) |
| **Model** | `qwen2.5:7b` (temp: 0.3, max_tokens: 1000) |

### Audit Agent

Quality assurance, hallucination detection, and policy compliance verification.

| Aspect | Detail |
|---|---|
| **Domain** | QA review, hallucination detection, policy compliance, accuracy scoring, conversation audits |
| **Tools** | `check_hallucination`, `check_policy_compliance`, `audit_conversation`, `score_response_accuracy`, `generate_qa_report`, MCP `query` |
| **DB Access** | `audit_logs`, `escalations`, `conversations`, `messages` |
| **Model** | `qwen2.5:7b` (temp: 0.1, max_tokens: 1200) |

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Agent Framework** | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | ≥0.13.6 | Multi-agent orchestration, handoffs, guardrails |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) | ≥0.135.3 | REST endpoints + WebSocket streaming |
| **Database ORM** | [SQLModel](https://sqlmodel.tiangolo.com) | ≥0.0.38 | Type-safe PostgreSQL models |
| **Database Driver** | [psycopg2](https://www.psycopg.org) | ≥2.9.11 | PostgreSQL adapter |
| **Database Access** | [MCP PostgreSQL Server](https://github.com/modelcontextprotocol/servers) | — | Real-time SQL tool access via MCP |
| **Authentication** | [bcrypt](https://github.com/pyca/bcrypt) + [PyJWT](https://github.com/jpadilla/pyjwt) | ≥5.0.0 + ≥2.12.1 | Password hashing + JWT tokens |
| **Configuration** | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | ≥2.13.1 | Type-safe environment configuration |
| **LLM Inference** | [Ollama](https://ollama.com) | ≥0.6.1 | Local model hosting (OpenAI-compatible API) |
| **HTTP Client** | [httpx](https://www.python-httpx.org) | ≥0.28.1 | Async HTTP requests (web search, APIs) |
| **Frontend** | [React](https://react.dev) 19 + [Vite](https://vite.dev) 8 | — | Modern SPA with HMR |
| **State Management** | [Zustand](https://github.com/pmndrs/zustand) | 5.0.12 | Lightweight React state |
| **UI Components** | [Lucide React](https://lucide.dev) | 1.8.0 | Consistent iconography |
| **Routing** | [React Router DOM](https://reactrouter.com) | 7.14.2 | Client-side SPA routing |
| **Animations** | [Framer Motion](https://www.framer.com/motion) | 12.38.0 | Page/component transitions |
| **Markdown** | [marked](https://marked.js.org) | 18.0.0 | Secure message rendering |

---

## Database Schema

**26 tables organized into 5 logical domains** with comprehensive seed data simulating a real SaaS customer support platform.

### Domain Map

```
🗣️  Conversation State (2 tables)
    conversations, messages
    → Core chat persistence with token/latency tracking

👥  Customer Data (4 tables)
    customers, customer_contacts, subscriptions, products
    → Multi-contact per customer, tiered subscription model

🔐  Authentication (1 table)
    customer (FastAPI Auth model with hashed_password)
    → bcrypt-hashed credentials, JWT token generation

💰  Billing & Payments (6 tables)
    invoices, invoice_line_items, payments, refunds, api_usage, feature_flags
    → Full billing lifecycle with refund chains

⚙️  Operational Systems (13 tables)
    support_tickets, ticket_comments, knowledge_articles
    escalations, notifications_log, agents_config
    security_events, audit_logs, feedback
    → Complete support operations with security auditing
```

### Key Design Patterns

- **Composite primary keys**: Invoices use `VARCHAR(20)` with format `INV-YYYY-NNNN` for human-readable identifiers
- **JSONB columns**: `features`, `details`, `tool_calls` use PostgreSQL JSONB for flexible schema
- **Array columns**: `tags` uses `TEXT[]` for efficient categorization
- **CHECK constraints**: `feedback.rating` and `feedback.nps_score` have range validation
- **Indexed foreign keys**: 15+ composite indexes on high-query columns

### Entity Relationships

```
customers ──┬── customer_contacts (1:N)
             ├── subscriptions (1:N)
             ├── invoices (1:N)
             ├── api_usage (1:N)
             ├── feature_flags (1:N)
             ├── support_tickets (1:N)
             ├── feedback (1:N)
             └── conversations (1:N)

subscriptions ── products (N:1)
invoices ──┬── invoice_line_items (1:N)
           └── payments (1:N) ── refunds (1:N)

support_tickets ──┬── ticket_comments (1:N)
                  └── escalations (1:N)

audit_logs ── conversations (N:1)
conversations ── messages (1:N)
```

### Seed Data Overview

The `seed.sql` contains realistic data for:
- **10 customers** across healthcare, fintech, gaming, logistics, edtech, and more
- **14 contacts** with roles (CTO, CIO, CISO, CEO) in multiple timezones
- **4 product tiers** (Free → Enterprise Plus) with granular feature flags
- **12 invoices** with payment/refund chains showing paid, overdue, and pending states
- **9 support tickets** with SLA deadlines, CSAT scores, and escalation chains
- **16 security events** including login failures, account locks, 2FA verification
- **12 knowledge articles** across API, SDK, security, billing, and deployment categories
- **8 audit logs** with hallucination risk scores and quality metrics

---

## Security & Guardrail Pipeline

### Three-Layer Input Validation

Three `InputGuardrail` functions execute **before** any agent processes incoming messages:

```python
# shared/guardrails/safety.py

@input_guardrail(name="Jailbreak Detector")
async def detect_jailbreak(ctx, agent, input):
    """Pattern matching on override/injection phrases."""
    patterns = ["ignore your instructions", "DAN mode", "<|im_start|>", ...]
    # Returns GuardrailFunctionOutput(tripwire_triggered=True/False)

@input_guardrail(name="PII Detector")
async def detect_pii(ctx, agent, input):
    """Regex patterns for CC numbers and SSNs."""
    # re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', text)
    # re.search(r'\b\d{3}-\d{2}-\d{4}\b', text)

@input_guardrail(name="SQL Injection Detector")
async def detect_sql_injection(ctx, agent, input):
    """Keyword matching for SQL injection attempts."""
    patterns = ["DROP TABLE", "DELETE FROM", "OR 1=1", "UNION SELECT", ...]
```

### Guardrail Isolation Protocol

1. Guardrail triggers → `InputGuardrailTripwireTriggered` exception raised
2. Exception caught in `run_chat_stream()` — user message **not** persisted
3. Assistant message stored with `agent_name = "Guardrail"`
4. History reconstruction filters `WHERE agent_name != 'Guardrail'`
5. Subsequent clean messages never re-trigger on blocked content

### Output Validation

`check_response_length` — blocks responses exceeding 3000 characters (cost/quality control):

```python
@output_guardrail(name="Response Length Check")
async def check_response_length(ctx, agent, output):
    if len(str(output)) > 3000:
        return GuardrailFunctionOutput(tripwire_triggered=True,
            output_info=f"Response too long: {len(str(output))} chars")
    return GuardrailFunctionOutput(tripwire_triggered=False, output_info="OK")
```

---

## MCP (Model Context Protocol) Integration

### Architecture

```
┌─────────────────────┐     ┌───────────────────────┐
│  MCPServerStdio     │────▶│  npx -y               │
│  (Per-Request)      │     │  @modelcontextprotocol │
│                     │     │  /server-postgres      │
│  timeout: 30s       │     │  <connection_string>   │
└─────────────────────┘     └───────────┬───────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │   PostgreSQL 14+  │
                               │   actuator_ai DB  │
                               └──────────────────┘
```

### Lifecycle Management

```python
# backend/services/agent_service.py — Lifecycle pattern

async def run_chat_stream(...):
    mcp = create_mcp_postgres()
    await mcp.connect()          # Phase 1: Initialize
    
    for ag in _ALL_AGENTS:
        ag.mcp_servers = [mcp]   # Phase 2: Assign to all agents
    
    try:
        result = Runner.run_streamed(supervisor, input_list, ...)
        # ... stream events ...
    finally:
        for ag in _ALL_AGENTS:
            ag.mcp_servers = []  # Phase 3: Clear references
        await mcp.cleanup()      # Phase 4: Graceful shutdown
```

### Why Per-Request Isolation?

The OpenAI Agents SDK's `MCPServerStdio` has an internal state machine for `connect/disconnect`. When agent handoffs occur mid-conversation, sharing a single MCP instance between multiple agents causes race conditions on the MCP lifecycle. The factory pattern guarantees each request gets an isolated MCP instance with a clean state.

---

## Human-in-the-Loop (HITL) Workflows

### Approval-Based Workflow Interruption

The `process_refund` tool uses `@function_tool(needs_approval=True)` to trap execution mid-chain:

```python
@function_tool(needs_approval=True)
def process_refund(email: str, invoice_id: str, amount: float, reason: str) -> str:
    """Process a refund. REQUIRES MANAGER APPROVAL."""
    # Create refund record with status='pending'
    return f"Refund {refund_id}: Pending approval"
```

### HITL Flow

```
1. Agent calls process_refund(email, invoice, amount, reason)
2. SDK yields result.interruptions → FastAPI catches this
3. API returns to frontend:
   {
     "needs_approval": true,
     "approval_items": ["process_refund"]
   }
4. Frontend displays amber warning banner with approval prompt
5. Human supervisor approves via Runner state resumption:
   state = result.to_state()
   state.approve(interruption)
   result = await Runner.run(supervisor, state)
6. Execution continues with refund processing
```

---

## Model Inference Architecture

### Supported Providers

| Provider | Backend | Use Case | Configuration |
|---|---|---|---|
| **Ollama** | `AsyncOpenAI` (OpenAI-compatible) | Local inference (default) | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| **Groq** | `AsyncOpenAI` | Fast cloud inference | `GROQ_API_KEY` |
| **OpenAI** | Native SDK model string | Cloud inference | `OPENAI_API_KEY` |
| **LiteLLM** | `LitellmModel` | 100+ provider gateway | Provider-specific |

### Shared Client & Connection Pooling

All agents use a shared, lazily-initialized `AsyncOpenAI` client for connection pooling:

```python
# shared/models/ollama_provider.py
_client = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    return _client

def get_model(model_name: str | None = None) -> OpenAIChatCompletionsModel:
    return OpenAIChatCompletionsModel(
        model=model_name or OLLAMA_DEFAULT_MODEL,
        openai_client=_get_client(),
    )
```

### Recommended Models

| Model | Strength | Provider |
|---|---|---|
| `deepseek-v3.1:671b-cloud` | Strongest tool calling, agentic chains | Ollama Cloud |
| `gpt-oss:120b-cloud` | GPT architecture, native tool schema | Ollama Cloud |
| `qwen3-coder:480b-cloud` | Structured output & code reasoning | Ollama Cloud |
| `qwen2.5:7b` | Lightweight default for local inference | Local Ollama |

---

## Setup & Installation

### Prerequisites

- **PostgreSQL 14+** with database `actuator_ai`
- **Python 3.11+** with [`uv`](https://docs.astral.sh/uv/) package manager
- **Node.js 18+** and **npm** (frontend development)
- **Ollama** running locally with target model pulled
- **Redis** (optional, for production session storage)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/PatheticUser/agentic-ai-hub.git
cd actuator-ai

# 2. Create Python virtual environment with uv
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Install backend dependencies
uv pip install -e .

# 4. Set up the database
psql -U postgres -c "CREATE DATABASE actuator_ai;"
psql -U postgres -d actuator_ai -f backend/db/schema.sql
psql -U postgres -d actuator_ai -f backend/db/seed.sql

# 5. Install frontend dependencies
cd frontend
npm install
cd ..

# 6. Configure environment
# Create .env from the template below and edit with your configuration
```

### Environment Configuration

```env
# ── Ollama Inference ──────────────────────────
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-v3.1:671b-cloud

# ── PostgreSQL Database ───────────────────────
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=actuator_ai

# ── Application Settings ──────────────────────
PROJECT_NAME=Actuator AI
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32

# ── Optional Services ─────────────────────────
# REDIS_URL=redis://localhost:6379
# GROQ_API_KEY=gsk_...
# OPENAI_API_KEY=sk-...
# SENDGRID_API_KEY=SG....
# SLACK_WEBHOOK_URL=https://hooks.slack.com/...
# TAVILY_API_KEY=tvly-...
```

### Running the Application

#### Unified Script (Recommended)

```bash
./run.sh   # Linux/macOS
# or
run.bat    # Windows
```

#### Manual Development Mode

```bash
# Terminal 1: Backend (serves API + static UI)
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend (Vite dev server with HMR)
cd frontend
npm run dev
```

#### Production Mode

```bash
cd frontend
npm run build
cd ..
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Access Points

| Service | URL | Description |
|---|---|---|
| Frontend (Dev) | http://localhost:5173 | Vite development server with hot reload |
| Static Portal | http://127.0.0.1:8000 | Production UI served by FastAPI |
| API Docs | http://127.0.0.1:8000/docs | OpenAPI/Swagger interactive docs |
| Health Check | http://127.0.0.1:8000/health | System status endpoint |

---

## API Reference

### WebSocket Chat Endpoint

```
WS /api/v1/chat/ws
```

#### Connection Flow

1. Client opens WebSocket to `/api/v1/chat/ws`
2. Server accepts connection
3. Client sends initial message:
```json
{
  "message": "I need help with my invoice INV-2026-0401",
  "conversation_id": null,
  "customer_email": "ahmed@techvista.pk"
}
```
4. Server processes and streams response events

#### Stream Events

```json
// conv_id — Conversation assigned
{"type": "conv_id", "conversation_id": "abc-123-def"}

// content — Streaming response tokens
{"type": "content", "agent_name": "Supervisor Router", "content": "Let me..."}

// agent_update — Handoff to specialist
{"type": "agent_update", "agent_name": "Billing Finance Agent"}

// done — Stream complete
{"type": "done", "agent_name": "Billing Finance Agent",
 "needs_approval": false, "approval_items": []}

// error — Processing failure
{"type": "error", "content": "Error message", "agent_name": "System"}
```

### REST Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/api/v1/agents/` | List all registered agents | No |
| `GET` | `/api/v1/agents/{key}` | Get agent details | No |
| `POST` | `/api/v1/auth/signup` | Create account | No |
| `POST` | `/api/v1/auth/login` | Authenticate | No |
| `GET` | `/api/v1/chat/conversations` | List conversations | No |
| `GET` | `/api/v1/chat/conversations/{id}/messages` | Get messages | No |
| `GET` | `/health` | System health check | No |
| `GET` | `/` | Static UI (production) | No |

---

## Project Structure

```
actuator-ai/
│
├── actuator_agents/                    # 8 specialist agents
│   ├── supervisor_router/agent.py      # Central orchestrator
│   ├── technical_specialist/agent.py   # API/SDK issue resolution
│   ├── account_security/agent.py       # Auth & profile management
│   ├── billing_finance/agent.py        # Payments & subscriptions
│   ├── success_retention/agent.py      # Health & churn prevention
│   ├── operations_sync/agent.py        # CRM & Jira integration
│   ├── linguistic/agent.py             # Translation & sentiment
│   └── audit/agent.py                  # QA & compliance
│
├── backend/                            # FastAPI application
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py                # WebSocket + REST chat endpoints
│   │   │   ├── agents.py              # Agent listing/info endpoints
│   │   │   └── auth.py                # Authentication endpoints
│   │   └── schemas.py                 # Pydantic request/response models
│   │
│   ├── core/
│   │   └── config.py                  # Pydantic Settings (env vars)
│   │
│   ├── db/
│   │   ├── session.py                 # SQLModel database session
│   │   ├── schema.sql                 # Full PostgreSQL DDL (26 tables)
│   │   └── seed.sql                   # Realistic seed data
│   │
│   ├── models/
│   │   ├── conversation.py            # SQLModel ORM models
│   │   └── agent.py                   # Agent configuration model
│   │
│   ├── services/
│   │   └── agent_service.py           # Agent orchestration engine
│   │
│   ├── static/
│   │   └── index.html                 # Production static UI
│   │
│   └── main.py                        # FastAPI application entry point
│
├── frontend/                           # React SPA (Vite)
│   └── src/
│       ├── main.tsx                   # React entry + BrowserRouter
│       ├── App.tsx                    # Main chat application
│       ├── LandingPage.tsx            # Marketing landing page
│       ├── EnhancedAuth.tsx           # Login/signup page
│       ├── Docs.tsx                   # Documentation page
│       ├── store.ts                   # Zustand state management
│       ├── api.ts                     # WebSocket + REST client
│       ├── index.css                  # Global styles + CSS variables
│       ├── App.css                    # Chat application styles
│       └── LandingPage.css            # Landing + auth page styles
│
├── shared/                             # Cross-component utilities
│   ├── guardrails/
│   │   └── safety.py                  # 3 input + 1 output guardrails
│   ├── models/
│   │   ├── ollama_provider.py         # Ollama inference provider
│   │   ├── groq_provider.py           # Groq cloud provider
│   │   ├── openai_provider.py         # OpenAI provider
│   │   └── litellm_provider.py        # LiteLLM multi-provider
│   ├── schemas/
│   │   └── common.py                  # Shared Pydantic models
│   └── tools/
│       ├── db_tools.py                # 15+ database query tools
│       ├── math_tools.py              # Calculation + currency tools
│       ├── time_tools.py              # Timezone conversion tools
│       ├── web_tools.py               # Web search + URL fetch tools
│       └── notification_tools.py      # Email/Slack/webhook tools
│
├── .env.example                       # Environment variable template
├── pyproject.toml                     # Python dependencies (managed via uv)
├── uv.lock                           # Locked dependency versions
├── run.sh / run.bat                   # Unified startup scripts
└── .env                              # Environment configuration (create from template below)
```

---

## Development Workflow

### Code Quality

```bash
# Python formatting
uv run black .
uv run isort .

# Python type checking
uv run mypy .

# Python linting
uv run ruff check .

# Frontend formatting
cd frontend && npm run format

# Frontend linting
cd frontend && npm run lint
```

### Testing

> **Note**: Test suites are under development. Framework scaffolding is prepared in `pyproject.toml`.

```bash
# Backend tests
uv run pytest

# Frontend tests
cd frontend && npm test
```

### Git Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/feature-name`
3. Commit changes: `git commit -m 'feat: add feature description'`
4. Push: `git push origin feature/feature-name`
5. Open Pull Request

---

## Production Deployment

### Docker Compose

> **Note**: You'll need to create a `Dockerfile` at the project root for the application service. Below is a reference docker-compose template for orchestrating the full stack.

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: actuator_ai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./backend/db/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_SERVER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - OLLAMA_BASE_URL=http://ollama:11434/v1
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      ollama:
        condition: service_started

volumes:
  postgres_data:
  ollama_data:
```

### Production Environment Variables

```env
# Required
POSTGRES_SERVER=postgres
POSTGRES_PASSWORD=<secure-random-password>
OLLAMA_BASE_URL=http://ollama:11434/v1
SECRET_KEY=<openssl rand -hex 32>

# Optional
REDIS_URL=redis://redis:6379
SENTRY_DSN=https://<key>@o<org>.ingest.sentry.io/<project>
```

---

## Monitoring & Observability

### Health Check

```http
GET /health

Response:
{
  "status": "ok",
  "project": "Actuator AI Prod",
  "version": "1.0.0",
  "agents": 8
}
```

### Key Metrics

| Metric | Source | Description |
|---|---|---|
| Request latency (p50/p95/p99) | FastAPI middleware | End-to-end response time |
| Agent handoff success rate | `audit_logs` | Supervisor routing accuracy |
| Guardrail trigger count | `messages WHERE agent_name = 'Guardrail'` | Security incident frequency |
| Database query performance | PostgreSQL `pg_stat_statements` | MCP query efficiency |
| Token consumption | `audit_logs.tokens_used` | Per-agent LLM usage |
| Quality scores | `audit_logs.quality_score` | Agent response quality |

### Logging Architecture

- Structured JSON logging via Python's `logging` module
- Correlation IDs propagated through request lifecycle
- Agent execution traces in `audit_logs` table
- All tool calls logged with input/output summaries

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) team — Multi-agent orchestration framework
- [FastAPI](https://fastapi.tiangolo.com) community — High-performance async API framework
- [Ollama](https://ollama.com) — Local LLM inference platform
- [Model Context Protocol](https://modelcontextprotocol.io) working group — Standardized tool access protocol
- [Lucide](https://lucide.dev) — Beautiful open-source icon library
