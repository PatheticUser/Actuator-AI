# ── Stage 1: Build React Frontend ─────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python Runtime ──────────────────────────────
FROM python:3.11-slim AS runtime

# System deps: Node.js (required for MCP npx subprocess) + PostgreSQL client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get purge -y gnupg && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Install MCP postgres server globally so it executes instantly without npx network overhead or permission issues
RUN npm install -g @modelcontextprotocol/server-postgres

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install Python dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY backend/ ./backend/
COPY actuator_agents/ ./actuator_agents/
COPY shared/ ./shared/
COPY .env.example ./.env.example

# Copy built frontend assets
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# Install project itself
RUN uv sync --frozen --no-dev

# Non-root user
RUN groupadd -r actuator && useradd -r -g actuator -d /app actuator && \
    chown -R actuator:actuator /app
USER actuator

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
