# Deployment & Hardening Phases

Actionable plan to harden, containerize, and deploy Actuator AI to production.

---

## Phase 1: Security Hardening & Critical Fixes

- [ ] **Fix Global Agent Mutation Race Condition**
  - Isolate MCP assignments per request or instantiate agent copies per stream invocation instead of mutating global module objects.
- [ ] **Secure WebSocket & Endpoints with Auth**
  - Implement JWT verification in WebSocket handshake (`WS /api/v1/chat/ws?token=...`).
  - Add authentication checks on conversation CRUD routes.
- [ ] **Strict Production Configuration Checks**
  - Enforce non-default `SECRET_KEY` and explicit non-wildcard `CORS_ORIGINS` when `ENVIRONMENT=production`.
  - Prevent development fallback keys from starting in production mode.
- [ ] **Auth & Guardrail Hardening**
  - Enforce password complexity requirements and email format validation via Pydantic.
  - Add rate limiting on `/auth/login`, `/auth/signup`, and WebSocket connections via `slowapi` or Redis.
  - Strengthen input guardrails against obfuscated prompt injections and SQL bypass techniques.

---

## Phase 2: Database & Concurrency Robustness

- [ ] **Connection Pooling**
  - Replace ad-hoc psycopg2 connections in `shared/tools/db_tools.py` with SQLAlchemy connection pool or PgBouncer.
- [ ] **Database Migrations (Alembic)**
  - Initialize Alembic for version-controlled database schema migrations replacing direct DDL execution on startup.
- [ ] **Context Window Management**
  - Truncate / summarize conversation history to prevent unbounded token expansion on long chats.
- [ ] **Subprocess & MCP Resource Throttling**
  - Optimize MCP server process lifecycle or direct DB tools to prevent Node.js subprocess memory bloat under high traffic.

---

## Phase 3: Observability, Health Checks & Logging

- [ ] **Structured Logging & Tracing**
  - Replace raw `print` statements with structured JSON logging (`structlog` or standard `logging`).
  - Attach request IDs / correlation IDs across WebSocket messages and backend agent traces.
- [ ] **Deep Health Check**
  - Expand `/health` to verify:
    - PostgreSQL connection status (`SELECT 1`).
    - OmniRouter / LLM gateway endpoint reachability.
    - Disc space and memory thresholds.
- [ ] **Metrics & Monitoring**
  - Expose Prometheus metrics endpoint (`/metrics`) for response latency, token usage, agent routing distribution, and error rates.

---

## Phase 4: Containerization & Cloud Architecture

- [ ] **Production Docker Compose (`docker-compose.prod.yml`)**
  - Setup multi-container stack:
    - `app`: FastAPI backend running with Gunicorn/Uvicorn workers.
    - `postgres`: PostgreSQL 16 with encrypted persistent volume.
    - `caddy` or `nginx`: Reverse proxy handling TLS termination (Let's Encrypt), static asset serving, and WebSocket proxying.
    - `redis`: Shared cache, rate limiting, and session coordination.
    - `omniroute` (optional self-hosted container or remote cloud endpoint).
- [ ] **Multi-stage Docker Optimization**
  - Ensure backend image runs under dedicated non-root user (`actuator`).
  - Cache npm and uv layers for rapid builds.
  - Exclude test artifacts, development dependencies, and local `.env` files via `.dockerignore`.

---

## Phase 5: CI/CD & Automated Verification

- [ ] **GitHub Actions CI Pipeline**
  - Automated formatting and linting: `ruff check .`, `eslint`.
  - Security audit: `bandit -r backend shared`, `trivy` container scanning.
  - Automated tests: `uv run pytest` covering unit tests, agent handoffs, guardrails, and auth endpoints.
  - Automatic container image build and push to container registry (GHCR/Docker Hub).
- [ ] **Staging Deployment & Smoke Testing**
  - Automated deployment to staging instance.
  - Automated smoke test verifying WebSocket streaming, agent handoffs, and auth flow.

---

## Phase 6: Production Launch & Day-2 Operations

- [ ] **DNS & TLS Provisioning**
  - Configure domain DNS records (A/CNAME) pointing to host or load balancer.
  - Provision automatic SSL/TLS certificates via Caddy or certbot.
- [ ] **Backup & Disaster Recovery**
  - Configure scheduled automated PostgreSQL backups (e.g. `pg_dump` to S3/B2 with retention policy).
- [ ] **Load Testing & Benchmark**
  - Run concurrent WebSocket load tests (k6 or Locust) to confirm connection stability under target concurrency.
- [ ] **Audit Trail Review**
  - Verify audit log integrity, hallucination risk metrics, and customer feedback data.

