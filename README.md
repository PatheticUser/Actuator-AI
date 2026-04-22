# Actuator AI

**Production-Grade Multi-Agent Customer Support Platform**

Enterprise-ready AI support system with 8 specialized agents, real-time database access via MCP, and human-in-the-loop escalation. Built on **OpenAI Agents SDK**, orchestrated via **FastAPI**, backed by **PostgreSQL** with full audit logging and compliance guardrails.

---

## System Architecture

### Request Flow Architecture

```
Client → WebSocket /api/v1/chat/ws
  │
  ├─▶ FastAPI reconstructs conversation history from PostgreSQL
  │   (guardrail-blocked messages filtered out)
  │
  ├─▶ Fresh MCP server instance spawned per request
  │   (factory pattern avoids singleton lifecycle conflicts)
  │
  ├─▶ Native Runner.run_streamed() yields AgentResponseStream JSON chunks
  │
  ├─▶ Supervisor agent classifies request intent
  │   → Routes to appropriate specialist agent
  │
  ├─▶ Specialist agent queries database via MCP SQL guardrails
  │   → Streams response tokens to client in real-time
  │
  ├─▶ Client UI detects agent handoffs (agent_update events)
  │   → Splits visual message bubbles automatically
  │
  ├─▶ Messages persisted to database only on successful stream completion
  │
  └─▶ WebSocket connection terminates gracefully
      (resource-efficient request lifecycle)
```

## Agent Specialization Matrix

| Agent | Domain Expertise | Core Tools | Database Access |
|---|---|---|---|
| **Supervisor Router** | Request triage & classification | `classify_request`, `escalate_to_human` | — |
| **Technical Specialist** | API errors, SDK issues, KB search | `diagnose_service`, `check_system_status`, `create_support_ticket` | `knowledge_articles`, `support_tickets` |
| **Account Security Agent** | Login, 2FA, lockout, profile management | `unlock_account`, `initiate_2fa_setup`, `reset_2fa`, `initiate_password_reset`, `update_profile` | `customers`, `customer_contacts`, `security_events` |
| **Billing Finance Agent** | Invoices, refunds, subscription plans, credits | `change_plan`, `process_refund`*, `apply_credit` | `invoices`, `invoice_line_items`, `subscriptions`, `products`, `payments`, `refunds`, `api_usage` |
| **Success Retention Agent** | Customer health scores, churn prevention, renewals | `schedule_check_in`, `create_renewal_offer`, `log_churn_intervention` | `customers`, `api_usage`, `feature_flags`, `feedback` |
| **Operations Sync Agent** | CRM integration, ticket management, Jira sync | `update_crm_note`, `create_support_ticket`, `create_jira_ticket`, `update_jira_ticket` | `support_tickets`, `ticket_comments`, `notifications_log` |
| **Linguistic Agent** | Sentiment analysis, translation, language detection | `detect_language`, `translate_text`, `analyze_sentiment`, `assess_communication_quality` | `feedback` |
| **Audit Agent** | Quality assurance, hallucination detection, policy compliance | `check_hallucination`, `check_policy_compliance`, `audit_conversation`, `score_response_accuracy`, `generate_qa_report` | `audit_logs`, `escalations`, `conversations` |

`*` `process_refund` tool has `needs_approval=True` → triggers human-in-the-loop interruption

---

## Database Schema

**26 tables organized into 5 logical domains:**

```
🗣️  Conversation State
   - conversations, messages

👥 Customer Data  
   - customers, customer_contacts, subscriptions, products

🔐 Authentication
   - customer (FastAPI Auth model with hashed_password)

💰 Billing & Payments
   - invoices, invoice_line_items, payments, refunds, api_usage

⚙️  Operational Systems
   - support_tickets, ticket_comments, knowledge_articles
   - feature_flags, feedback, audit_logs, escalations
   - security_events, notifications_log, feature_changelog
```

All agents receive the `query` MCP tool for direct PostgreSQL read access with strict schema validation. Write operations go through typed `@function_tool` wrappers with Pydantic-validated parameters and approval workflows.

---

## MCP (Model Context Protocol) Integration

**Per-Request MCP Server Isolation**

Each WebSocket request receives a fresh `MCPServerStdio` instance via `create_mcp_postgres()`, avoiding singleton lifecycle conflicts (`Server not initialized`) during agent handoffs.

**Integration Flow:**
1. `mcp.connect()` called before `Runner.run()`
2. `mcp_servers = [mcp]` assigned to all 8 specialist agents
3. References cleared and `mcp.cleanup()` called in `finally` block

**MCP Server**: `@modelcontextprotocol/server-postgres` executed via `npx`, providing secure, schema-validated database tool access with full PostgreSQL type safety.

---

## Security & Guardrail Pipeline

**Three-Layer Input Validation**

Three `InputGuardrail` functions execute before any agent processes incoming messages:

| Guardrail | Detection Method | Purpose |
|---|---|---|
| `detect_jailbreak` | Pattern matching on override/injection phrases | Prevents prompt injection attacks |
| `detect_pii` | Regex patterns (credit cards: 16-digit, SSN: ###-##-####) | Protects sensitive customer data |
| `detect_sql_injection` | Keyword matching (`DROP TABLE`, `UNION SELECT`, `OR 1=1`) | Blocks database injection attempts |

**Guardrail Isolation**: Blocked messages are **not persisted** to database. History replay filters exclude `agent_name = 'Guardrail'` rows, preventing re-triggering on subsequent clean messages.

### SQL Strictness Enforcement

Prevents local models from schema hallucination and retry loops (`Max turns 10 exceeded`) by enforcing strict SQL pattern usage:

> **WARNING: DO NOT WRITE YOUR OWN SQL QUERIES. YOU MUST COPY AND PASTE THESE EXACT SQL PATTERNS. NEVER INVENT TABLES OR COLUMNS.**

---

## HITL (Human-in-the-Loop) Escalation

**Approval-Based Workflow Interruption**

`@function_tool(needs_approval=True)` traps `Runner` execution mid-chain. The SDK yields `result.interruptions` to FastAPI, which returns:
- `needs_approval: true` flag
- `approval_items` with detailed request context

Frontend displays amber warning banner with approval options. Execution resumes only when human supervisor approves via `Runner` state resumption.

---

## Model Inference & Configuration

**Local Model Hosting**
- **Provider**: Ollama local inference server
- **API Endpoint**: `http://localhost:11434/v1` (OpenAI-compatible)
- **Primary Model**: `deepseek-v3.1:671b-cloud` — highest tool-calling accuracy
- **Fallback Model**: `gpt-oss:120b-cloud` — backup for availability
- **Configuration**: `OLLAMA_MODEL` environment variable

**Client Architecture**
All agents utilize `OpenAIChatCompletionsModel` via shared lazy-initialized `AsyncOpenAI` client for connection pooling and efficiency.

---

## Setup

## Prerequisites

- **PostgreSQL 14+** with database `actuator_ai`
- **Ollama** running locally with target model pulled (`deepseek-v3.1:671b-cloud` recommended)
- **Node.js 18+** (frontend development)
- **Python 3.11+** with `uv` package manager
- **Redis** (optional, for production session storage)

## Installation

### Backend Setup

```bash
# Clone and setup
cd actuator-ai

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -e .  # Install in development mode
```

### Frontend Setup

```bash
cd frontend
npm install  # Install npm dependencies
```

## Environment Configuration

Create `.env` file in project root:

```env
# Ollama Inference
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-v3.1:671b-cloud

# PostgreSQL Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=actuator_ai

# Application Settings
PROJECT_NAME=Actuator AI
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key-here  # Change in production

# Optional: Redis for production
# REDIS_URL=redis://localhost:6379
```

## Running the Application

### Development Mode

```bash
# Terminal 1: Backend (serves API + static UI)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend (development server with hot reload)
cd frontend
npm run dev
```

### Production Mode

```bash
# Build frontend for production
cd frontend
npm run build

# Backend serves built frontend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

| Endpoint | URL | Description |
|---|---|---|
| Vite frontend | http://localhost:5173 | React development server with hot reload |
| Static portal | http://127.0.0.1:8000 | Production UI served by FastAPI |
| FastAPI docs | http://127.0.0.1:8000/docs | Interactive API documentation |
| Health check | http://127.0.0.1:8000/health | System status endpoint |

---

## API Documentation

### WebSocket Chat Endpoint
```
WS /api/v1/chat/ws
```

**Request Format:**
```json
{
  "message": "Customer query text",
  "conversation_id": "uuid-or-null",
  "customer_id": "uuid-or-null"
}
```

**Response Stream Events:**
- `text` - Content tokens
- `agent_update` - Agent handoff notifications
- `needs_approval` - Human intervention required
- `error` - Processing failures

### REST Endpoints
- `GET /api/v1/agents` - List available agents
- `POST /api/v1/auth/login` - Customer authentication
- `GET /api/v1/conversations/{id}` - Retrieve conversation history

---

## Project Structure

```
actuator-ai/
├── actuator_agents/          # 8 specialist agent implementations
│   ├── supervisor_router/
│   ├── technical_specialist/
│   └── ...
├── backend/                  # FastAPI application
│   ├── api/routes/          # REST/WebSocket endpoints
│   ├── models/              # SQLModel database models
│   ├── services/           # Business logic
│   └── main.py             # Application entry point
├── frontend/                # React Vite application
│   ├── src/
│   │   ├── api.ts          # API client
│   │   ├── App.tsx         # Main component
│   │   └── store.ts        # Zustand state management
│   └── package.json
├── shared/                  # Cross-component utilities
│   ├── guardrails/         # Security validations
│   ├── models/            # Shared Pydantic models
│   └── tools/             # Common function tools
└── pyproject.toml          # Python dependencies
```

---

## Deployment

### Docker Compose (Production)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: actuator_ai
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_SERVER=postgres
      - OLLAMA_BASE_URL=http://ollama:11434/v1
    depends_on:
      - postgres
      - ollama

volumes:
  postgres_data:
  ollama_data:
```

### Environment Variables (Production)

```env
# Required
POSTGRES_SERVER=postgres
POSTGRES_PASSWORD=secure-password
OLLAMA_BASE_URL=http://ollama:11434/v1
SECRET_KEY=your-production-secret-key

# Optional
REDIS_URL=redis://redis:6379
SENTRY_DSN=your-sentry-dsn
```

---

## Development

### Running Tests
```bash
# Backend tests
pytest backend/tests/

# Frontend tests  
cd frontend && npm test
```

### Code Style
```bash
# Python formatting
uv run black .
uv run isort .

# Type checking
uv run mypy .

# Frontend formatting
cd frontend && npm run format
```

---

## Monitoring & Observability

### Health Checks
- Application: `GET /health`
- Database: Connection pooling status
- Ollama: Model availability

### Logging
- Structured JSON logging
- Request/response correlation IDs
- Agent execution traces

### Metrics
- Request latency percentiles
- Agent handoff success rates
- Guardrail trigger counts
- Database query performance

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow existing code style patterns
- Add tests for new functionality
- Update documentation for API changes
- Use conventional commit messages

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For issues and questions:
- Create GitHub Issues for bugs
- Check existing documentation
- Review API specifications

## Acknowledgments

- OpenAI Agents SDK team
- FastAPI community
- Ollama inference platform
- Model Context Protocol working group

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Agent Framework** | OpenAI Agents SDK | ≥0.13.6 | Multi-agent orchestration |
| **Backend API** | FastAPI + Uvicorn | ≥0.135.3 | REST/WebSocket endpoints |
| **Database ORM** | SQLModel | ≥0.0.38 | Type-safe PostgreSQL access |
| **Authentication** | bcrypt + PyJWT | ≥5.0.0 + ≥2.12.1 | Password hashing + JWT tokens |
| **Database Access** | MCP PostgreSQL Server | - | Real-time SQL tool access |
| **Inference** | Ollama | ≥0.6.1 | Local model hosting (OpenAI-compatible) |
| **Frontend** | React 19 + Vite 8 | - | Modern SPA with hot reload |
| **State Management** | Zustand | - | Lightweight React state |
| **UI Components** | Lucide React | - | Consistent iconography |
| **Configuration** | Pydantic Settings | ≥2.13.1 | Type-safe environment config |
| **Markdown Rendering** | marked | - | Secure message formatting |
