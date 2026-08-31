"""
Deterministic Nutrition Validation Engine.
Verifies the generated meal plan against calorie and macro targets.
No LLM is involved.
"""

from collections import Counter
import re

from app.schemas.profile import MealPlan, MacroResult, ValidationReport, ValidationIssue, Meal
from app.schemas.foods import RetrievedFoods, FoodItem
from app.core.constants import (
    CALORIE_TOLERANCE_PCT,
    PROTEIN_TOLERANCE_PCT,
    CARBS_TOLERANCE_PCT,
    FAT_TOLERANCE_PCT,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def _pct_deviation(actual: float, target: float) -> float:
    """Return signed percentage deviation from target."""
    if target == 0:
        return 0.0
    return (actual - target) / target


def _check_macro(
    issues: list[ValidationIssue],
    label: str,
    actual: float,
    target: float,
    tolerance: float,
) -> float:
    deviation = _pct_deviation(actual, target)
    if abs(deviation) > tolerance:
        issues.append(ValidationIssue(
            rule=f"{label}_tolerance",
            expected=f"{target:.1f}g ±{tolerance*100:.0f}%",
            actual=f"{actual:.1f}g (deviation {deviation*100:+.1f}%)",
            severity="error",
        ))
    return deviation


def _norm_name(value: str) -> str:
    return " ".join(value.lower().replace("،", ",").split())


def _meal_slot_key(meal: Meal) -> str:
    name = meal.meal_name.lower()
    if "breakfast" in name or "إفطار" in name or "افطار" in name:
        return "breakfast"
    if "lunch" in name or "غداء" in name:
        return "lunch"
    if "dinner" in name or "عشاء" in name:
        return "dinner"
    if "snack" in name or "سناك" in name:
        return "snack"
    return name


def _candidate_index(retrieved_foods: RetrievedFoods | None) -> dict[str, FoodItem]:
    if retrieved_foods is None:
        return {}
    return {_norm_name(food.name): food for food in retrieved_foods.all_foods}


def _validate_food_metadata(
    issues: list[ValidationIssue],
    meal_plan: MealPlan,
    macro_result: MacroResult,
    retrieved_foods: RetrievedFoods | None,
) -> None:
    candidates = _candidate_index(retrieved_foods)
    if not candidates:
        return

    meals = [meal_plan.breakfast, meal_plan.lunch, meal_plan.dinner]
    if meal_plan.snack:
        meals.append(meal_plan.snack)

    all_names: list[str] = []
    meal_role_sets: list[set[str]] = []
    ingredient_like_total = 0
    diet_type = macro_result.diet_type.lower()
    goal = macro_result.goal.lower()
    ingredient_keywords = {
        "flour",
        "starch",
        "extract",
        "powder",
        "bran",
        "germ",
        "baking",
        "seasoning",
        "flavoring",
    }

    for meal in meals:
        slot = _meal_slot_key(meal)
        roles: set[str] = set()
        for item in meal.foods:
            all_names.append(_norm_name(item.name))
            food = candidates.get(_norm_name(item.name))
            if food is None:
                issues.append(ValidationIssue(
                    rule="food_dataset_membership",
                    expected="all foods must come from retrieved dataset candidates",
                    actual=f"{item.name} was not in candidate foods",
                    severity="error",
                ))
                continue

            roles.add(food.meal_role.lower())
            if any(keyword in food.name.lower() for keyword in ingredient_keywords):
                ingredient_like_total += 1
            if food.meal_slot_fit and slot not in food.meal_slot_fit:
                issues.append(ValidationIssue(
                    rule="meal_slot_suitability",
                    expected=f"{item.name} should fit {slot}",
                    actual=f"meal_slot_fit={food.meal_slot_fit}",
                    severity="warning",
                ))
            if diet_type not in {"normal", "omnivore"} and diet_type not in food.diet_types and diet_type not in food.diet_profile:
                issues.append(ValidationIssue(
                    rule="diet_compatibility",
                    expected=f"food compatible with {diet_type}",
                    actual=f"{item.name} diet_profile={food.diet_profile}",
                    severity="error",
                ))
            if food.goal_fit_tags and goal not in food.goal_fit_tags and "maintenance" not in food.goal_fit_tags:
                issues.append(ValidationIssue(
                    rule="goal_compatibility",
                    expected=f"food tagged for {goal} or maintenance",
                    actual=f"{item.name} goal_fit_tags={food.goal_fit_tags}",
                    severity="warning",
                ))
        meal_role_sets.append(roles)

    duplicates = [name for name, count in Counter(all_names).items() if count > 1]
    if duplicates:
        issues.append(ValidationIssue(
            rule="duplicate_foods",
            expected="avoid duplicate foods across the day",
            actual=", ".join(sorted(duplicates)),
            severity="warning",
        ))

    unique_foods = set(all_names)
    if len(unique_foods) < min(5, len(all_names)):
        issues.append(ValidationIssue(
            rule="food_diversity",
            expected="at least five distinct foods when enough items are used",
            actual=f"{len(unique_foods)} distinct foods",
            severity="warning",
        ))

    if all_names and ingredient_like_total / len(all_names) >= 0.25:
        issues.append(ValidationIssue(
            rule="ingredient_heaviness",
            expected="ingredient-like foods should be a minority of the meal plan",
            actual=f"{ingredient_like_total} of {len(all_names)} foods appear ingredient-like",
            severity="warning",
        ))

    if len(unique_foods) >= 3 and ingredient_like_total >= 2 and len(unique_foods) - ingredient_like_total < 2:
        issues.append(ValidationIssue(
            rule="meal_composition_realism",
            expected="meals should be built from distinct meal foods, not mostly ingredients",
            actual="composition leans too heavily toward ingredient-like items",
            severity="warning",
        ))

    for meal, roles in zip(meals, meal_role_sets):
        if len(meal.foods) >= 3 and len(roles) < 2:
            issues.append(ValidationIssue(
                rule="meal_realism",
                expected="multi-item meals should combine complementary meal roles",
                actual=f"{meal.meal_name} roles={sorted(roles)}",
                severity="warning",
            ))

    if len({tuple(sorted(roles)) for roles in meal_role_sets}) < min(2, len(meal_role_sets)):
        issues.append(ValidationIssue(
            rule="meal_diversity",
            expected="meals should not all use the same role pattern",
            actual="repeated meal role pattern",
            severity="warning",
        ))

    if any(len(roles) == 1 for roles in meal_role_sets if roles):
        issues.append(ValidationIssue(
            rule="meal_role_balance",
            expected="multi-item meals should combine more than one meal role",
            actual="one-role meal composition detected",
            severity="warning",
        ))


def validate_meal_plan(
    meal_plan: MealPlan,
    macro_result: MacroResult,
    retrieved_foods: RetrievedFoods | None = None,
) -> ValidationReport:
    """
    Run all validation rules against the generated meal plan.
    Returns a ValidationReport with PASS/FAIL and detailed issues.
    """
    issues: list[ValidationIssue] = []

    # ── Calorie check ─────────────────────────────────────────────────────────
    cal_dev = _pct_deviation(meal_plan.total_daily_calories, macro_result.target_calories)
    if abs(cal_dev) > CALORIE_TOLERANCE_PCT:
        issues.append(ValidationIssue(
            rule="calorie_tolerance",
            expected=f"{macro_result.target_calories:.1f} kcal ±{CALORIE_TOLERANCE_PCT*100:.0f}%",
            actual=f"{meal_plan.total_daily_calories:.1f} kcal (deviation {cal_dev*100:+.1f}%)",
            severity="error",
        ))

    # ── Macro checks ──────────────────────────────────────────────────────────
    prot_dev = _check_macro(
        issues, "protein",
        meal_plan.total_daily_protein_g, macro_result.protein_g, PROTEIN_TOLERANCE_PCT,
    )
    carb_dev = _check_macro(
        issues, "carbohydrates",
        meal_plan.total_daily_carbs_g, macro_result.carbs_g, CARBS_TOLERANCE_PCT,
    )
    fat_dev = _check_macro(
        issues, "fat",
        meal_plan.total_daily_fat_g, macro_result.fat_g, FAT_TOLERANCE_PCT,
    )

    # ── Meal completeness ─────────────────────────────────────────────────────
    for meal in [meal_plan.breakfast, meal_plan.lunch, meal_plan.dinner]:
        if not meal.foods:
            issues.append(ValidationIssue(
                rule="meal_completeness",
                expected=f"{meal.meal_name} must contain at least one food",
                actual="empty",
                severity="error",
            ))

    _validate_food_metadata(issues, meal_plan, macro_result, retrieved_foods)

    passed = not any(i.severity == "error" for i in issues)

    report = ValidationReport(
        passed=passed,
        issues=issues,
        calorie_deviation_pct=round(cal_dev * 100, 2),
        protein_deviation_pct=round(prot_dev * 100, 2),
        carbs_deviation_pct=round(carb_dev * 100, 2),
        fat_deviation_pct=round(fat_dev * 100, 2),
    )

    logger.info(
        "Validation %s | %d issues | cal_dev=%.1f%%  prot_dev=%.1f%%",
        "PASSED" if passed else "FAILED",
        len(issues),
        cal_dev * 100,
        prot_dev * 100,
    )
    return report
