"""
Actuator AI — FastAPI Backend

Production-grade multi-agent customer support platform.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from backend.core.config import settings
from backend.db.session import engine

# Import ALL models so SQLModel registers them before create_all
from backend.models.agent import Agent
from backend.models.conversation import Conversation, Message, Customer, SupportTicket

from backend.api.routes.chat import router as chat_router
from backend.api.routes.agents import router as agents_router
from backend.api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Create all tables
    SQLModel.metadata.create_all(engine)
    print(f"✅ {settings.PROJECT_NAME} started. Tables synced.")
    yield
    print(f"⏹ {settings.PROJECT_NAME} shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production multi-agent AI platform with 8 specialist agents.",
    lifespan=lifespan,
)

# CORS — allow all origins for dev, lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app.mount("/static", StaticFiles(directory="backend/static"), name="static")

@app.get("/", response_class=FileResponse)
def root_ui():
    """Serve the basic Chat UI."""
    return FileResponse(os.path.join("backend", "static", "index.html"))

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "agents": 8,
    }
