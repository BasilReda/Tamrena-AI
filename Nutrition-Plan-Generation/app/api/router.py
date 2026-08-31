# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.api.routes import health, nutrition

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(nutrition.router)
