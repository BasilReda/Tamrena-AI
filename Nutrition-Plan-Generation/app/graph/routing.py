"""
Conditional routing logic for the LangGraph nutrition workflow.
"""

from app.state.graph_state import NutritionGraphState
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def route_after_validation(state: NutritionGraphState) -> str:
    """
    Called by LangGraph after the validation node.

    Returns:
        "explain"      — validation passed, continue to explanation
        "retry_meal"   — validation failed and retries remain
        "explain"      — validation failed but max retries exhausted (best effort)
    """
    report = state.get("validation_report")
    retry_count = state.get("retry_count", 0)

    if report is None:
        logger.error("route_after_validation: no validation report found!")
        return "explain"

    if report.passed:
        logger.info("Routing → explain (validation PASSED)")
        return "explain"

    if retry_count < settings.max_retries:
        logger.info(
            "Routing → retry_meal (validation FAILED, retry %d/%d)",
            retry_count + 1,
            settings.max_retries,
        )
        return "retry_meal"

    # Max retries exhausted — proceed with best-effort plan
    logger.warning(
        "Routing → explain (max retries %d exhausted, proceeding with best effort)",
        settings.max_retries,
    )
    return "explain"


def route_after_retry_increment(state: NutritionGraphState) -> str:
    """
    Called by LangGraph after the increment_retry node.

    Routes to the appropriate meal composition node based on mode:
      - llm_arabic         → compose_meals_iterative          (re-generates all 3 free-form options)
      - llm_arabic_parquet → compose_meals_parquet_arabic     (re-generates from parquet catalog)
      - dataset            → compose_meal                     (original single-plan dataset agent)
    """
    mode = state.get("meal_generation_mode", "dataset")
    if mode == "llm_arabic":
        logger.info("Retry routing → compose_meals_iterative (llm_arabic mode)")
        return "compose_meals_iterative"
    if mode == "llm_arabic_parquet":
        logger.info("Retry routing → compose_meals_parquet_arabic (llm_arabic_parquet mode)")
        return "compose_meals_parquet_arabic"
    logger.info("Retry routing → compose_meal (dataset mode)")
    return "compose_meal"

