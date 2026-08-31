"""
Nutrition Service — orchestrates a full nutrition generation run.

Responsibilities:
- Accept GenerateNutritionRequest
- Assign a unique run_id
- Execute the LangGraph workflow asynchronously
- Publish streaming events through StreamService
- Store the final result for later retrieval
"""

import asyncio
import uuid
from app.schemas.request import GenerateNutritionRequest
from app.schemas.response import NutritionPlanResponse
from app.graph.builder import nutrition_graph
from app.services.stream_service import stream_service
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory result store (MVP — replace with DB in future)
_results: dict[str, NutritionPlanResponse] = {}


def generate_run_id() -> str:
    return str(uuid.uuid4())


async def _run_graph_with_streaming(
    run_id: str,
    request: GenerateNutritionRequest,
) -> None:
    """
    Execute the LangGraph workflow via ainvoke (not astream).

    Nodes publish their own SSE progress events directly through stream_service,
    so graph-level streaming is not needed here.  Using ainvoke instead of astream
    avoids the GeneratorExit that LangGraph raises when the SSE client disconnects
    before the graph finishes.

    Runs as a background asyncio task — client disconnection does not cancel it.
    """
    logger.info("Starting graph run | run_id=%s", run_id)
    initial_state = {
        "request": request,
        "run_id": run_id,
        "retry_count": 0,
        "errors": [],
        "meal_generation_mode": request.meal_generation_mode.value,
    }

    try:
        final_state: dict = await nutrition_graph.ainvoke(initial_state)

        result = NutritionPlanResponse(
            run_id=run_id,
            success=True,
            macro_result=final_state.get("macro_result"),
            calories_result=final_state.get("calories_result"),
            meal_plan=final_state.get("meal_plan"),
            triple_meal_plan=final_state.get("triple_meal_plan"),
            validation_report=final_state.get("validation_report"),
            explanation=final_state.get("explanation"),
            retry_count=final_state.get("retry_count", 0),
        )

    except Exception as exc:
        logger.exception("Graph run failed | run_id=%s | error=%s", run_id, exc)
        await stream_service.publish_node_error(run_id, "workflow", str(exc))
        result = NutritionPlanResponse(
            run_id=run_id,
            success=False,
            error=str(exc),
        )

    _results[run_id] = result
    await stream_service.publish_finished(run_id)
    logger.info("Graph run completed | run_id=%s | success=%s", run_id, result.success)


async def start_nutrition_generation(
    request: GenerateNutritionRequest,
) -> str:
    """
    Kick off the nutrition generation workflow as a background asyncio task.
    Returns the run_id immediately so the client can connect to the SSE stream.
    """
    run_id = generate_run_id()
    stream_service.create_run(run_id)
    asyncio.create_task(
        _run_graph_with_streaming(run_id, request),
        name=f"nutrition_run_{run_id}",
    )
    logger.info("Nutrition generation started | run_id=%s", run_id)
    return run_id


def get_result(run_id: str) -> NutritionPlanResponse | None:
    """Retrieve the final result for a completed run."""
    return _results.get(run_id)


def list_results() -> list[NutritionPlanResponse]:
    """Return all completed results (history endpoint)."""
    return list(_results.values())
