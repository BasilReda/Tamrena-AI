"""
Deterministic macro calculator.

Computes daily protein, carbohydrate, and fat targets from the
CaloriesResult using goal-specific ratios. No LLM is involved.
"""

from app.schemas.profile import CaloriesResult, MacroResult
from app.core.constants import (
    MACRO_RATIOS,
    KCAL_PER_G_PROTEIN,
    KCAL_PER_G_CARBS,
    KCAL_PER_G_FAT,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def run_macro_calculator(
    calories_result: CaloriesResult,
    diet_type: str,
    preferences: list[str],
    allergies: list[str],
) -> MacroResult:
    """
    Calculate daily macro targets based on goal ratios.

    Protein is capped at 2.5 g/kg and derived from both the
    ratio approach and the per-kg recommendation; the higher value is used.
    """
    goal = calories_result.goal.lower()
    target_calories = calories_result.target_calories
    weight_kg = calories_result.weight_kg

    ratios = MACRO_RATIOS.get(goal, MACRO_RATIOS["maintenance"])
    protein_per_kg = ratios["protein_g_per_kg"]

    # Protein — take the higher of ratio-based and per-kg recommendation
    protein_from_ratio = (ratios["protein"] * target_calories) / KCAL_PER_G_PROTEIN
    protein_from_per_kg = protein_per_kg * weight_kg
    protein_g = round(max(protein_from_ratio, protein_from_per_kg), 1)

    # Fat
    fat_g = round((ratios["fat"] * target_calories) / KCAL_PER_G_FAT, 1)

    # Carbs — remainder of calories
    protein_kcal = protein_g * KCAL_PER_G_PROTEIN
    fat_kcal = fat_g * KCAL_PER_G_FAT
    carb_kcal = max(target_calories - protein_kcal - fat_kcal, 0)
    carbs_g = round(carb_kcal / KCAL_PER_G_CARBS, 1)

    result = MacroResult(
        target_calories=target_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        goal=goal,
        weight_kg=weight_kg,
        protein_per_kg=protein_per_kg,
        diet_type=diet_type,
        preferences=preferences,
        allergies=allergies,
    )

    logger.info(
        "Macros calculated | Calories=%.1f  Protein=%.1fg  Carbs=%.1fg  Fat=%.1fg",
        target_calories, protein_g, carbs_g, fat_g,
    )
    return result
