"""
LangGraph workflow builder.

Assembles all nodes into a compiled StateGraph with:
  - Sequential edges:
      profile → calories → macros
      → meal_distributor          (llm_arabic + llm_arabic_parquet only, no-op in dataset mode)
      → compose_meals_iterative   (llm_arabic only, no-op otherwise)
      → compose_meals_parquet_arabic (llm_arabic_parquet only, no-op otherwise)
      → retrieve_foods            (dataset only, no-op in llm_arabic/llm_arabic_parquet mode)
      → compose_meal              (dataset only, no-op in other modes)
      → validate → explain
  - Conditional edge after validation (explain | retry_meal)
  - Retry loop: retry_meal → increment_retry → compose_meal/compose_meals_iterative/compose_meals_parquet_arabic
  - Terminal edge: explain → END
"""

# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, END
from app.state.graph_state import NutritionGraphState
from app.graph.nodes import (
    node_profile,
    node_calories,
    node_macros,
    node_meal_distributor,
    node_compose_meals_iterative,
    node_compose_meals_parquet_arabic,
    node_retrieve_foods,
    node_compose_meal,
    node_validate,
    node_increment_retry,
    node_explain,
)
from app.graph.routing import route_after_validation, route_after_retry_increment
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_nutrition_graph():
    """
    Build and compile the nutrition planning LangGraph.
    Returns a compiled graph ready for invocation.
    """
    builder = StateGraph(NutritionGraphState)

    # ── Register nodes ──────────────────────────────────────────────
    builder.add_node("profile", node_profile)
    builder.add_node("calories", node_calories)
    builder.add_node("macros", node_macros)
    builder.add_node("meal_distributor", node_meal_distributor)
    builder.add_node("compose_meals_iterative", node_compose_meals_iterative)
    builder.add_node("compose_meals_parquet_arabic", node_compose_meals_parquet_arabic)
    builder.add_node("retrieve_foods", node_retrieve_foods)
    builder.add_node("compose_meal", node_compose_meal)
    builder.add_node("validate", node_validate)
    builder.add_node("increment_retry", node_increment_retry)
    builder.add_node("explain", node_explain)

    # ── Entry point ───────────────────────────────────────────────────────────
    builder.set_entry_point("profile")

    # ── Sequential edges ───────────────────────────────────────────────
    builder.add_edge("profile", "calories")
    builder.add_edge("calories", "macros")
    # Distributor (mode-guarded: active in llm_arabic + llm_arabic_parquet):
    builder.add_edge("macros", "meal_distributor")
    # Free-form Arabic iterative node (llm_arabic only, no-op otherwise):
    builder.add_edge("meal_distributor", "compose_meals_iterative")
    # Parquet-backed Arabic node (llm_arabic_parquet only, no-op otherwise):
    builder.add_edge("compose_meals_iterative", "compose_meals_parquet_arabic")
    # Legacy dataset nodes (dataset only, no-op otherwise):
    builder.add_edge("compose_meals_parquet_arabic", "retrieve_foods")
    builder.add_edge("retrieve_foods", "compose_meal")
    builder.add_edge("compose_meal", "validate")

    # ── Conditional routing after validation ───────────────────────────────────
    builder.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "explain": "explain",
            "retry_meal": "increment_retry",
        },
    )

    # ── Retry loop ──────────────────────────────────────────────────
    # Mode-aware:
    #   llm_arabic          → compose_meals_iterative
    #   llm_arabic_parquet  → compose_meals_parquet_arabic
    #   dataset             → compose_meal
    builder.add_conditional_edges(
        "increment_retry",
        route_after_retry_increment,
        {
            "compose_meals_iterative": "compose_meals_iterative",
            "compose_meals_parquet_arabic": "compose_meals_parquet_arabic",
            "compose_meal": "compose_meal",
        },
    )

    # ── Terminal edge ─────────────────────────────────────────────────────────
    builder.add_edge("explain", END)

    compiled = builder.compile()
    logger.info("Nutrition graph compiled successfully")
    return compiled


# Module-level singleton — compiled once at startup
nutrition_graph = build_nutrition_graph()
