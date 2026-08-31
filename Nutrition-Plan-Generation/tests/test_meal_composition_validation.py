"""Unit tests for meal composition validation heuristics."""

from app.schemas.profile import MealPlan, Meal, MealFoodItem, MacroResult
from app.schemas.foods import FoodItem, RetrievedFoods
from app.validation.validator import validate_meal_plan


def _meal_food(name: str, grams: int = 100):
    factor = grams / 100
    return MealFoodItem(
        name=name,
        serving_grams=grams,
        calories=round(100 * factor, 1),
        protein_g=round(10 * factor, 1),
        carbs_g=round(10 * factor, 1),
        fat_g=round(2 * factor, 1),
    )


def _meal(name: str, foods: list[MealFoodItem]):
    total = len(foods) * 100
    return Meal(
        meal_name=name,
        foods=foods,
        total_calories=total,
        total_protein_g=len(foods) * 10,
        total_carbs_g=len(foods) * 10,
        total_fat_g=len(foods) * 2,
    )


def _macro():
    return MacroResult(
        target_calories=2000,
        protein_g=150,
        carbs_g=200,
        fat_g=70,
        goal="fat_loss",
        weight_kg=80,
        protein_per_kg=2.2,
        diet_type="normal",
        preferences=[],
        allergies=[],
    )


def _retrieved_food(name: str, role: str = "General"):
    return FoodItem(
        food_id=name.lower().replace(" ", "_"),
        name=name,
        calories_per_100g=100,
        protein_per_100g=10,
        carbs_per_100g=10,
        fat_per_100g=2,
        meal_types=["breakfast", "lunch", "dinner"],
        allergens=[],
        diet_types=["normal"],
        meal_role=role,
        meal_slot_fit=["breakfast", "lunch", "dinner"],
        goal_fit_tags=["fat_loss", "maintenance"],
        primary_macro_type="balanced",
        macro_gap_utility_profile="balanced_macro",
        best_with=[],
        diet_profile=["normal"],
        selection_priority=5,
        food_group="general",
    )


def test_validator_flags_ingredient_heaviness():
    meal_plan = MealPlan(
        breakfast=_meal("Breakfast", [_meal_food("Soy Flour")]),
        lunch=_meal("Lunch", [_meal_food("Corn Starch")]),
        dinner=_meal("Dinner", [_meal_food("Soy Flour"), _meal_food("Corn Starch")]),
        snack=None,
        total_daily_calories=400,
        total_daily_protein_g=40,
        total_daily_carbs_g=40,
        total_daily_fat_g=8,
    )
    macro = _macro()
    retrieved = RetrievedFoods(proteins=[_retrieved_food("Soy Flour")])

    report = validate_meal_plan(meal_plan, macro, retrieved)

    assert any(issue.rule == "ingredient_heaviness" for issue in report.issues)


def test_validator_flags_one_role_meals():
    meal_plan = MealPlan(
        breakfast=_meal("Breakfast", [_meal_food("Oats"), _meal_food("Honey")]),
        lunch=_meal("Lunch", [_meal_food("Rice"), _meal_food("Bread")]),
        dinner=_meal("Dinner", [_meal_food("Chicken"), _meal_food("Fish")]),
        snack=None,
        total_daily_calories=600,
        total_daily_protein_g=60,
        total_daily_carbs_g=60,
        total_daily_fat_g=12,
    )
    macro = _macro()
    retrieved = RetrievedFoods(
        carbohydrates=[_retrieved_food("Oats", role="Main Carb"), _retrieved_food("Rice", role="Main Carb")],
        proteins=[_retrieved_food("Chicken", role="Main Protein"), _retrieved_food("Fish", role="Main Protein")],
    )

    report = validate_meal_plan(meal_plan, macro, retrieved)

    assert any(issue.rule == "meal_role_balance" for issue in report.issues)
