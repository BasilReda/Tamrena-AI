from app.agents.meal_composition.allergen_check import find_allergen_matches
from app.schemas.profile import MealPlan, Meal, MealFoodItem


def _plan_with_food(name: str) -> MealPlan:
    food = MealFoodItem(name=name, serving_grams=100, calories=200, protein_g=10, carbs_g=20, fat_g=5)
    meal = Meal(meal_name="Breakfast", foods=[food], total_calories=200, total_protein_g=10, total_carbs_g=20, total_fat_g=5)
    return MealPlan(
        breakfast=meal, lunch=meal, dinner=meal, snack=None,
        total_daily_calories=600, total_daily_protein_g=30, total_daily_carbs_g=60, total_daily_fat_g=15,
    )


def test_finds_case_insensitive_substring_match():
    plan = _plan_with_food("Grilled Peanut Chicken")
    assert find_allergen_matches(plan, ["peanuts"]) == []  # "peanuts" (plural) isn't a substring of "Peanut" — see Step 3 note
    assert find_allergen_matches(plan, ["peanut"]) == ["peanut"]


def test_no_match_returns_empty_list():
    plan = _plan_with_food("Grilled Chicken Breast")
    assert find_allergen_matches(plan, ["peanut", "shellfish"]) == []


def test_empty_allergy_list_returns_empty_list():
    plan = _plan_with_food("Grilled Peanut Chicken")
    assert find_allergen_matches(plan, []) == []
