"""
Nutrition API Routes

POST   /api/v1/nutrition/generate         → start generation, return run_id
GET    /api/v1/nutrition/stream/{run_id}  → SSE stream of agent events
GET    /api/v1/nutrition/result/{run_id}  → retrieve final meal plan
GET    /api/v1/nutrition/history          → list all past plans
DELETE /api/v1/nutrition/{run_id}         → remove a result
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException

# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse

from app.api.dependencies import require_internal_auth
from app.schemas.request import GenerateNutritionRequest
from app.schemas.response import StartResponse, NutritionPlanResponse, APIResponse
from app.services import nutrition_service
from app.services.stream_service import stream_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/nutrition", tags=["Nutrition"], dependencies=[Depends(require_internal_auth)])


@router.post(
    "/generate",
    response_model=StartResponse,
    status_code=202,
    summary="Start nutrition plan generation",
    description=(
        "Accepts a user profile and kicks off the multi-agent nutrition planning workflow. "
        "Returns a `run_id` immediately. Connect to the `/stream/{run_id}` endpoint to "
        "receive real-time agent progress events."
    ),
)
async def generate_nutrition(request: GenerateNutritionRequest) -> StartResponse:
    run_id = await nutrition_service.start_nutrition_generation(request)
    logger.info("POST /generate → run_id=%s", run_id)
    return StartResponse(run_id=run_id)


@router.get(
    "/stream/{run_id}",
    summary="Stream agent execution events (SSE)",
    description=(
        "Opens a Server-Sent Events connection. Streams one event per agent node "
        "as the workflow executes. Terminates with a `completed` event when the "
        "full meal plan is ready."
    ),
)
async def stream_events(run_id: str) -> StreamingResponse:
    """
    stream_service.stream_events() already yields fully SSE-formatted text
    ("data: {...}\n\n" per event, see StreamService.stream_events) — it is
    not a sequence of raw payloads for a library to format itself.
    EventSourceResponse formats whatever it's given as its OWN "data: "
    message per yielded chunk, so wrapping this generator in it produced a
    doubled "data: data: {...}" line that no SSE client (including the
    browser's native EventSource, which strips exactly one "data: " prefix
    per spec) can parse as JSON — every event silently failed client-side
    JSON.parse and the browser's EventSource treated the resulting garbled
    stream as a connection error. StreamingResponse passes bytes straight
    through with no reformatting, which is what this generator's output
    actually needs (same pattern as the tamreena-web BFF's own proxy of
    this exact endpoint).
    """
    logger.info("GET /stream/%s → opening SSE", run_id)

    async def generator():
        async for chunk in stream_service.stream_events(run_id):
            yield chunk

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get(
    "/result/{run_id}",
    response_model=NutritionPlanResponse,
    summary="Retrieve the final nutrition plan",
    description="Fetch the completed meal plan, validation report, and AI explanation for a given run_id.",
)
async def get_result_by_path(run_id: str) -> NutritionPlanResponse:
    return _get_result_or_404(run_id)


@router.get(
    "/history",
    response_model=APIResponse,
    summary="List all past nutrition plans",
)
async def get_history() -> APIResponse:
    results = nutrition_service.list_results()
    return APIResponse(
        success=True,
        data=[r.model_dump() for r in results],
        message=f"{len(results)} plans found",
    )


def _get_result_or_404(run_id: str) -> NutritionPlanResponse:
    result = nutrition_service.get_result(run_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No result found for run_id={run_id}. The run may still be in progress.",
        )
    return result


# Generic single-segment path — must stay registered after every other
# literal single-segment route above (currently just /history) or it
# shadows them: FastAPI/Starlette matches routes in registration order,
# and {run_id} matches any single path segment including "history".
# This shadowed /history entirely until this fix (it always 404'd as an
# unknown run_id instead of ever running list_results()).
@router.get(
    "/{run_id}",
    response_model=NutritionPlanResponse,
    summary="Retrieve the final nutrition plan (alias)",
)
async def get_result(run_id: str) -> NutritionPlanResponse:
    return _get_result_or_404(run_id)


@router.delete(
    "/{run_id}",
    response_model=APIResponse,
    summary="Delete a nutrition plan result",
)
async def delete_result(run_id: str) -> APIResponse:
    result = nutrition_service.get_result(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"run_id={run_id} not found")
    # Remove from in-memory store
    nutrition_service._results.pop(run_id, None)
    return APIResponse(success=True, message=f"run_id={run_id} deleted")
