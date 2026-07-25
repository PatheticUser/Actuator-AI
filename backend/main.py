"""
Actuator AI — FastAPI Backend

Production-grade multi-agent customer support platform.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import SQLModel
import os

from backend.core.config import settings
from backend.db.session import engine

# Import ALL models so SQLModel registers them before create_all
from backend.models.agent import Agent
from backend.models.conversation import Conversation, Message, Customer, SupportTicket

from backend.api.routes.chat import router as chat_router
from backend.api.routes.agents import router as agents_router
from backend.api.routes.auth import router as auth_router


# ── Paths ────────────────────────────────────────────────
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
STATIC_FALLBACK = os.path.join(os.path.dirname(__file__), "static")


def init_db_tables():
    """Verify products and business tables exist and are seeded on startup."""
    try:
        from shared.tools.db_tools import _query, _conn
        rows = _query("SELECT COUNT(*) FROM products")
        if not rows or "error" in rows[0] or rows[0].get("count", 0) == 0:
            print("🌱 Seeding database tables with 21 business data tables...")
            db_dir = os.path.join(os.path.dirname(__file__), "db")
            schema_path = os.path.join(db_dir, "schema.sql")
            seed_path = os.path.join(db_dir, "seed.sql.bak")
            
            with _conn() as conn:
                with conn.cursor() as cur:
                    if os.path.exists(schema_path):
                        with open(schema_path, "r") as f:
                            cur.execute(f.read())
                            conn.commit()
                    if os.path.exists(seed_path):
                        with open(seed_path, "r") as f:
                            seed_sql = f.read()
                            parts = seed_sql.split('-- ==================== AUDIT LOGS ====================')
                            cur.execute(parts[0])
                            conn.commit()
                            cur.execute("""
                                INSERT INTO conversations (id, customer_id, customer_email, channel, status) VALUES
                                ('conv-sample-001', 1, 'ahmed@techvista.pk', 'web', 'resolved'),
                                ('conv-sample-002', 2, 'sara@novabyte.io', 'web', 'resolved'),
                                ('conv-sample-003', 3, 'omar@cloudmatrix.ae', 'web', 'resolved'),
                                ('conv-sample-004', 4, 'bilal@datapulse.pk', 'web', 'resolved'),
                                ('conv-sample-005', 5, 'ayesha@meridianhealth.pk', 'web', 'resolved')
                                ON CONFLICT DO NOTHING;
                            """)
                            conn.commit()
                            if len(parts) > 1:
                                cur.execute('-- ==================== AUDIT LOGS ====================' + parts[1])
                                conn.commit()
            print("✅ Database tables successfully initialized & seeded!")
    except Exception as e:
        print(f"⚠ Database startup init notice: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Create all tables
    SQLModel.metadata.create_all(engine)
    init_db_tables()
    print(f"✅ {settings.PROJECT_NAME} started ({settings.ENVIRONMENT}). Tables synced.")
    yield
    print(f"⏹ {settings.PROJECT_NAME} shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production multi-agent AI platform with 8 specialist agents.",
    lifespan=lifespan,
    # Disable docs in production
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS — env-driven origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "agents": 8,
    }


# ── Static File Serving ─────────────────────────────────
# Serve React SPA from frontend/dist if it exists (production build),
# otherwise fall back to backend/static/index.html (lightweight UI).

if os.path.isdir(FRONTEND_DIST) and os.path.isfile(os.path.join(FRONTEND_DIST, "index.html")):
    # Mount assets subdirectory for JS/CSS bundles
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Serve static files at root (favicon, icons, etc.)
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST), name="frontend-static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Catch-all: serve file if exists, else index.html for client-side routing."""
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    # Fallback: serve lightweight static HTML UI
    app.mount("/static", StaticFiles(directory=STATIC_FALLBACK), name="static")

    @app.get("/")
    def root_ui():
        """Serve the basic Chat UI."""
        return FileResponse(os.path.join(STATIC_FALLBACK, "index.html"))

