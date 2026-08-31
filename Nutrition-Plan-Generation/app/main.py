"""
FastAPI Application Factory

Startup sequence:
  1. Configure logging
  2. Set LangSmith env vars
  3. Load food dataset (singleton via lru_cache)
  4. Initialise FoodRepository and inject into graph nodes
  5. Register routes
  6. Start serving
"""

import os
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.retrieval.loader import load_food_dataframe
from app.retrieval.repository import FoodRepository
from app.graph.nodes import set_food_repository
from app.api.router import api_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    # ── Configure LangSmith ──────────────────────────────────────────────────
    api_key = settings.langsmith_api_key or settings.langchain_api_key or os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY") or ""
    project = settings.langsmith_project or settings.langchain_project or os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or "tamrena"
    endpoint = settings.langsmith_endpoint or settings.langchain_endpoint or os.getenv("LANGSMITH_ENDPOINT") or os.getenv("LANGCHAIN_ENDPOINT") or "https://api.smith.langchain.com"
    tracing = settings.langsmith_tracing or settings.langchain_tracing_v2 or os.getenv("LANGSMITH_TRACING") or os.getenv("LANGCHAIN_TRACING_V2") or "true"

    os.environ["LANGSMITH_TRACING"] = tracing
    os.environ["LANGCHAIN_TRACING_V2"] = tracing
    os.environ["LANGSMITH_ENDPOINT"] = endpoint
    os.environ["LANGCHAIN_ENDPOINT"] = endpoint
    if api_key:
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGSMITH_PROJECT"] = project
    os.environ["LANGCHAIN_PROJECT"] = project
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    logger.info("LangSmith tracing enabled | project=%s | endpoint=%s", project, endpoint)

    # ── Pre-load food dataset ─────────────────────────────────────────────────
    logger.info("Loading food dataset...")
    load_food_dataframe()  # warms the lru_cache

    # ── Initialise FoodRepository and inject into graph nodes ─────────────────
    repo = FoodRepository()
    set_food_repository(repo)
    logger.info("FoodRepository initialised and injected into graph")

    logger.info("✅ Nutrition AI Service ready at http://localhost:8000/docs")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Nutrition AI Multi-Agent System",
        description=(
            "Personalized AI-powered nutrition planning using a Multi-Agent LangGraph pipeline. "
            "Generates scientifically grounded, validated meal plans with Egyptian food support."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS (open for microservice integration) ──────────────────────────────
    # This API is called server-to-server (tamreena-web's BFF), never from a
    # browser session with cookies, so allow_credentials=False keeps the
    # wildcard origin valid per the Fetch spec (browsers refuse
    # "*" + credentialed requests) without weakening anything real callers
    # rely on — actual authorization is the X-Internal-Auth header checked
    # in app/api/dependencies.py, not CORS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    return app


app = create_app()
