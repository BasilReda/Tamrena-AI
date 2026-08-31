"""
FastAPI dependency injection providers.
"""

import hmac
from functools import lru_cache

# pyrefly: ignore [missing-import]
from fastapi import Header, HTTPException

from app.core.config import settings
from app.retrieval.repository import FoodRepository
from app.retrieval.loader import load_food_dataframe


@lru_cache(maxsize=1)
def get_food_repository() -> FoodRepository:
    """Provide a singleton FoodRepository instance."""
    return FoodRepository()


def require_internal_auth(x_internal_auth: str = Header(default="")) -> None:
    """This service has no user-level auth — see settings.internal_service_token.
    An unset configured token rejects everything (fail closed) rather than
    letting every request through, so a forgotten .env value shows up as a
    hard 401 on every call instead of as a silent open API.
    hmac.compare_digest avoids leaking the token's length/prefix via timing."""
    if not settings.internal_service_token or not hmac.compare_digest(
        x_internal_auth, settings.internal_service_token
    ):
        raise HTTPException(status_code=401, detail="Missing or invalid internal service credentials.")
