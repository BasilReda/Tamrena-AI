"""
Nutrition routes: proxies real macro/meal-plan generation to the
Nutrition-Plan-Generation coworker service (a real multi-agent LangGraph
pipeline, not mocked). That service has no auth of its own — the BFF
still requires the caller to be signed in, same pattern as the
Computer-Vision and Workout proxies. The SSE progress-stream proxy is
added onto this same router in a later change — see
stream_nutrition_progress below.
"""

import json
from contextlib import AsyncExitStack
from typing import Literal, Optional
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.auth.dependencies import get_verified_token, get_verified_token_for_stream
from app.auth.models import get_last_nutrition_run_id, set_last_nutrition_run_id
from app.auth.tokens import decode_access_token
from app.config import INTERNAL_SERVICE_TOKEN, NUTRITION_API_URL
from app.rate_limit import nutrition_generate_limiter
from app.tamreena_client import call_upstream, proxy_json

router = APIRouter(prefix="/api/nutrition")


class NutritionGenerateRequest(BaseModel):
    age: int = Field(..., ge=10, le=100)
    gender: Literal["male", "female"]
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=30, le=300)
    goal: Literal["fat_loss", "weight_loss", "muscle_gain", "bulking", "maintenance", "recomposition"]
    activity_level: Literal["sedentary", "lightly_active", "moderate", "very_active", "extra_active"] = "moderate"
    diet_type: Literal["normal", "vegetarian", "vegan", "keto", "high_protein"] = "normal"
    preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    additional_notes: Optional[str] = Field(default=None, max_length=500)
    # "dataset" composes meals from the Egyptian food DB in English;
    # "llm_arabic" lets the LLM freely generate three full-day Arabic meal
    # plan options (triple_meal_plan) instead of a single meal_plan.
    meal_generation_mode: Literal["dataset", "llm_arabic"] = "dataset"


@router.post("/generate")
async def generate_nutrition_plan(body: NutritionGenerateRequest, token: str = Depends(get_verified_token)):
    if not nutrition_generate_limiter.check(decode_access_token(token)):
        raise HTTPException(status_code=429, detail="Too many plan generation requests — please slow down.")
    # Upstream AWS endpoint: http://nutrition-agent.fitness-app-prod.local:8000/generate-plan
    resp = await call_upstream(
        "POST", "/generate-plan", token=None, base_url=NUTRITION_API_URL, json=body.model_dump()
    )
    if resp is not None and resp.status_code == 404:
        resp = await call_upstream(
            "POST", "/api/v1/nutrition/generate", token=None, base_url=NUTRITION_API_URL, json=body.model_dump()
        )
    if resp is not None and resp.status_code == 202:
        try:
            run_id = resp.json().get("run_id")
        except ValueError:
            run_id = None
        if run_id:
            set_last_nutrition_run_id(decode_access_token(token), run_id)
    return proxy_json(resp, internal_auth=True)


@router.get("/last")
async def get_last_nutrition_run(token: str = Depends(get_verified_token)):
    """Lets the Nutrition tab resume the user's most recent plan instead of
    always dropping them on a blank intake form — the frontend has no other
    way to learn a run_id exists once it's left the results page's URL."""
    run_id = get_last_nutrition_run_id(decode_access_token(token))
    return {"run_id": run_id}


def _assert_owns_run(user_id: str, run_id: str) -> None:
    """Nutrition-Plan-Generation has no auth or per-user scoping of its own
    (see module docstring) — run_id is proxied straight through to it, so
    the BFF is the only place that can stop one signed-in user from reading
    another user's nutrition plan by run_id. This service only ever tracks
    each user's most recent run (see set_last_nutrition_run_id), so
    "owns" means "is the caller's current run_id"."""
    if run_id != get_last_nutrition_run_id(user_id):
        raise HTTPException(404, "Unknown nutrition run.")


@router.get("/result/{run_id}")
async def get_nutrition_result(run_id: str, token: str = Depends(get_verified_token)):
    _assert_owns_run(decode_access_token(token), run_id)
    resp = await call_upstream(
        "GET", f"/api/v1/nutrition/result/{quote(run_id, safe='')}", token=None, base_url=NUTRITION_API_URL
    )
    return proxy_json(resp, internal_auth=True)


@router.get("/stream/{run_id}")
async def stream_nutrition_progress(run_id: str, token: str = Depends(get_verified_token_for_stream)):
    """
    Proxies Nutrition-Plan-Generation's real SSE progress stream. token is
    a query param (not a header) because the browser's native EventSource
    API cannot set custom headers — same constraint already solved for the
    Workout plan-generation stream in app/workout/routes.py's stream_plan,
    whose exact structure this mirrors (AsyncExitStack-managed streaming
    httpx client, raw-byte passthrough, clean JSON on non-200 instead of a
    hung stream) — the only difference is no Authorization header is
    forwarded (this upstream has no user-level auth), but the shared
    internal-service secret is (see app/config.py's INTERNAL_SERVICE_TOKEN
    — this upstream does require that one).
    """
    _assert_owns_run(decode_access_token(token), run_id)
    stack = AsyncExitStack()
    try:
        client = await stack.enter_async_context(httpx.AsyncClient(base_url=NUTRITION_API_URL, timeout=None))
        upstream = await stack.enter_async_context(
            client.stream(
                "GET",
                f"/api/v1/nutrition/stream/{quote(run_id, safe='')}",
                headers={"X-Internal-Auth": INTERNAL_SERVICE_TOKEN},
            )
        )
    except httpx.HTTPError as exc:
        await stack.aclose()
        raise HTTPException(502, f"Nutrition service unavailable: {exc}") from exc

    if upstream.status_code != 200:
        error_body = await upstream.aread()
        await stack.aclose()
        status_code = 503 if upstream.status_code == 401 else upstream.status_code
        if upstream.status_code == 401:
            content = {"detail": "Upstream service is misconfigured (internal auth rejected). Not a session issue."}
        else:
            try:
                content = json.loads(error_body)
            except ValueError:
                content = {"detail": error_body.decode(errors="replace")}
        return JSONResponse(status_code=status_code, content=content)

    async def event_generator():
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
        finally:
            await stack.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
