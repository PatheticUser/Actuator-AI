# syntax=docker/dockerfile:1.7
# ══════════════════════════════════════════════════════════════════════
#  Actuator AI — multi-arch production image
#
#  Primary target : linux/arm64 / aarch64 (Oracle Cloud Ampere A1, Always Free)
#  Also builds for : linux/amd64
#
#  arm64 safety notes
#  -------------------
#  * Base images all publish official linux/arm64 manifests:
#      node:20-bookworm-slim, python:3.11-slim-bookworm,
#      ghcr.io/astral-sh/uv:latest
#  * Node.js is copied from the official multi-arch node image instead of
#    NodeSource .debs, so the binary always matches the build architecture.
#  * Every Python wheel pinned in uv.lock ships a
#    manylinux2014_aarch64 / musllinux aarch64 build
#    (numpy, pillow, psycopg2-binary, bcrypt, pydantic-core, ...).
#    Nothing is compiled from source, so no cross-toolchain is required.
#  * The only native binary beyond the interpreter is Tesseract OCR,
#    installed from Debian's own multi-arch `tesseract-ocr` package.
#  * There is no PyTorch, ONNX, VAD or TTS runtime in this codebase —
#    the LLM providers (Gemini / OpenAI / OmniRouter / Ollama) are called
#    over HTTP, so no ML wheel has to be compiled for aarch64.
# ══════════════════════════════════════════════════════════════════════


# ── Stage 1: React frontend build (arch-independent output) ────────────
# Runs on the build host's architecture ($BUILDPLATFORM) because only JS
# artifacts are produced — this keeps cross-builds fast under QEMU.
FROM --platform=$BUILDPLATFORM node:20-bookworm-slim AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python runtime ────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

# System deps:
#   curl               -> container HEALTHCHECK
#   libstdc++6         -> Node.js runtime (copied below)
#   tesseract-ocr      -> OCR tool used by pytool (multi-arch Debian pkg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        libstdc++6 \
        tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

# ── Node.js 20 (official multi-arch build) + MCP Postgres server ──────
# Copying from the official node image guarantees the node binary matches
# TARGETPLATFORM (arm64 on OCI Ampere A1) instead of relying on a
# third-party apt repository.
COPY --from=node:20-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js  /usr/local/bin/npm && \
    ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js  /usr/local/bin/npx && \
    npm install -g @modelcontextprotocol/server-postgres && \
    npm cache clean --force && \
    node --version && npm --version && which mcp-server-postgres

# ── uv (multi-arch static build) ───────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Deterministic, cache-friendly dependency layer
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=automatic
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Application code ───────────────────────────────────────────────────
COPY backend/ ./backend/
COPY actuator_agents/ ./actuator_agents/
COPY shared/ ./shared/
COPY .env.example ./.env.example

# Built SPA (served by FastAPI from frontend/dist)
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# Install the project itself into the venv
RUN uv sync --frozen --no-dev

# ── Non-root user ──────────────────────────────────────────────────────
RUN groupadd -r actuator && useradd -r -g actuator -d /app actuator && \
    chown -R actuator:actuator /app
USER actuator

EXPOSE 8000

# Belt-and-braces: compose defines the authoritative healthcheck too.
# /health returns HTTP 200 even when degraded, so also assert the payload.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=5 \
    CMD curl -fsS http://localhost:8000/health | grep -Eq '"status": *"ok"' || exit 1

# --no-sync: the venv is baked into the image, never re-resolve at boot.
# --proxy-headers/--forwarded-allow-ips: honour X-Forwarded-* from Caddy.
STOPSIGNAL SIGTERM
CMD ["sh", "-c", "exec uv run --no-sync uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips='*' --timeout-graceful-shutdown 30"]
