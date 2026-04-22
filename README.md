# Actuator AI

Production-grade multi-agent customer support platform. Built on **OpenAI Agents SDK**, orchestrated via **FastAPI**, backed by **PostgreSQL** with real-time **MCP** database access for all agents.

---

## Architecture

### Request Flow

```
WebSocket /api/v1/chat/ws
  → FastAPI reconstructs history from PostgreSQL (guardrail-blocked messages excluded)
  → Fresh MCP server spawned per request (factory pattern, not singleton)
  → Native `Runner.run_streamed()` yields `AgentResponseStream` JSON chunks
  → Supervisor classifies → handoff to specialist
  → Specialist queries DB via exact SQL guardrails → streams tokens to client
  → Client detects agent handoffs (`agent_update`) and splits visual message bubbles automatically
  → Messages saved to DB only on successfully finishing the stream
  → WebSocket terminates gracefully (saving resources)
```

### Agent Graph

| Agent | Domain | Tools | MCP Tables |
|---|---|---|---|
| **Supervisor Router** | Triage, classification, handoff | `classify_request`, `escalate_to_human` | — |
| **Technical Specialist** | API errors, SDK issues, KB search | `diagnose_service`, `check_system_status`, `create_support_ticket` | `knowledge_articles`, `support_tickets` |
| **Account Security Agent** | Login, 2FA, lockout, profile | `unlock_account`, `initiate_2fa_setup`, `reset_2fa`, `initiate_password_reset`, `update_profile` | `customers`, `customer_contacts`, `security_events` |
| **Billing Finance Agent** | Invoices, refunds, plans, credits | `change_plan`, `process_refund`*, `apply_credit` | `invoices`, `invoice_line_items`, `subscriptions`, `products`, `payments`, `refunds`, `api_usage` |
| **Success Retention Agent** | Health scores, churn, renewals | `schedule_check_in`, `create_renewal_offer`, `log_churn_intervention` | `customers`, `api_usage`, `feature_flags`, `feedback` |
| **Operations Sync Agent** | CRM, tickets, Jira | `update_crm_note`, `create_support_ticket`, `create_jira_ticket`, `update_jira_ticket` | `support_tickets`, `ticket_comments`, `notifications_log` |
| **Linguistic Agent** | Sentiment, translation, language detection | `detect_language`, `translate_text`, `analyze_sentiment`, `assess_communication_quality` | `feedback` |
| **Audit Agent** | QA, hallucination detection, policy compliance | `check_hallucination`, `check_policy_compliance`, `audit_conversation`, `score_response_accuracy`, `generate_qa_report` | `audit_logs`, `escalations`, `conversations` |

`*` `process_refund` has `needs_approval=True` → triggers HITL interruption

---

## Database Schema

26 tables across 4 logical groups:

```
Conversation State   : conversations, messages
Customer Data        : customers, customer_contacts, subscriptions, products
Authentication       : customer (FastAPI Auth model with hashed_password)
Billing              : invoices, invoice_line_items, payments, refunds, api_usage
Operational          : support_tickets, ticket_comments, knowledge_articles,
                       feature_flags, feedback, audit_logs, escalations,
                       security_events, notifications_log, feature_changelog
```

All agents receive the `query` MCP tool for direct PostgreSQL read access. Write operations go through typed `@function_tool` wrappers with Pydantic-validated parameters.

---

## MCP Integration

Each request gets a **fresh `MCPServerStdio` instance** via `create_mcp_postgres()`. This avoids the lifecycle conflict (`Server not initialized`) that occurs when sharing a singleton across handoffs. The service:

1. Calls `mcp.connect()` before `Runner.run()`
2. Assigns `mcp_servers = [mcp]` to all 8 agents
3. Clears refs and calls `mcp.cleanup()` in a `finally` block

MCP server: `@modelcontextprotocol/server-postgres` via `npx`.

---

## Guardrail Pipeline

Three `InputGuardrail` functions run before any agent processes a message:

| Guardrail | Trigger |
|---|---|
| `detect_jailbreak` | Pattern match on override/injection phrases |
| `detect_pii` | Regex for credit card (16-digit) and SSN (###-##-####) |
| `detect_sql_injection` | Keyword match: `DROP TABLE`, `UNION SELECT`, `OR 1=1`, etc. |

**Guardrail isolation fix**: blocked messages are **not** persisted to DB. History replay filters out `agent_name = 'Guardrail'` rows, preventing re-trigger on subsequent clean messages.

### SQL Strictness Lock

To prevent smaller local models from interpreting database schemas independently and entering hallucination-retry loops (`Max turns 10 exceeded`), all database-aware agents enforce this instruction logic: 
> `WARNING: DO NOT WRITE YOUR OWN SQL QUERIES. YOU MUST COPY AND PASTE THESE EXACT SQL PATTERNS. NEVER INVENT TABLES.`

---

## HITL (Human-in-the-Loop)

`@function_tool(needs_approval=True)` traps `Runner` execution mid-chain. The SDK yields `result.interruptions` to FastAPI, which returns `needs_approval: true` with `approval_items` in the response. Frontend displays an amber warning banner. Execution resumes only when the `Runner` state is resumed with approval.

---

## Inference

- **Provider**: Ollama local server at `http://localhost:11434/v1` (OpenAI-compatible API)
- **Model (recommended)**: `deepseek-v3.1:671b-cloud` — highest tool-calling accuracy in available model set
- **Fallback**: `gpt-oss:120b-cloud`
- **Configured via**: `OLLAMA_MODEL` in `.env`

All agents use `OpenAIChatCompletionsModel` via a shared lazy-initialized `AsyncOpenAI` client.

---

## Setup

### Prerequisites

- PostgreSQL 14+ with database `actuator_ai`
- Ollama running locally with target model pulled
- Node.js 18+ (frontend)
- Python 3.11+ with `uv`

### Install

```fish
# Backend
cd 'Actuator AI'
uv venv && source .venv/bin/activate.fish
uv pip install -r pyproject.toml   # or: uv sync

# Frontend
cd frontend
npm install
```

### Environment

```env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-v3.1:671b-cloud

POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=actuator_ai
```

### Run

```fish
# Backend (serves static portal at /)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Vite dev server (proxies /api to port 8000)
cd frontend && npm run dev
```

| Endpoint | URL |
|---|---|
| Vite frontend | http://localhost:5173 |
| Static portal | http://127.0.0.1:8000 |
| FastAPI docs | http://127.0.0.1:8000/docs |

---

## Stack

| Layer | Technology |
|---|---|
| Agent SDK | `openai-agents >= 0.13.6` |
| Backend | FastAPI + SQLModel + psycopg2 + bcrypt + PyJWT |
| Database access | MCP (`@modelcontextprotocol/server-postgres`) |
| Inference | Ollama (OpenAI-compat API) |
| Frontend | React 19 + Vite 8 + Zustand + Lucide UI |
| Markdown | `marked` |
| Config | `pydantic-settings` + `.env` |
