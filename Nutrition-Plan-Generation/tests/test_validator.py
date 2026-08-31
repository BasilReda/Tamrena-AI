"""Unit tests for the deterministic validation engine."""

# pyrefly: ignore [missing-import]
import pytest

# pyrefly: ignore [missing-import]
from app.schemas.profile import (
    MealPlan,
    Meal,
    MealFoodItem,
    MacroResult,
    ValidationReport,
)
from app.validation.validator import validate_meal_plan


def _make_food(
    name="Chicken Breast", calories=165, protein=31, carbs=0, fat=3.6, grams=100
):
    factor = grams / 100
    return MealFoodItem(
        name=name,
        serving_grams=grams,
        calories=round(calories * factor, 1),
        protein_g=round(protein * factor, 1),
        carbs_g=round(carbs * factor, 1),
        fat_g=round(fat * factor, 1),
    )


def _make_meal(name, foods, calories, protein, carbs, fat):
    return Meal(
        meal_name=name,
        foods=foods,
        total_calories=calories,
        total_protein_g=protein,
        total_carbs_g=carbs,
        total_fat_g=fat,
    )


def _make_plan(total_cal=2000, protein=150, carbs=200, fat=70):
    """Build a minimal but structurally valid MealPlan."""
    cal_b, cal_l, cal_d = total_cal * 0.25, total_cal * 0.35, total_cal * 0.30
    prot_b, prot_l, prot_d = protein * 0.25, protein * 0.35, protein * 0.30
    carb_b, carb_l, carb_d = carbs * 0.25, carbs * 0.35, carbs * 0.30
    fat_b, fat_l, fat_d = fat * 0.25, fat * 0.35, fat * 0.30

    chicken = _make_food()

    return MealPlan(
        breakfast=_make_meal("Breakfast", [chicken], cal_b, prot_b, carb_b, fat_b),
        lunch=_make_meal("Lunch", [chicken], cal_l, prot_l, carb_l, fat_l),
        dinner=_make_meal("Dinner", [chicken], cal_d, prot_d, carb_d, fat_d),
        snack=None,
        total_daily_calories=total_cal,
        total_daily_protein_g=protein,
        total_daily_carbs_g=carbs,
        total_daily_fat_g=fat,
    )


def _make_macro(target_cal=2000, protein=150, carbs=200, fat=70):
    return MacroResult(
        target_calories=target_cal,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
        goal="fat_loss",
        weight_kg=80,
        protein_per_kg=2.2,
        diet_type="normal",
        preferences=[],
        allergies=[],
    )


class TestValidationEngine:
    def test_passes_on_target(self):
        plan = _make_plan(2000, 150, 200, 70)
        macro = _make_macro(2000, 150, 200, 70)
        report = validate_meal_plan(plan, macro)
        assert report.passed is True
        assert len([i for i in report.issues if i.severity == "error"]) == 0

    def test_fails_calorie_excess(self):
        plan = _make_plan(total_cal=2500)  # 25% over 2000 kcal target
        macro = _make_macro(2000)
        report = validate_meal_plan(plan, macro)
        assert report.passed is False
        assert any(i.rule == "calorie_tolerance" for i in report.issues)

    def test_fails_calorie_deficit(self):
        plan = _make_plan(total_cal=1500)  # 25% under 2000 kcal target
        macro = _make_macro(2000)
        report = validate_meal_plan(plan, macro)
        assert report.passed is False

    def test_fails_protein_too_low(self):
        plan = _make_plan(protein=50)  # way below 150g target
        macro = _make_macro(protein=150)
        report = validate_meal_plan(plan, macro)
        assert report.passed is False
        assert any(i.rule == "protein_tolerance" for i in report.issues)

    def test_deviation_pct_reported(self):
        plan = _make_plan(total_cal=2200)
        macro = _make_macro(2000)
        report = validate_meal_plan(plan, macro)
        assert abs(report.calorie_deviation_pct - 10.0) < 1.0

    def test_empty_meal_fails(self):
        plan = _make_plan()
        plan.breakfast.foods = []  # empty breakfast
        plan.breakfast.total_calories = 0
        macro = _make_macro()
        report = validate_meal_plan(plan, macro)
        assert any(i.rule == "meal_completeness" for i in report.issues)
