"""
Deterministic calorie calculator.

Uses the Mifflin-St Jeor formula to compute BMR, then applies the
TDEE activity multiplier and a goal-based calorie adjustment.
No LLM is involved.
"""

from app.schemas.profile import NutritionProfile, CaloriesResult
from app.core.constants import ACTIVITY_MULTIPLIERS, GOAL_CALORIE_ADJUSTMENTS
from app.core.logging import get_logger

logger = get_logger(__name__)


def calculate_bmr(profile: NutritionProfile) -> float:
    """
    Mifflin-St Jeor BMR formula.

    Male:   10 × weight(kg) + 6.25 × height(cm) − 5 × age + 5
    Female: 10 × weight(kg) + 6.25 × height(cm) − 5 × age − 161
    """
    base = (
        10 * profile.weight_kg
        + 6.25 * profile.height_cm
        - 5 * profile.age
    )
    if profile.gender.lower() == "male":
        return round(base + 5, 2)
    else:
        return round(base - 161, 2)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Apply activity multiplier to BMR to get TDEE."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.55)
    return round(bmr * multiplier, 2)


def calculate_target_calories(tdee: float, goal: str) -> tuple[float, int]:
    """Apply goal-based calorie adjustment to TDEE."""
    adjustment = GOAL_CALORIE_ADJUSTMENTS.get(goal.lower(), 0)
    target = round(tdee + adjustment, 2)
    # Enforce a sensible minimum
    target = max(target, 1200.0)
    return target, adjustment


def run_calories_calculator(profile: NutritionProfile) -> CaloriesResult:
    """
    Entry point for the Calories Calculator node.
    Returns a fully populated CaloriesResult.
    """
    bmr = calculate_bmr(profile)
    tdee = calculate_tdee(bmr, profile.activity_level)
    target_calories, adjustment = calculate_target_calories(tdee, profile.goal)

    result = CaloriesResult(
        bmr=bmr,
        tdee=tdee,
        target_calories=target_calories,
        formula_used="Mifflin-St Jeor",
        goal=profile.goal,
        activity_level=profile.activity_level,
        weight_kg=profile.weight_kg,
        goal_adjustment_kcal=adjustment,
    )

    logger.info(
        "Calories calculated | BMR=%.1f  TDEE=%.1f  Target=%.1f  Goal=%s",
        bmr, tdee, target_calories, profile.goal,
    )
    return result
