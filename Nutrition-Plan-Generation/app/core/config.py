# pyrefly: ignore [missing-import]
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application configuration loaded from .env"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())

    # ── Google GenAI / Gemini Central Configuration ───────────────────────────
    gemini_api_key: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    model_name: str = "gemini-3.5-flash-lite"

    # ── ITI Bedrock (Legacy fallback) ──────────────────────────────────────────
    sbg_api_key: str = ""
    sbg_model_id: str = "us.meta.llama3-3-70b-instruct-v1:0"

    # ── Groq (Legacy fallback) ────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_api_key2: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    composition_mean_model: str = "openai/gpt-oss-120b"

    # ── LangSmith ─────────────────────────────────────────────────────────────
    langsmith_tracing: str = "true"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "tamrena"
    langchain_tracing_v2: str = "true"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str = ""
    langchain_project: str = "tamrena"

    # ── Anthropic ─────────────────────────────────────────────────────────────
    anthropic_api_key: str = ""

    # ── Food Dataset ──────────────────────────────────────────────────────────
    food_data_path: str = "DataPrep/usedData/foods_master_final.parquet"

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    # ── Agent ─────────────────────────────────────────────────────────────────
    max_retries: int = 3

    # ── Internal service auth ────────────────────────────────────────────────
    internal_service_token: str = ""


settings = Settings()

# Normalize Gemini keys and model defaults
if not settings.gemini_api_key:
    settings.gemini_api_key = settings.google_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
if not settings.google_api_key:
    settings.google_api_key = settings.gemini_api_key

active_model = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME")
if active_model:
    settings.gemini_model = active_model
    settings.model_name = active_model
