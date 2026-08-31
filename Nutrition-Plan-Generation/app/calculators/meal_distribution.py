"""
Deterministic meal distribution calculator.

Splits the daily MacroResult into per-slot calorie + macro budgets using
the MEAL_DISTRIBUTION percentage constants. No LLM is involved.
"""

from app.schemas.profile import MacroResult, MealSlotTarget, MealDistribution
from app.core.constants import MEAL_DISTRIBUTION
from app.core.logging import get_logger

logger = get_logger(__name__)

# Arabic display names for each slot
_SLOT_NAMES: dict[str, str] = {
    "breakfast": "الإفطار",
    "lunch": "الغداء",
    "dinner": "العشاء",
    "snack": "السناك",
}


def run_meal_distribution(macro_result: MacroResult) -> MealDistribution:
    """
    Distribute the daily macro targets across meal slots.

    Each slot receives a proportional share of calories, protein,
    carbs, and fat based on the MEAL_DISTRIBUTION ratios.
    """
    total_cal = macro_result.target_calories
    total_pro = macro_result.protein_g
    total_carb = macro_result.carbs_g
    total_fat = macro_result.fat_g

    def _make_slot(key: str) -> MealSlotTarget:
        ratio = MEAL_DISTRIBUTION[key]
        return MealSlotTarget(
            meal_name=_SLOT_NAMES[key],
            slot_key=key,
            target_calories=round(total_cal * ratio, 1),
            target_protein_g=round(total_pro * ratio, 1),
            target_carbs_g=round(total_carb * ratio, 1),
            target_fat_g=round(total_fat * ratio, 1),
        )

    distribution = MealDistribution(
        breakfast=_make_slot("breakfast"),
        lunch=_make_slot("lunch"),
        dinner=_make_slot("dinner"),
        snack=_make_slot("snack"),
        total_calories=total_cal,
    )

    logger.info(
        "Meal distribution calculated | "
        "Breakfast=%.0f kcal  Lunch=%.0f kcal  Dinner=%.0f kcal  Snack=%.0f kcal",
        distribution.breakfast.target_calories,
        distribution.lunch.target_calories,
        distribution.dinner.target_calories,
        distribution.snack.target_calories,
    )
    return distribution
