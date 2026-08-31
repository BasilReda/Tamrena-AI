"""
LangGraph Node Functions

Each function represents one node in the nutrition workflow graph.
Nodes read from NutritionGraphState and return a dict of updated fields.
"""

import asyncio
from app.state.graph_state import NutritionGraphState
from app.agents.profile.agent import run_profile_agent
from app.agents.meal_composition.agent import run_meal_composition_agent
from app.agents.meal_composition.dataset_triple_composer import compose_dataset_triple_meal_plan
from app.agents.meal_composition.agent_arabic import run_meal_composition_agent_arabic
from app.agents.meal_composition.agent_iterative import run_meal_composition_iterative
from app.agents.meal_composition.agent_iterative_parquet import run_meal_composition_iterative_parquet
from app.agents.explanation.agent import run_explanation_agent
from app.calculators.calories import run_calories_calculator
from app.calculators.macros import run_macro_calculator
from app.calculators.meal_distribution import run_meal_distribution
from app.retrieval.repository import FoodRepository, ParquetFoodRepository
from app.schemas.foods import RetrievedFoods
from app.validation.validator import validate_meal_plan
from app.core.logging import get_logger

logger = get_logger(__name__)

from app.services.stream_service import stream_service

# FoodRepository singletons — set once at startup
_food_repo: FoodRepository | None = None
_parquet_repo: ParquetFoodRepository | None = None


def set_food_repository(repo: FoodRepository) -> None:
    """Called once at startup to inject the FoodRepository into the graph layer."""
    global _food_repo, _parquet_repo
    _food_repo = repo
    # Also initialise the parquet repo at the same time so both are ready
    _parquet_repo = ParquetFoodRepository()


# ─── Node: Profile ────────────────────────────────────────────────────────────

async def node_profile(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    if run_id:
        await stream_service.publish_node_start(run_id, "profile")
    logger.info("[node] profile_agent started")
    request = state["request"]
    profile = await run_profile_agent(request)
    if run_id:
        await stream_service.publish_node_complete(run_id, "profile")
    return {"nutrition_profile": profile}


# ─── Node: Calories Calculator ────────────────────────────────────────────────

async def node_calories(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    if run_id:
        await stream_service.publish_node_start(run_id, "calories")
    logger.info("[node] calories_calculator started")
    profile = state["nutrition_profile"]
    result = run_calories_calculator(profile)
    if run_id:
        await stream_service.publish_node_complete(run_id, "calories")
    return {"calories_result": result}


# ─── Node: Macro Calculator ───────────────────────────────────────────────────

async def node_macros(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    if run_id:
        await stream_service.publish_node_start(run_id, "macros")
    logger.info("[node] macro_calculator started")
    calories = state["calories_result"]
    profile = state["nutrition_profile"]
    result = run_macro_calculator(
        calories,
        diet_type=profile.diet_type,
        preferences=profile.preferences,
        allergies=profile.allergies,
    )
    if run_id:
        await stream_service.publish_node_complete(run_id, "macros")
    return {"macro_result": result}


# ─── Node: Food Retrieval ─────────────────────────────────────────────────────

async def node_retrieve_foods(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    mode = state.get("meal_generation_mode", "dataset")

    # ── LLM-Arabic / Parquet-Arabic modes: skip shared dataset retrieval ──────
    # For llm_arabic: no retrieval at all (free-form LLM)
    # For llm_arabic_parquet: retrieval is done per-slot inside node_compose_meals_parquet_arabic
    if mode in ("llm_arabic", "llm_arabic_parquet"):
        logger.info("[node] food_retrieval SKIPPED (mode=%s)", mode)
        if run_id:
            await stream_service.publish_node_start(run_id, "retrieve_foods")
            await stream_service.publish_node_complete(run_id, "retrieve_foods")
        return {
            "retrieved_foods": RetrievedFoods()
        }

    # ── Dataset mode: normal Excel-based retrieval ────────────────────────────
    if run_id:
        await stream_service.publish_node_start(run_id, "retrieve_foods")
    logger.info("[node] food_retrieval started")
    if _food_repo is None:
        raise RuntimeError("FoodRepository not initialised. Call set_food_repository() first.")
    macro_result = state["macro_result"]
    foods = _food_repo.get_candidate_foods(macro_result)
    if run_id:
        await stream_service.publish_node_complete(run_id, "retrieve_foods")
    return {"retrieved_foods": foods}


# ─── Node: Meal Composition ───────────────────────────────────────────────────

async def node_compose_meal(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    mode = state.get("meal_generation_mode", "dataset")

    # In llm_arabic mode the iterative node handles meal composition
    if mode == "llm_arabic":
        logger.info("[node] compose_meal SKIPPED (llm_arabic mode uses iterative agent)")
        if run_id:
            await stream_service.publish_node_start(run_id, "compose_meal")
            await stream_service.publish_node_complete(run_id, "compose_meal")
        return {}

    if run_id:
        await stream_service.publish_node_start(run_id, "compose_meal")
    retry_count = state.get("retry_count", 0)
    macro_result = state["macro_result"]

    # On retries, pass the previous plan + validation report so agents can
    # make targeted corrections instead of regenerating from scratch.
    previous_meal_plan = state.get("meal_plan") if retry_count > 0 else None
    previous_validation = state.get("validation_report") if retry_count > 0 else None

    if mode == "llm_arabic":
        # ── LLM-Arabic mode: no dataset, LLM invents Egyptian meals in Arabic ─
        logger.info(
            "[node] meal_composition_agent_arabic started (retry=%d, correction=%s)",
            retry_count,
            previous_meal_plan is not None,
        )
        meal_plan = await run_meal_composition_agent_arabic(
            macro_result,
            retry_count,
            previous_meal_plan=previous_meal_plan,
            previous_validation=previous_validation,
        )
    else:
        # ── Dataset mode: original pipeline ──────────────────────────────────
        logger.info(
            "[node] dataset_triple_composer started (retry=%d, correction=%s)",
            retry_count,
            previous_meal_plan is not None,
        )
        retrieved_foods = state["retrieved_foods"]
        triple_meal_plan = compose_dataset_triple_meal_plan(macro_result, retrieved_foods)
        meal_plan = triple_meal_plan.option_a

    if run_id:
        await stream_service.publish_node_complete(run_id, "compose_meal")
    updates = {"meal_plan": meal_plan}
    if mode == "dataset":
        updates["triple_meal_plan"] = triple_meal_plan
    return updates



# ─── Node: Validation ─────────────────────────────────────────────────────────

async def node_validate(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    if run_id:
        await stream_service.publish_node_start(run_id, "validate")
    logger.info("[node] validation_engine started")
    meal_plan = state["meal_plan"]
    macro_result = state["macro_result"]
    report = validate_meal_plan(meal_plan, macro_result, state.get("retrieved_foods"))
    if run_id:
        await stream_service.publish_node_complete(run_id, "validate")
    return {"validation_report": report}


# ─── Node: Retry Increment ────────────────────────────────────────────────────

async def node_increment_retry(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    if run_id:
        await stream_service.publish_node_start(run_id, "increment_retry")
    """Increments retry counter before looping back to meal composition."""
    current = state.get("retry_count", 0)
    logger.info("[node] retry_counter → %d", current + 1)
    if run_id:
        await stream_service.publish_node_complete(run_id, "increment_retry")
    return {"retry_count": current + 1}


# ─── Node: Explanation ────────────────────────────────────────────────────────

async def node_explain(state: NutritionGraphState) -> dict:
    run_id = state.get("run_id", "")
    if run_id:
        await stream_service.publish_node_start(run_id, "explain")
    logger.info("[node] explanation_agent started")
    meal_plan = state["meal_plan"]
    macro_result = state["macro_result"]
    validation_report = state["validation_report"]
    explanation = await run_explanation_agent(meal_plan, macro_result, validation_report)
    if run_id:
        await stream_service.publish_node_complete(run_id, "explain")
    return {"explanation": explanation}


# ─── Node: Meal Distributor ──────────────────────────────────────────────

async def node_meal_distributor(state: NutritionGraphState) -> dict:
    """
    Splits the daily macro targets into per-slot budgets.
    Pure Python, no LLM.
    Active in: llm_arabic | llm_arabic_parquet modes.
    """
    run_id = state.get("run_id", "")
    mode = state.get("meal_generation_mode", "dataset")

    if mode not in ("llm_arabic", "llm_arabic_parquet"):
        logger.info("[node] meal_distributor SKIPPED (mode=%s)", mode)
        return {}

    if run_id:
        await stream_service.publish_node_start(run_id, "meal_distributor")
    logger.info("[node] meal_distributor started")
    macro_result = state["macro_result"]
    distribution = run_meal_distribution(macro_result)
    if run_id:
        await stream_service.publish_node_complete(run_id, "meal_distributor")
    return {"meal_distribution": distribution}


# ─── Node: Iterative Meal Composition (3 options, per-slot parallel) ───────────

async def node_compose_meals_iterative(state: NutritionGraphState) -> dict:
    """
    Generates 3 independent meal plan options via per-slot parallelism.
    Only active in llm_arabic mode (free-form Arabic, no dataset).
    Stores the TripleMealPlan and also sets meal_plan = option_a so the
    existing validation node works unchanged.
    """
    run_id = state.get("run_id", "")
    mode = state.get("meal_generation_mode", "dataset")

    if mode != "llm_arabic":
        logger.info("[node] compose_meals_iterative SKIPPED (mode=%s)", mode)
        return {}

    if run_id:
        await stream_service.publish_node_start(run_id, "compose_meals_iterative")
    logger.info("[node] compose_meals_iterative started")

    macro_result = state["macro_result"]
    meal_distribution = state["meal_distribution"]

    triple = await run_meal_composition_iterative(macro_result, meal_distribution)

    if run_id:
        await stream_service.publish_node_complete(run_id, "compose_meals_iterative")

    # Expose option_a as meal_plan so the validator / retry loop remain unchanged
    return {
        "triple_meal_plan": triple,
        "meal_plan": triple.option_a,
    }


# ─── Node: Parquet-Backed Arabic Iterative Meal Composition ─────────────────

async def node_compose_meals_parquet_arabic(state: NutritionGraphState) -> dict:
    """
    Generates 3 independent meal plan options grounded in real foods from
    the foods_master_final.parquet dataset.

    Only active in llm_arabic_parquet mode.

    Pipeline:
      1. For each meal slot: retrieve top-N foods from the parquet via
         ParquetFoodRepository (multi-column filtering + ranking).
      2. Fire 3 LLM calls in parallel per slot, passing the real food catalog
         in Arabic so the LLM composes meals from actual Egyptian foods.
      3. Assembles a TripleMealPlan and exposes option_a as meal_plan for
         the shared validation node.
    """
    run_id = state.get("run_id", "")
    mode = state.get("meal_generation_mode", "dataset")

    if mode != "llm_arabic_parquet":
        logger.info("[node] compose_meals_parquet_arabic SKIPPED (mode=%s)", mode)
        return {}

    if run_id:
        await stream_service.publish_node_start(run_id, "compose_meals_parquet_arabic")
    logger.info("[node] compose_meals_parquet_arabic started")

    if _parquet_repo is None:
        raise RuntimeError(
            "ParquetFoodRepository not initialised. "
            "Call set_food_repository() first."
        )

    macro_result = state["macro_result"]
    meal_distribution = state["meal_distribution"]

    # ── Step 1: retrieve per-slot foods from the parquet ─────────────────────
    logger.info("[node] compose_meals_parquet_arabic — retrieving per-slot foods from parquet")
    parquet_foods = _parquet_repo.get_all_slots(macro_result)
    logger.info(
        "Parquet retrieval complete | "
        "breakfast=%d  lunch=%d  dinner=%d  snack=%d foods",
        len(parquet_foods.breakfast),
        len(parquet_foods.lunch),
        len(parquet_foods.dinner),
        len(parquet_foods.snack),
    )

    # ── Step 2: LLM generates 3 options from the real food catalog ─────────
    triple = await run_meal_composition_iterative_parquet(
        macro_result, meal_distribution, parquet_foods
    )

    if run_id:
        await stream_service.publish_node_complete(run_id, "compose_meals_parquet_arabic")

    # Expose option_a as meal_plan for the shared validation / explanation nodes
    return {
        "triple_meal_plan": triple,
        "meal_plan": triple.option_a,
    }
