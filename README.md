<div align="center">

# Actuator AI

**Production-Grade Multi-Agent Customer Support Orchestration Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135.3+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OmniRouter](https://img.shields.io/badge/LLM-OmniRouter-6366F1?style=flat&logo=openai&logoColor=white)](https://github.com/diegosouzapw/OmniRoute)
[![OpenAI Agents SDK](https://img.shields.io/badge/OpenAI_Agents_SDK-0.13.6+-412991?style=flat&logo=openai&logoColor=white)](https://github.com/openai/openai-agents-python)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=white)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)](LICENSE)

**8 specialized AI agents · OmniRouter auto-routing to 290+ providers · Multimodal Vision & OCR · Persistent Conversation Sidebar · Real-time PostgreSQL MCP · Free Email Notifications · Safe CRUD Operations**

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
10. [Authentication & Authorization](#authentication--authorization)
11. [Frontend Architecture](#frontend-architecture)
12. [Setup & Installation](#setup--installation)
13. [API Reference](#api-reference)
14. [Project Structure](#project-structure)
15. [Development Workflow](#development-workflow)
16. [Production Deployment](#production-deployment)

---

## Architecture Overview

Actuator AI implements the **supervisor-router orchestration pattern** atop the OpenAI Agents SDK. A central supervisor agent classifies incoming customer requests via keyword-weighted intent scoring, then delegates to one of seven domain-specialist agents through the SDK's native handoff mechanism. Each specialist agent is equipped with domain-specific function tools and real-time PostgreSQL access through the Model Context Protocol (MCP).

### Core Architectural Decisions

#### 1. Per-Request MCP Isolation

Each WebSocket connection receives a **fresh** `MCPServerStdio` instance. The OpenAI Agents SDK's MCP implementation maintains an internal state machine for connect/disconnect lifecycle operations. When agent handoffs occur mid-conversation, a shared singleton MCP instance triggers race conditions manifesting as "Server not initialized" errors. The factory pattern guarantees isolated lifecycle management.

<details>
<summary>MCP factory pattern implementation</summary>

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

Lifecycle in the orchestrator:

```python
async def run_chat_stream(...):
    mcp = create_mcp_postgres()    # 1. Fresh instance
    await mcp.connect()            # 2. Initialize transport

    async with _run_lock:
        for ag in _ALL_AGENTS:
            ag.mcp_servers = [mcp] # 3. Assign to all agents (read-only)

        try:
            result = Runner.run_streamed(supervisor, input_list, ...)
        finally:
            for ag in _ALL_AGENTS:
                ag.mcp_servers = []  # 4. Clear references
            await mcp.cleanup()      # 5. Graceful teardown
```
</details>

#### 2. Guardrail Poisoning Prevention

Blocked messages must never contaminate conversation history. If a user message triggers a guardrail, it is **not persisted**. Only the guardrail's response is stored -- tagged with `agent_name = 'Guardrail'` -- and filtered out during history reconstruction. This prevents re-triggering on subsequent clean messages and maintains conversation integrity.

<details>
<summary>History reconstruction filtering guardrail responses</summary>

```python
prior_messages = db.exec(
    select(Message)
    .where(Message.conversation_id == conversation_id)
    .where(Message.agent_name != "Guardrail")  # Skip blocked exchanges
    .order_by(Message.created_at)
).all()
```
</details>

#### 3. SQL Hallucination Prevention

Local LLMs frequently hallucinate non-existent database columns, tables, or SQL syntax, entering retry loops that exhaust the agent's `max_turns`. Each agent prompt embeds **exact copy-paste SQL patterns** with an explicit instruction against writing custom SQL.

<details>
<summary>Example SQL pattern embedded in agent prompts</summary>

```
WARNING: DO NOT WRITE YOUR OWN SQL QUERIES. YOU MUST COPY AND PASTE
THESE EXACT SQL PATTERNS. NEVER INVENT TABLES OR COLUMNS!

SELECT c.company_name, c.health_score, c.mrr, c.status,
       p.name as plan, s.current_period_end, s.auto_renew
FROM customers c
JOIN customer_contacts cc ON cc.customer_id = c.id
JOIN subscriptions s ON s.customer_id = c.id
JOIN products p ON p.id = s.product_id
WHERE cc.email ILIKE '{customer_email}'
```
</details>

#### 4. Asynchronous Request Serialization

A module-level `asyncio.Lock` serializes concurrent requests. The OpenAI Agents SDK's agent objects maintain mutable state (e.g., `mcp_servers`, current turn tracking), and shared mutation across concurrent `Runner.run_streamed()` calls produces non-deterministic behavior.

#### 5. Hybrid Database Approach

The project uses a **dual strategy** for database access:

| Layer | Technology | Scope |
|---|---|---|
| **ORM** | SQLModel (Pydantic + SQLAlchemy) | Conversation/message CRUD in `backend/models/conversation.py` |
| **Raw SQL** | psycopg2 with `RealDictCursor` | All 21 business tables via DDL in `schema.sql` |
| **MCP Query** | `@modelcontextprotocol/server-postgres` | Agent runtime DB access through OpenAI Agents SDK |

FastAPI's `lifespan` handler calls `SQLModel.metadata.create_all(engine)` on startup for ORM-managed tables. The 21-table DDL schema is applied separately via `psql -f schema.sql`.

---

## Request Lifecycle

```
END-TO-END REQUEST LIFECYCLE

Client (React SPA / static HTML)
   |
   | WebSocket: WS /api/v1/chat/ws
   v

Step 1: FastAPI accepts WebSocket connection
Step 2: Receive JSON: { message, conversation_id?, customer_email? }
Step 3: New conversation -> Create Conversation(id=uuid4(), ...)
         Existing conversation -> Fetch by conversation_id
Step 4: Send conv_id event to client
Step 5: Rebuild history (excluding Guardrail messages)
Step 6: Acquire _run_lock (asyncio.Lock)
Step 7: MCP lifecycle Phase 1: create_mcp_postgres() -> connect()
Step 8: Runner.run_streamed(supervisor, input_list, context={...})

Step 9: Supervisor processes input:
    a. Input guardrails fire (jailbreak -> PII -> SQL injection)
       If triggered -> GuardrailTripwireTripped -> error event
    b. classify_request(message) -> keyword scoring across 7 categories
    c. Handoff to specialist via SDK mechanism
    d. If ambiguous -> asks one clarification question

Step 10: Specialist agent executes:
    a. Queries PostgreSQL via MCP 'query' tool
    b. Calls domain function_tools
    c. Streams ResponseTextDeltaEvent events to client
    d. If refund tool called -> HITL interruption

Step 11: Stream completion:
    a. MCP lifecycle Phase 2: cleanup() -> release _run_lock
    b. Persist user and assistant messages to DB
    c. Update conversation.last_agent
    d. Send "done" event

Step 12: Client receives final event with agent_name, needs_approval
```

### Stream Event Protocol

| Event Type | Direction | Payload Schema | Description |
|---|---|---|---|
| `conv_id` | Server -> Client | `{type, conversation_id}` | Assigned conversation UUID; emitted once |
| `content` | Server -> Client | `{type, agent_name, content}` | Incremental response text deltas |
| `agent_update` | Server -> Client | `{type, agent_name}` | Agent handoff notification |
| `done` | Server -> Client | `{type, agent_name, needs_approval, approval_items}` | Stream termination |
| `error` | Server -> Client | `{type, content, agent_name}` | Processing failure |

All events are JSON-serialized strings sent over a single persistent WebSocket connection.

---

## Agent Specialization Matrix

### Supervisor Router

The central orchestrator. Every customer message enters through this agent, which never attempts to solve issues itself -- its sole responsibility is classification and routing.

| Property | Value |
|---|---|
| **Agent Name** | Supervisor Router |
| **Model** | `auto` (OmniRouter) |
| **Temperature** | 0.20 |
| **Max Tokens** | 800 |
| **Input Guardrails** | Jailbreak, PII, SQL Injection |
| **Function Tools** | `classify_request`, `escalate_to_human` |

**classify_request** -- Scans the message against 7 predefined category dictionaries. Each dictionary contains domain-specific signal keywords. The category with the highest cumulative signal score is selected. Priority is determined by urgency keyword presence (P1-critical vs P3-medium).

**escalate_to_human** -- Creates an escalation record with SLA tracking when the agent pipeline cannot resolve. Returns ESC-XXXXX formatted escalation assigned to on-duty supervisor with 30-minute SLA.

### Domain Specialist Agents

| Agent | Model | Temp | Max Tokens | Function Tools | DB Tables (via MCP) |
|---|---|---|---|---|---|
| **Technical Specialist** | `auto` | 0.2 | 1200 | `diagnose_service`, `check_system_status`, `create_support_ticket` | knowledge_articles, support_tickets, ticket_comments, api_usage, customers, customer_contacts |
| **Account Security Agent** | `qwen2.5:7b` | 0.2 | 1000 | `unlock_account`, `initiate_2fa_setup`, `reset_2fa`, `initiate_password_reset`, `update_profile` | customers, customer_contacts, security_events |
| **Billing Finance Agent** | `qwen2.5:7b` | 0.2 | 1000 | `change_plan`, `process_refund*`, `apply_credit` | invoices, invoice_line_items, subscriptions, products, payments, refunds, api_usage, customer_contacts |
| **Success Retention Agent** | `auto` | 0.4 | 1200 | `schedule_check_in`, `create_renewal_offer`, `log_churn_intervention` | customers, api_usage, feature_flags, feedback, support_tickets, subscriptions, products |
| **Operations Sync Agent** | `qwen2.5:7b` | 0.2 | 1000 | `update_crm_note`, `create_support_ticket`, `create_jira_ticket`, `update_jira_ticket` | support_tickets, ticket_comments, notifications_log, customers, customer_contacts, subscriptions, products |
| **Linguistic Agent** | `auto` | 0.3 | 1000 | `detect_language`, `translate_text`, `analyze_sentiment`, `assess_communication_quality` | feedback |
| **Audit Agent** | `auto` | 0.1 | 1200 | `check_hallucination`, `check_policy_compliance`, `audit_conversation`, `score_response_accuracy`, `generate_qa_report` | audit_logs, escalations, conversations, messages |

Key behaviors:
- **Billing**: `process_refund` has `needs_approval=True` -- triggers HITL workflow. Credit limits: <= PKR 5,000 direct; larger amounts require escalation.
- **Success Retention**: Health thresholds: >=80 Healthy, 40-79 At Risk, <40 Critical. Maximum discount: 25% without escalation.
- **Technical Specialist**: Protocol is Search KB -> Check system status -> Diagnose error -> Create ticket.
- **Account Security**: Write operations logged to security_events for audit trail.
- **Operations Sync**: Assignment mapping: Billing->Finance, Technical->Engineering, Account->Account Team, Feature requests->Product Team. SLA: P1/P2=4h, P3/P4=24h.

### Error Diagnostics Map (Technical Specialist)

| Error Code | Root Cause Diagnosis |
|---|---|
| `500` | Unhandled exception, DB connection timeout, OOM |
| `502` | Upstream service unreachable, network policy, LB config |
| `503` | Overloaded or maintenance, check replicas/memory |
| `429` | Rate limited -- review quota tier |
| `timeout` | P99 latency spike -- DB query perf, connection pool |

---

## Technology Stack

| Layer | Technology | Version | Description |
|---|---|---|---|
| **Agent Framework** | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | >=0.13.6 | Streaming via `Runner.run_streamed()`; handoffs for routing; guardrails for validation; HITL via `@function_tool(needs_approval=True)` |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) | >=0.135.3 + >=0.44.0 | ASGI server; WebSocket streaming; dependency injection for DB sessions; lifespan handler for ORM table creation |
| **Database Access** | [SQLModel](https://sqlmodel.tiangolo.com) + raw SQL (hybrid) | >=0.0.38 | SQLModel for conversation/message persistence; raw DDL (`schema.sql`) + psycopg2 `RealDictCursor` for 21 business tables |
| **Database Driver** | [psycopg2](https://www.psycopg.org) | >=2.9.11 | `RealDictCursor` for dict-row mappings; `psycopg2.extras.Json` for JSONB inserts |
| **DB Access Protocol** | [MCP PostgreSQL Server](https://github.com/modelcontextprotocol/servers) | npx | `MCPServerStdio` with 30s session timeout; per-request factory pattern |
| **Authentication** | [bcrypt](https://github.com/pyca/bcrypt) + [PyJWT](https://github.com/jpadilla/pyjwt) | >=5.0.0 + >=2.12.1 | bcrypt password hashing; HS256 JWT with 7-day expiry |
| **Configuration** | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | >=2.13.1 | `BaseSettings` with `SettingsConfigDict(env_file=".env")`; computed properties for `SQLALCHEMY_DATABASE_URI` |
| **LLM Inference** | [OmniRouter](https://github.com/diegosouzapw/OmniRoute) | >=1.0 | Self-hosted AI gateway routing to 290+ providers with auto-failover. OpenAI-compatible endpoint. |
| **HTTP Client** | [httpx](https://www.python-httpx.org) | >=0.28.1 | Async HTTP for Tavily search, currency conversion, webhook delivery |
| **Frontend** | [React](https://react.dev) 19 + [Vite](https://vite.dev) 8 | -- | TypeScript 6.0 strict mode; `@vitejs/plugin-react` with SWC |
| **State Management** | [Zustand](https://github.com/pmndrs/zustand) | 5.0.12 | Single store with `create<ChatStore>()`; action-based updates |
| **Routing** | [React Router DOM](https://reactrouter.com) | 7.14.2 | `BrowserRouter` with `Routes` for landing/login/docs/chat |
| **Animation** | [Framer Motion](https://www.framer.com/motion) | 12.38.0 | Orchestrated page transitions; `AnimatePresence` for feature card cycling |
| **Icons** | [Lucide React](https://lucide.dev) | 1.8.0 | Agent-specific icons mapped via `AGENT_CONFIG` color dictionary |
| **Markdown** | [marked](https://marked.js.org) | 18.0.0 | Client-side parsing with `breaks: true, gfm: true` |

---

## Database Schema

21 tables organized across 5 logical domains with 15+ composite indexes and comprehensive seed data (1500+ rows) simulating a real SaaS customer support platform spanning 10 companies across 4 regions.

### Domain Map

**Conversation State (2 tables)**
- `conversations`, `messages`
- Core chat persistence with token/latency tracking

**Customer Data (6 tables)**
- `customers`, `customer_contacts`, `products`, `subscriptions`, `api_usage`, `feature_flags`
- Multi-contact per customer; tiered subscription model; granular usage tracking

**Billing & Payments (4 tables)**
- `invoices`, `invoice_line_items`, `payments`, `refunds`
- Full billing lifecycle with refund chain and multi-currency support (PKR, AED)

**Support & Operations (5 tables)**
- `support_tickets`, `ticket_comments`, `knowledge_articles`, `escalations`, `notifications_log`
- Complete support operations with SLA tracking, knowledge base, and notifications

**Security & Audit (4 tables)**
- `security_events`, `audit_logs`, `feedback`, `agents_config`
- Immutable audit trail; NPS/CSAT tracking; agent configuration registry; hallucination risk scoring

### Entity Relationships

```
customers ------ customer_contacts (1:N, ON DELETE CASCADE)
             |--- subscriptions (1:N)
             |--- invoices (1:N)
             |--- api_usage (1:N)
             |--- feature_flags (1:N, UNIQUE per customer+feature)
             |--- support_tickets (1:N)
             |--- feedback (1:N, CHECK rating 1-5, nps_score 0-10)
             |--- conversations (1:N)

subscriptions --- products (N:1)
invoices --- invoice_line_items (1:N, ON DELETE CASCADE)
         |--- payments (1:N) --- refunds (1:N)

support_tickets --- ticket_comments (1:N, ON DELETE CASCADE, author_type discriminator)
                  |--- escalations (1:N)

conversations --- messages (1:N)
```

<details>
<summary>Key table DDL schemas</summary>

**customers -- Core Business Entity**
```sql
CREATE TABLE customers (
    id              SERIAL PRIMARY KEY,
    company_name    VARCHAR(200) NOT NULL,
    industry        VARCHAR(100),
    company_size    VARCHAR(50),           -- '1-10', '11-50', '51-200', '201-500', '500+'
    region          VARCHAR(100),
    status          VARCHAR(20) DEFAULT 'active',
    health_score    INTEGER DEFAULT 70,
    mrr             DECIMAL(12,2) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**customer_contacts -- Multi-Contact with Security State**
```sql
CREATE TABLE customer_contacts (
    id                  SERIAL PRIMARY KEY,
    customer_id         INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    name                VARCHAR(200) NOT NULL,
    email               VARCHAR(255) UNIQUE NOT NULL,
    role                VARCHAR(100),
    is_primary          BOOLEAN DEFAULT false,
    last_login          TIMESTAMP,
    login_failures      INTEGER DEFAULT 0,
    account_locked      BOOLEAN DEFAULT false,
    two_factor_enabled  BOOLEAN DEFAULT false,
    two_factor_method   VARCHAR(20),       -- totp, sms, email
);
```

**support_tickets -- SLA-Bound Ticket Management**
```sql
CREATE TABLE support_tickets (
    id                VARCHAR(20) PRIMARY KEY, -- TKT-XXXXX
    customer_id       INTEGER REFERENCES customers(id),
    category          VARCHAR(30) NOT NULL,
    priority          VARCHAR(5) NOT NULL,     -- P1, P2, P3, P4
    status            VARCHAR(20) DEFAULT 'open',
    assigned_to       VARCHAR(100),
    sla_deadline      TIMESTAMP,
    satisfaction      INTEGER,                -- 1-5 CSAT
    tags              TEXT[],                 -- PostgreSQL array column
);
```

**audit_logs -- Immutable Agent Audit Trail**
```sql
CREATE TABLE audit_logs (
    id                  SERIAL PRIMARY KEY,
    conversation_id     VARCHAR(50),
    agent_name          VARCHAR(100) NOT NULL,
    action              VARCHAR(50) NOT NULL,
    input_summary       TEXT,
    output_summary      TEXT,
    hallucination_risk  VARCHAR(10),          -- low, medium, high
    policy_compliant    BOOLEAN DEFAULT true,
    quality_score       INTEGER,             -- 0-100
    latency_ms          INTEGER,
    tokens_used         INTEGER,
);
```
</details>

### Seed Data Profile

| Table | Rows | Notable Characteristics |
|---|---|---|
| `customers` | 10 | Active (6), Churned (1), Suspended (1), Trial (1), 2 Enterprise Plus customers |
| `customer_contacts` | 14 | 8 primary contacts; 3 locked accounts; 5 with 2FA enabled (TOTP/SMS/Email) |
| `products` | 4 | Free (PKR 0), Pro (PKR 4.9K), Enterprise (PKR 29.9K), Enterprise Plus (PKR 89.9K) |
| `invoices` | 12 | 2 overdue (DataPulse + LogiTrack); multi-currency (PKR, AED) |
| `payments` | 9 | 1 refunded (REF-00001); methods: visa/mastercard/bank_transfer |
| `support_tickets` | 9 | 3 open; 2 in_progress; 1 critical escalation (ESC-00001) |
| `knowledge_articles` | 12 | 3.4K views on SDK setup; topics: API/SDK/Security/Billing/Deployment |
| `security_events` | 16 | Login failures, account locks, 2FA verifications, suspicious activity |
| `audit_logs` | 7 | Quality scores 88-96; hallucination risk all "low"; AI feedback sample data |

---

## Security & Guardrail Pipeline

### Three-Layer Input Validation

Three `@input_guardrail` functions execute in sequence **before** any agent processes incoming messages. If any guardrail triggers, execution is halted and the `InputGuardrailTripwireTriggered` exception propagates to the orchestrator.

| Layer | Detection Method | Examples |
|---|---|---|
| **1. Jailbreak** | Pattern matching against 10+ injection patterns | `"ignore your instructions"`, `"DAN mode"`, `"system prompt"` |
| **2. PII** | Regex scanning for sensitive data | Credit card numbers (Luhn-checkable), US SSNs |
| **3. SQL Injection** | Keyword blacklist | `DROP TABLE`, `DELETE FROM`, `OR 1=1`, `UNION SELECT` |

<details>
<summary>Guardrail implementation examples</summary>

```python
# PII Detection
re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', text)  # Credit cards
re.search(r'\b\d{3}-\d{2}-\d{4}\b', text)  # SSNs

# SQL Injection Detection
patterns = ["DROP TABLE", "DELETE FROM", "'; --", "OR 1=1", "UNION SELECT"]
```
</details>

### Output Validation

A single output guardrail enforces a 3000-character response limit for cost/quality control.

### Guardrail Isolation Protocol

```
User sends message
       |
       v
  [InputGuardrail 1: Jailbreak]
  [InputGuardrail 2: PII]           -- All pass --> Agent processes
  [InputGuardrail 3: SQL Injection]
          |
          v Triggered
  ------------------------
  Exception caught
  User message NOT saved to DB
  Guardrail response saved only
  Error event emitted to client
```

### Post-Processing Policy Compliance

The Audit Agent's `check_policy_compliance` tool scans responses for:

| Check | Detection Pattern |
|---|---|
| PII exposure | Full CC number or SSN in response |
| Unauthorized promises | "guarantee", "100% uptime", "free upgrade" |
| Competitor mentions | "zendesk", "intercom", "freshdesk" |
| Refund policy violation | "refund" without "approved" in context |

---

## MCP (Model Context Protocol) Integration

### Architecture

```
+---------------------+     WS transport     +-----------------------+
|  MCPServerStdio     |<-------------------->|  npx -y               |
|  (Per-Request)      |                      |  @modelcontextprotocol|
|                     |                      |  /server-postgres     |
|  session_timeout:   |                      |           |           |
|  30.0s              |                      |           |           |
+---------------------+                      |     TCP/5432          |
                                              |           |           |
                                              +-----------+-----------+
                                                          |
                                                          v
                                                 +------------------+
                                                 |   PostgreSQL 14+ |
                                                 |   actuator_ai DB |
                                                 +------------------+
```

### Why Per-Request Isolation?

The `MCPServerStdio` class manages an internal state machine: `CREATED -> CONNECTED -> CLEANED`. When agent A hands off to agent B mid-conversation, the SDK internally manages the MCP lifecycle. If agents A and B share the same instance, concurrent lifecycle calls race -- one agent's `connect()` while another's `cleanup()` is in progress produces "Server not initialized" errors. The factory pattern guarantees each request gets an isolated MCP instance with a clean state.

### Tool Registration

Each agent's MCP server provides a `query` tool that executes read-only SQL. The tool is registered implicitly when `ag.mcp_servers = [mcp]` is set. Agent system prompts instruct using `query` for all database access rather than inventing data.

---

## Human-in-the-Loop (HITL) Workflows

The `process_refund` tool uses the SDK's `needs_approval=True` parameter to trigger an interruption workflow:

1. Agent calls `process_refund` during streaming
2. SDK yields an interruption event
3. FastAPI catches the interruption and sends `"done"` event with `needs_approval: true`
4. Frontend displays an amber warning banner
5. User approves via `state.approve(interruption)`
6. SDK resumes execution
7. Refund is completed and persisted

<details>
<summary>process_refund tool implementation</summary>

```python
@function_tool(needs_approval=True)
def process_refund(email: str, invoice_id: str, amount: float, reason: str) -> str:
    # Look up payment for the invoice
    # Look up customer ID
    # Create refund record with status='pending'
    return f"Refund {refund_id}: Pending approval. Approved amount: PKR {amount:,.0f}"
```

Resuming execution:

```python
state = result.to_state()
for i in result.interruptions:
    answer = input(f"Approve '{i.raw_item.name}'? (y/n): ")
    if answer == "y":
        state.approve(i)
result = await Runner.run(agent, state)
```
</details>

---

## Model Inference Architecture

### Provider Layer

All LLM calls route through **OmniRouter** — self-hosted AI gateway at `http://localhost:20128/v1`. OmniRouter handles provider selection, failover, and compression across 290+ providers. Model is set to `auto` so OmniRouter picks the best provider per request.

| Module | Purpose |
|---|---|
| `shared.models.ollama_provider` | Default import for all agents (delegates to factory) |
| `shared.models.factory` | Core factory — creates OpenAI-compatible client pointing at OmniRouter |
| `shared.models.litellm_provider` | Direct LiteLLM access (only for use outside OmniRouter) |

---

## Authentication & Authorization

### JWT-Based Authentication

Stateless JWT tokens with bcrypt password hashing. **Warning**: The `SECRET_KEY` must be set via environment variable in production -- the fallback default is insecure.

<details>
<summary>Authentication configuration</summary>

```python
SECRET_KEY = getattr(settings, 'SECRET_KEY', None)
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in environment")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
```
</details>

### Endpoints

| Method | Endpoint | Request Body | Response | Effect |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/signup` | `{email, password, name?}` | `{access_token, token_type, email, name}` | Creates user or claims legacy account |
| `POST` | `/api/v1/auth/login` | `{email, password}` | `{access_token, token_type, email, name}` | Validates credentials, returns token |

### Token Payload

```json
{
  "sub": "user@example.com",
  "exp": 1748300000
}
```

---

## Frontend Architecture

The project ships **two UI implementations**:

| UI | Location | Purpose |
|---|---|---|
| **React 19 SPA** (Primary) | `frontend/` | Main customer-facing interface with agent chat, landing page, authentication, and documentation. Bundled via Vite. |
| **Static HTML** (Fallback) | `backend/static/index.html` | Standalone UI with inline CSS/JS served directly from FastAPI at root path. Used when React frontend has not been built or for quick deployment. |

### Component Tree (React SPA)

```
<BrowserRouter>
  <Routes>
    <Route path="/" element={<ChatApp> | <LandingPage>} />
    <Route path="/login" element={<EnhancedAuth>} />
    <Route path="/docs" element={<Docs>} />
  </Routes>
</BrowserRouter>
```

### State Management (Zustand)

The `ChatStore` interface manages: user auth state, message array with streaming flag, conversation UUID, WebSocket loading state, and active agent tracking. Actions: `setUser`, `addMessage`, `updateLastMessage`, `setConversationId`, `setActiveAgent`, `clear`.

### WebSocket Client Protocol

The `streamMessage()` function in `api.ts` implements the full duplex protocol:

1. Add user message to store
2. Create placeholder assistant message with `isStreaming: true`
3. Open WebSocket to `ws://host/api/v1/chat/ws`
4. On `conv_id` event: store conversation UUID
5. On `content` event: accumulate text, update last message in-place
6. On `agent_update` event: seal current message, create new assistant message
7. On `done` event: finalize message, close WebSocket
8. On `error` event: append error content, close WebSocket

### Agent Color Configuration

Each of the 8 agents plus Guardrail and System have unique color + icon mappings (via Lucide React icons) used for visual differentiation in the chat UI.

---

## Setup & Installation

### Prerequisites

- **PostgreSQL 14+** -- Create database `actuator_ai` and apply schema + seed
- **Python 3.11+** -- Package management via `uv` (Astral)
- **Node.js 18+** -- Frontend build tooling
- **OmniRouter** -- Self-hosted AI gateway auto-routing to 290+ providers (`npm install -g omniroute`)
- **npx** (ships with Node.js) -- Required by MCP PostgreSQL server

### Quick Start

```bash
# 1. Clone & enter repository
git clone https://github.com/PatheticUser/agentic-ai-hub.git
cd actuator-ai

# 2. Create virtual environment & install Python dependencies
uv venv
source .venv/bin/activate   # Linux/macOS
uv pip install -e .

# 3. Set up database
psql -U postgres -c "CREATE DATABASE actuator_ai;"
psql -U postgres -d actuator_ai -f backend/db/schema.sql
psql -U postgres -d actuator_ai -f backend/db/seed.sql

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 6. Run (both servers)
./run.sh   # Linux/macOS
run.bat    # Windows
```

### Manual Development Mode

```bash
# Terminal 1: Backend
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend (with HMR + API proxy)
cd frontend && npm run dev
```

### Production Build

```bash
cd frontend && npm run build && cd ..
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## API Reference

### WebSocket: `/api/v1/chat/ws`

**Connection**: Client sends first message as JSON:
```json
{
  "message": "I need help with my invoice",
  "conversation_id": null,
  "customer_email": "ahmed@techvista.pk"
}
```

**Response Stream** (JSON events, one per line):
```
{"type": "conv_id", "conversation_id": "abc-123-def"}
{"type": "content", "agent_name": "Supervisor Router", "content": "Let me check..."}
{"type": "agent_update", "agent_name": "Billing Finance Agent"}
{"type": "content", "agent_name": "Billing Finance Agent", "content": "I found invoice..."}
{"type": "done", "agent_name": "Billing Finance Agent", "needs_approval": false, "approval_items": []}
```

### REST Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/agents/` | List all 8 agents with metadata |
| `GET` | `/api/v1/agents/{key}` | Agent details: name, description, tools |
| `POST` | `/api/v1/auth/signup` | Account registration |
| `POST` | `/api/v1/auth/login` | Authentication |
| `GET` | `/api/v1/chat/conversations?email=&status=&limit=` | List conversations (filtered by user email) |
| `GET` | `/api/v1/chat/conversations/{id}/messages` | Get conversation messages |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Delete conversation and messages |
| `PATCH` | `/api/v1/chat/conversations/{id}` | Rename conversation session title |
| `GET` | `/health` | System health: status, version, agent count |
| `GET` | `/` | Serve production static UI |

---

## Project Structure

```
actuator-ai/
|
+-- actuator_agents/                     # 8 OpenAI Agents SDK agents
|   +-- supervisor_router/agent.py       # Central orchestrator + classifier
|   +-- technical_specialist/agent.py    # API/SDK diagnostics
|   +-- account_security/agent.py        # Auth + 2FA + unlock
|   +-- billing_finance/agent.py         # Invoices + refunds (HITL)
|   +-- success_retention/agent.py       # Health scores + churn
|   +-- operations_sync/agent.py         # CRM + Jira + tickets
|   +-- linguistic/agent.py              # Translation + sentiment
|   +-- audit/agent.py                   # QA + compliance + hallucination
|
+-- backend/                              # FastAPI application
|   +-- api/
|   |   +-- routes/
|   |   |   +-- chat.py                  # WebSocket + REST chat
|   |   |   +-- agents.py                # Agent listing/info
|   |   |   +-- auth.py                  # JWT auth endpoints
|   |   +-- schemas.py                   # Request/response Pydantic models
|   +-- core/config.py                   # Pydantic Settings
|   +-- db/
|   |   +-- session.py                   # SQLModel engine + session
|   |   +-- schema.sql                   # 21-table DDL
|   |   +-- seed.sql                     # 1500+ rows seed data
|   +-- models/
|   |   +-- conversation.py              # SQLModel: Conversation, Message, Customer, SupportTicket
|   |   +-- agent.py                     # Agent config model
|   +-- services/
|   |   +-- agent_service.py             # Agent orchestration engine
|   +-- static/index.html                # Lightweight static HTML fallback UI
|   +-- main.py                          # FastAPI entry point + lifespan
|
+-- frontend/                             # React 19 + Vite 8 SPA (Primary UI)
|   +-- src/
|       +-- main.tsx                     # Entry + BrowserRouter
|       +-- App.tsx                      # Main chat + agent badges
|       +-- LandingPage.tsx              # Marketing page (framer-motion)
|       +-- EnhancedAuth.tsx             # Login/signup with features
|       +-- Docs.tsx                     # Documentation page
|       +-- store.ts                     # Zustand state
|       +-- api.ts                       # WebSocket + REST client
|       +-- index.css                    # CSS variables + markdown styles
|       +-- App.css                      # Chat UI layout + animations
|       +-- LandingPage.css              # Landing + auth styles
|
+-- shared/                               # Cross-component packages
|   +-- guardrails/safety.py             # 3 input + 1 output guardrails
|   +-- models/                          # LLM provider abstraction (all route through OmniRouter)
|   |   +-- ollama_provider.py           # Default import — delegates to factory
|   |   +-- groq_provider.py             # Re-export from factory (legacy compat)
|   |   +-- openai_provider.py           # Re-export from factory (legacy compat)
|   |   +-- litellm_provider.py          # Direct LiteLLM (non-OmniRouter use only)
|   +-- schemas/common.py                # Shared Pydantic models
|   +-- tools/
|   |   +-- db_tools.py                  # 18 database query/write tools
|   |   +-- math_tools.py                # Calculator + currency
|   |   +-- time_tools.py                # Timezone + business hours
|   |   +-- web_tools.py                 # Tavily search + URL fetch
|   |   +-- notification_tools.py        # SendGrid + Slack + webhook
|   +-- mcp_config.py                    # MCP server factory
|
+-- .env.example                         # Environment template
+-- pyproject.toml                       # Python dependencies
+-- uv.lock                              # Locked dependency versions
+-- run.sh / run.bat                     # Unified startup scripts
+-- README.md                            # This file
```

---

## Development Workflow

### Code Quality Commands

```bash
# Python
uv run ruff check .       # Linting
uv run black .            # Formatting
uv run isort .            # Import sorting
uv run mypy .             # Type checking (in progress)

# Frontend
cd frontend && npm run lint   # ESLint + TypeScript checking
```

### Testing

```bash
uv run pytest                   # Backend tests (scaffolding)
cd frontend && npm test         # Frontend tests (scaffolding)
```

---

## Production Deployment

### Docker Compose Reference

Note: The frontend is served from `backend/static/index.html` as the default static UI. To use the React SPA, build it separately (`cd frontend && npm run build`) and serve via a reverse proxy (Nginx/Caddy).

<details>
<summary>Docker Compose configuration</summary>

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: actuator_ai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?err}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./backend/db/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports: ["8000:8000"]
    environment:
      POSTGRES_SERVER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?err}
      SECRET_KEY: ${SECRET_KEY:?err}
    depends_on:
      postgres: { condition: service_healthy }

volumes:
  postgres_data:
```
</details>

### Production Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_SERVER` | Yes | `localhost` | Database host |
| `POSTGRES_PORT` | No | `5432` | Database port |
| `POSTGRES_USER` | No | `postgres` | Database user |
| `POSTGRES_PASSWORD` | Yes | -- | Database password |
| `POSTGRES_DB` | No | `actuator_ai` | Database name |
| `OMNIROUTER_BASE_URL` | Yes | `http://127.0.0.1:20128/v1` | OmniRouter endpoint |
| `OMNIROUTER_API_KEY` | Yes | -- | OmniRouter auth token |
| `OMNIROUTER_MODEL` | No | `auto` | Model string (use `auto` for smart routing) |
| `SECRET_KEY` | **Yes** | -- | JWT signing key -- **must be set in production** (`openssl rand -hex 32`) |
| `API_V1_STR` | No | `/api/v1` | API prefix |

### Health Check

```http
GET /health
-> 200 OK
{
  "status": "ok",
  "project": "Actuator AI",
  "version": "1.0.0",
  "agents": 8
}
```

---

## License

MIT License. See `LICENSE` for full text.

---

## Acknowledgments

- **OpenAI Agents SDK** -- Multi-agent orchestration framework providing handoffs, guardrails, function tools, and streaming
- **FastAPI** -- High-performance async Python API framework with WebSocket support
- **OmniRouter** -- Self-hosted AI gateway routing to 290+ providers with auto-failover and token compression
- **Model Context Protocol** -- Standardized protocol for tool access and database integration
- **Lucide** -- Open-source icon library with consistent SVG-based design system