# Gaps & Improvements Analysis

Comprehensive audit of vulnerabilities, performance bottlenecks, architecture limitations, and operational gaps prior to production deployment.

---

## 1. Security Vulnerabilities & Gaps

### Critical / High
1. **Unprotected WebSockets & Missing Auth on Chat Endpoints**
   - **Current:** `WS /api/v1/chat/ws` accepts client messages without JWT validation or user identity verification. Any client can connect and trigger expensive LLM pipeline executions.
   - **Fix:** Require JWT token in WebSocket handshake query parameter (`?token=...`) or first frame auth message. Reject unauthenticated connections immediately.

2. **Insecure Password / Email Validation**
   - **Current:** `signup` in `backend/api/routes/auth.py` does not validate email format, password complexity (length, entropy), or rate-limit brute force attempts.
   - **Fix:** Integrate `pydantic[email]` (`EmailStr`), enforce minimum 8–12 char password complexity, and implement exponential backoff / IP rate limiting via Redis or `slowapi`.

3. **CORS Wildcard In Production Default**
   - **Current:** `CORS_ORIGINS` defaults to `*`. If not explicitly overridden in `.env`, production permits any external origin with `allow_credentials=True`.
   - **Fix:** Enforce explicit domain list in production in `Settings` validator (disallow `*` when `ENVIRONMENT=production`).

4. **Weak / Simplistic Guardrails**
   - **Current:** `shared/guardrails/safety.py` uses naive string substrings (`"DROP TABLE"`, `"OR 1=1"`, `"ignore your instructions"`). Bypassable via unicode obfuscation, newline breaks, synonym injection, or hex encoding.
   - **Fix:** Implement robust semantic/regex detection or integrate an established guardrail model/library (e.g. Llama Guard, NeMo Guardrails, or regex with tokenization).

5. **Direct Arbitrary Parameter Injection in DB Tools**
   - **Current:** While most queries use parameterized queries, `_query` and `_execute` in `shared/tools/db_tools.py` create raw psycopg2 connections without connection pooling. Any dynamically formatted string in tools poses SQL injection danger.
   - **Fix:** Use strict SQLAlchemy/SQLModel parameterized queries everywhere and connection pooling (`psycopg2.pool.ThreadedConnectionPool` or SQLAlchemy engine pool).

---

## 2. Concurrency & Architectural Bottlenecks

1. **Global Agent Object Mutation Race Condition**
   - **Current:** In `backend/services/agent_service.py`:
     ```python
     for ag in _ALL_AGENTS:
         ag.mcp_servers = [mcp]
     ```
     `_semaphore` allows up to 10 concurrent requests (`_MAX_CONCURRENT_REQUESTS = 10`), but `_ALL_AGENTS` are **global module-level singleton objects**. Concurrent requests overwrite `ag.mcp_servers` simultaneously, causing MCP server leaks, cross-tenant data leaks, or crashes mid-stream.
   - **Fix:** Instantiate agents per request or clone agent instances with isolated `mcp_servers` contexts per runner invocation.

2. **MCP Subprocess Spawning Overhead**
   - **Current:** Every WebSocket request spawns a separate `npx -y @modelcontextprotocol/server-postgres` or `mcp-server-postgres` Node.js subprocess. Under 10+ concurrent requests, 10 separate Node.js processes spawn simultaneously, exhausting system RAM and CPU.
   - **Fix:** Use a pooled or persistent MCP proxy, or connect specialist agents directly via internal async database tools without CLI subprocess forks for read queries.

3. **Single Process Uvicorn vs Multi-Worker State**
   - **Current:** `Dockerfile` starts Uvicorn with `--workers 4`. Because the in-memory semaphore and agent mutations reside in process memory, each worker runs independently with no unified connection tracking or shared cache.
   - **Fix:** Keep backend single worker per container and scale horizontally via Docker Compose / Kubernetes replicas with Redis as centralized state coordinator.

---

## 3. Reliability & Operational Gaps

1. **Health Check Shallow Ping**
   - **Current:** `/health` returns static JSON (`{"status": "ok", ...}`) without testing PostgreSQL connectivity or OmniRouter/LLM reachability.
   - **Fix:** Add deep health check verifying DB connection query (`SELECT 1`) and OmniRouter HTTP ping.

2. **Unbounded Conversation History Context**
   - **Current:** Entire conversation history is loaded and fed to the LLM without context window truncation or summarization. Long conversations will eventually hit context token limits or trigger high latency and cost.
   - **Fix:** Implement rolling window (e.g. last 10 turns) with automatic background conversation summarization.

3. **Logging & Observability**
   - **Current:** Uses raw `print()` statements throughout backend and agent services. No request ID correlation, structured JSON logs, or OpenTelemetry tracing.
   - **Fix:** Replace `print` with Python `logging` or `structlog`, add correlation IDs to WebSocket and REST requests, and wire into OpenTelemetry / Prometheus metrics.

---

## 4. Frontend & UX Improvements

1. **Token Refresh & Expiration Handling**
   - **Current:** Frontend stores JWT in localStorage without automatic refresh token exchange or clean handling when expired (returns generic error or WebSocket drop).
   - **Fix:** Add axios/fetch interceptor to detect 401 and redirect to `/login` with session expiration alert.

2. **WebSocket Auto-Reconnect & Heartbeat**
   - **Current:** If network drops or proxy drops idle connection, WebSocket terminates without auto-reconnect backoff.
   - **Fix:** Implement client-side heartbeat ping/pong and exponential backoff reconnection.

3. **File / Image Upload Restrictions**
   - **Current:** Client can send arbitrary base64 strings; image OCR parses entire base64 payload in memory without size or MIME type validation.
   - **Fix:** Validate file type (PNG, JPEG, WebP) and enforce maximum upload size (e.g. 5MB) on client and server.

---

## 5. Deployment & Infrastructure Gaps

1. **OmniRouter Dependency In Production**
   - **Current:** `docker-compose.yml` relies on external host (`host.docker.internal:20128`) for OmniRouter. In standalone cloud production, OmniRouter is missing unless deployed as a companion container or remote URL is specified.
   - **Fix:** Add `omniroute` service definition in `docker-compose.prod.yml` or document cloud AI gateway setup (OpenAI/Groq/LiteLLM fallback).

2. **Database Migration Pipeline**
   - **Current:** Database initialized via raw SQL files and `metadata.create_all()`. No schema migration tool (Alembic) configured for safe future updates without data loss.
   - **Fix:** Initialize Alembic (`alembic init`) for version-controlled, reversible database migrations.

3. **Missing Reverse Proxy & SSL Configuration**
   - **Current:** App exposes raw port 8000. No Nginx/Caddy container configured for SSL termination, HTTP/2, and static asset caching.
   - **Fix:** Add Nginx/Caddy service in `docker-compose.yml` with automated Let's Encrypt certificates.

