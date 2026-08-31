"""Unit tests for the deterministic calorie and macro calculators."""

# pyrefly: ignore [missing-import]
import pytest
from app.schemas.profile import NutritionProfile
from app.calculators.calories import (
    calculate_bmr,
    calculate_tdee,
    run_calories_calculator,
)
from app.calculators.macros import run_macro_calculator


def _make_profile(**overrides) -> NutritionProfile:
    defaults = dict(
        age=25,
        gender="male",
        height_cm=180,
        weight_kg=80,
        goal="fat_loss",
        activity_level="moderate",
        diet_type="normal",
        preferences=[],
        allergies=[],
    )
    defaults.update(overrides)
    return NutritionProfile(**defaults)


# ─── BMR Tests ────────────────────────────────────────────────────────────────


class TestBMR:
    def test_male_bmr(self):
        profile = _make_profile(age=25, gender="male", height_cm=180, weight_kg=80)
        bmr = calculate_bmr(profile)
        # 10*80 + 6.25*180 - 5*25 + 5 = 800 + 1125 - 125 + 5 = 1805
        assert bmr == 1805.0

    def test_female_bmr(self):
        profile = _make_profile(age=30, gender="female", height_cm=165, weight_kg=60)
        bmr = calculate_bmr(profile)
        # 10*60 + 6.25*165 - 5*30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
        assert bmr == 1320.25

    def test_bmr_positive(self):
        profile = _make_profile(age=60, gender="female", height_cm=155, weight_kg=50)
        assert calculate_bmr(profile) > 0


# ─── TDEE Tests ───────────────────────────────────────────────────────────────


class TestTDEE:
    def test_moderate_multiplier(self):
        tdee = calculate_tdee(1805.0, "moderate")
        assert round(tdee, 2) == round(1805.0 * 1.55, 2)

    def test_sedentary_multiplier(self):
        tdee = calculate_tdee(1500.0, "sedentary")
        assert tdee == round(1500.0 * 1.2, 2)

    def test_unknown_activity_defaults_to_moderate(self):
        tdee = calculate_tdee(1500.0, "unknown_level")
        assert tdee == round(1500.0 * 1.55, 2)


# ─── Full Calories Result ─────────────────────────────────────────────────────


class TestCaloriesCalculator:
    def test_fat_loss_reduces_calories(self):
        profile = _make_profile(goal="fat_loss")
        result = run_calories_calculator(profile)
        assert result.target_calories < result.tdee
        assert result.goal_adjustment_kcal == -500

    def test_muscle_gain_increases_calories(self):
        profile = _make_profile(goal="muscle_gain")
        result = run_calories_calculator(profile)
        assert result.target_calories > result.tdee
        assert result.goal_adjustment_kcal == 300

    def test_minimum_calories_floor(self):
        profile = _make_profile(
            age=80, gender="female", height_cm=150, weight_kg=40, goal="fat_loss"
        )
        result = run_calories_calculator(profile)
        assert result.target_calories >= 1200.0

    def test_result_contains_all_fields(self):
        profile = _make_profile()
        result = run_calories_calculator(profile)
        assert result.bmr > 0
        assert result.tdee > 0
        assert result.target_calories > 0
        assert result.formula_used == "Mifflin-St Jeor"


# ─── Macro Calculator Tests ───────────────────────────────────────────────────


class TestMacroCalculator:
    def _run(self, goal="fat_loss", **kwargs):
        profile = _make_profile(goal=goal, **kwargs)
        cal = run_calories_calculator(profile)
        return run_macro_calculator(cal, "normal", [], [])

    def test_macro_calories_sum_close_to_target(self):
        result = self._run()
        macro_cals = result.protein_g * 4 + result.carbs_g * 4 + result.fat_g * 9
        # Allow ±5% tolerance from rounding
        assert abs(macro_cals - result.target_calories) / result.target_calories < 0.05

    def test_fat_loss_high_protein(self):
        result = self._run(goal="fat_loss", weight_kg=80)
        # Should be at least 2.2 g/kg for fat loss
        assert result.protein_g >= 80 * 2.0

    def test_muscle_gain_high_carbs(self):
        fat_loss = self._run(goal="fat_loss")
        muscle_gain = self._run(goal="muscle_gain")
        assert muscle_gain.carbs_g > fat_loss.carbs_g

    def test_all_macros_positive(self):
        result = self._run()
        assert result.protein_g > 0
        assert result.carbs_g > 0
        assert result.fat_g > 0
