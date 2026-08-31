"""
LangGraph Graph State — single TypedDict shared across all nodes.
Each node reads what it needs and writes only its own output fields.
"""

from typing import TypedDict
from app.schemas.profile import (
    NutritionProfile,
    CaloriesResult,
    MacroResult,
    MealDistribution,
    MealPlan,
    TripleMealPlan,
    ValidationReport,
    Explanation,
)
from app.schemas.foods import RetrievedFoods
from app.schemas.request import GenerateNutritionRequest


class NutritionGraphState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────────────
    request: GenerateNutritionRequest
    run_id: str

    # ── Generation mode ───────────────────────────────────────────────────────
    # "dataset"            → Excel food DB retrieval + LLM composes in English
    # "llm_arabic"         → LLM freely generates Egyptian meals in Arabic (no food DB)
    # "llm_arabic_parquet" → parquet food DB retrieval per slot + LLM composes in Arabic
    meal_generation_mode: str

    # ── Node outputs ──────────────────────────────────────────────────────────
    nutrition_profile: NutritionProfile
    calories_result: CaloriesResult
    macro_result: MacroResult
    retrieved_foods: RetrievedFoods
    meal_distribution: MealDistribution
    triple_meal_plan: TripleMealPlan
    meal_plan: MealPlan
    validation_report: ValidationReport
    explanation: Explanation

    # ── Orchestration ─────────────────────────────────────────────────────────
    retry_count: int
    errors: list[str]

