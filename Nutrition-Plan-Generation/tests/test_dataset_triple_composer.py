"""Tests for deterministic Dataset Mode triple meal composition."""

from app.agents.meal_composition.dataset_triple_composer import (
    SIMILARITY_THRESHOLD,
    calculate_plan_similarity,
    compose_dataset_triple_meal_plan,
)
from app.schemas.foods import FoodItem, RetrievedFoods
from app.schemas.profile import MacroResult, TripleMealPlan
from app.validation.validator import validate_meal_plan


def _food(
    name: str,
    role: str,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
    priority: float,
    slots: list[str] | None = None,
    best_with: list[str] | None = None,
    group: str = "general",
) -> FoodItem:
    primary = "balanced"
    if role.lower() in {"main protein", "protein", "protein snack", "dairy"}:
        primary = "protein"
    elif role.lower() in {"main carb", "healthy snack", "fruit", "vegetable"}:
        primary = "carbs"
    elif role.lower() == "healthy fat":
        primary = "fat"

    return FoodItem(
        food_id=name.lower().replace(" ", "_"),
        name=name,
        calories_per_100g=calories,
        protein_per_100g=protein,
        carbs_per_100g=carbs,
        fat_per_100g=fat,
        food_group=group,
        meal_types=slots or ["breakfast", "lunch", "dinner", "snack"],
        diet_types=["normal"],
        meal_role=role,
        meal_slot_fit=slots or ["breakfast", "lunch", "dinner", "snack"],
        goal_fit_tags=["fat_loss", "maintenance"],
        primary_macro_type=primary,
        macro_gap_utility_profile=f"{primary}_support",
        best_with=best_with or [],
        diet_profile=["normal"],
        selection_priority=priority,
    )


def _macro() -> MacroResult:
    return MacroResult(
        target_calories=2000,
        protein_g=130,
        carbs_g=230,
        fat_g=60,
        goal="fat_loss",
        weight_kg=80,
        protein_per_kg=1.6,
        diet_type="normal",
        preferences=[],
        allergies=[],
    )


def _retrieved_foods() -> RetrievedFoods:
    return RetrievedFoods(
        proteins=[
            _food("Chicken Breast", "Main Protein", 165, 31, 0, 3.6, 5, ["lunch", "dinner"], ["Brown Rice", "Broccoli"], "protein"),
            _food("Salmon Fillet", "Main Protein", 208, 20, 0, 13, 4, ["lunch", "dinner"], ["Quinoa", "Spinach"], "protein"),
            _food("Turkey Slices", "Main Protein", 135, 29, 1, 2, 3, ["lunch", "dinner"], ["Sweet Potato"], "protein"),
            _food("Egg Whites", "Protein", 52, 11, 0.7, 0.2, 5, ["breakfast", "dinner"], ["Oats"], "protein"),
            _food("Cottage Cheese", "Protein Snack", 98, 11, 3.4, 4.3, 4, ["snack", "breakfast"], ["Blueberries"], "dairy"),
            _food("Greek Yogurt", "Dairy", 73, 10, 3.9, 1.9, 5, ["breakfast", "snack"], ["Apple", "Oats"], "dairy"),
        ],
        carbohydrates=[
            _food("Oats", "Main Carb", 389, 16.9, 66, 6.9, 5, ["breakfast"], ["Greek Yogurt", "Banana"], "grain"),
            _food("Brown Rice", "Main Carb", 123, 2.7, 25.6, 1, 5, ["lunch", "dinner"], ["Chicken Breast"], "grain"),
            _food("Quinoa", "Main Carb", 120, 4.4, 21.3, 1.9, 4, ["lunch", "dinner"], ["Salmon Fillet"], "grain"),
            _food("Sweet Potato", "Main Carb", 86, 1.6, 20.1, 0.1, 3, ["lunch", "dinner"], ["Turkey Slices"], "starch"),
            _food("Whole Wheat Toast", "Main Carb", 247, 13, 41, 4.2, 2, ["breakfast", "snack"], ["Egg Whites"], "grain"),
        ],
        vegetables=[
            _food("Broccoli", "Vegetable", 35, 2.4, 7.2, 0.4, 5, ["lunch", "dinner"], ["Chicken Breast"], "vegetable"),
            _food("Spinach", "Vegetable", 23, 2.9, 3.6, 0.4, 4, ["breakfast", "lunch", "dinner"], ["Salmon Fillet"], "vegetable"),
            _food("Carrots", "Vegetable", 41, 0.9, 10, 0.2, 3, ["lunch", "dinner", "snack"], ["Turkey Slices"], "vegetable"),
            _food("Green Beans", "Vegetable", 31, 1.8, 7, 0.1, 2, ["lunch", "dinner"], ["Quinoa"], "vegetable"),
        ],
        fruits=[
            _food("Banana", "Fruit", 89, 1.1, 22.8, 0.3, 5, ["breakfast", "snack"], ["Oats"], "fruit"),
            _food("Apple", "Fruit", 52, 0.3, 13.8, 0.2, 4, ["breakfast", "snack"], ["Greek Yogurt"], "fruit"),
            _food("Blueberries", "Fruit", 57, 0.7, 14.5, 0.3, 3, ["breakfast", "snack"], ["Cottage Cheese"], "fruit"),
            _food("Orange", "Fruit", 47, 0.9, 11.8, 0.1, 2, ["breakfast", "snack", "lunch"], [], "fruit"),
        ],
        dairy=[
            _food("Skim Milk", "Dairy", 34, 3.4, 5, 0.1, 3, ["breakfast", "snack"], ["Oats"], "dairy"),
            _food("Kefir", "Dairy", 41, 3.8, 4.5, 1, 2, ["breakfast", "snack"], ["Blueberries"], "dairy"),
        ],
        healthy_fats=[
            _food("Almonds", "Healthy Fat", 579, 21, 22, 50, 5, ["breakfast", "snack"], ["Apple"], "fat"),
            _food("Avocado", "Healthy Fat", 160, 2, 8.5, 14.7, 4, ["breakfast", "lunch", "dinner"], ["Whole Wheat Toast"], "fat"),
            _food("Olive Oil", "Healthy Fat", 884, 0, 0, 100, 3, ["lunch", "dinner"], ["Broccoli", "Spinach"], "fat"),
        ],
    )


def _retrieved_foods_with_realism_traps() -> RetrievedFoods:
    foods = _retrieved_foods()
    foods.proteins.append(
        _food("Defatted Soy Flour", "Protein Snack", 330, 52, 30, 1, 10, ["breakfast", "snack"], [], "flour")
    )
    foods.proteins.append(
        _food("Soy Flour", "Protein Snack", 360, 42, 35, 4, 9, ["snack"], [], "flour")
    )
    foods.carbohydrates.append(
        _food("Raw Rice Flour", "Main Carb", 366, 6, 80, 1, 9, ["breakfast", "snack"], [], "flour")
    )
    foods.vegetables.extend([
        _food("Stuffed Grape Leaves", "Vegetable", 150, 4, 22, 5, 9, ["lunch", "dinner"], [], "prepared"),
        _food("Grape Leaves", "Vegetable", 93, 6, 17, 2, 8, ["lunch", "dinner"], [], "vegetable"),
        _food("Fenugreek Leaves", "Vegetable", 49, 4.4, 6, 0.9, 8, ["snack", "lunch"], [], "vegetable"),
    ])
    return foods


def _plan_food_names(plan) -> set[str]:
    meals = [plan.breakfast, plan.lunch, plan.dinner, plan.snack]
    return {item.name for meal in meals if meal for item in meal.foods}


def _all_plan_food_names(triple) -> set[str]:
    names = set()
    for plan in [triple.option_a, triple.option_b, triple.option_c]:
        names.update(_plan_food_names(plan))
    return names


def test_dataset_composer_returns_three_meal_plans():
    triple = compose_dataset_triple_meal_plan(_macro(), _retrieved_foods())

    assert isinstance(triple, TripleMealPlan)
    assert triple.option_a is not None
    assert triple.option_b is not None
    assert triple.option_c is not None
    assert triple.option_a != triple.option_b
    assert triple.option_a != triple.option_c
    assert triple.option_b != triple.option_c


def test_option_a_is_nutritionally_valid_for_existing_validator():
    macro = _macro()
    retrieved = _retrieved_foods()
    triple = compose_dataset_triple_meal_plan(macro, retrieved)

    report = validate_meal_plan(triple.option_a, macro, retrieved)

    assert report.passed is True


def test_dataset_options_are_meaningfully_different():
    retrieved = _retrieved_foods()
    triple = compose_dataset_triple_meal_plan(_macro(), retrieved)

    names_a = _plan_food_names(triple.option_a)
    names_b = _plan_food_names(triple.option_b)
    names_c = _plan_food_names(triple.option_c)

    assert len(names_a - names_b) >= 3
    assert len(names_a - names_c) >= 3
    assert len(names_b - names_c) >= 3


def test_similarity_score_stays_below_threshold():
    retrieved = _retrieved_foods()
    triple = compose_dataset_triple_meal_plan(_macro(), retrieved)

    similarities = [
        calculate_plan_similarity(triple.option_a, triple.option_b, retrieved),
        calculate_plan_similarity(triple.option_a, triple.option_c, retrieved),
        calculate_plan_similarity(triple.option_b, triple.option_c, retrieved),
    ]

    assert max(similarities) <= SIMILARITY_THRESHOLD


def test_ingredient_like_foods_are_avoided_when_edible_alternatives_exist():
    triple = compose_dataset_triple_meal_plan(_macro(), _retrieved_foods_with_realism_traps())

    selected_names = _all_plan_food_names(triple)

    assert "Soy Flour" not in selected_names
    assert "Defatted Soy Flour" not in selected_names
    assert "Raw Rice Flour" not in selected_names


def test_duplicate_food_concepts_do_not_appear_in_same_meal():
    triple = compose_dataset_triple_meal_plan(_macro(), _retrieved_foods_with_realism_traps())

    for plan in [triple.option_a, triple.option_b, triple.option_c]:
        for meal in [plan.breakfast, plan.lunch, plan.dinner, plan.snack]:
            names = {item.name for item in meal.foods}
            assert not {"Stuffed Grape Leaves", "Grape Leaves"}.issubset(names)


def test_duplicate_food_concepts_do_not_repeat_across_same_day():
    triple = compose_dataset_triple_meal_plan(_macro(), _retrieved_foods_with_realism_traps())

    for plan in [triple.option_a, triple.option_b, triple.option_c]:
        names = _plan_food_names(plan)
        assert not {"Stuffed Grape Leaves", "Grape Leaves"}.issubset(names)


def test_snacks_prioritize_realistic_snack_foods():
    triple = compose_dataset_triple_meal_plan(_macro(), _retrieved_foods_with_realism_traps())
    unrealistic_snack_items = {
        "Soy Flour",
        "Defatted Soy Flour",
        "Raw Rice Flour",
        "Fenugreek Leaves",
        "Green Beans",
        "Chicken Breast",
        "Salmon Fillet",
        "Turkey Slices",
        "Brown Rice",
        "Quinoa",
        "Sweet Potato",
    }

    for plan in [triple.option_a, triple.option_b, triple.option_c]:
        snack_names = {item.name for item in plan.snack.foods}
        assert snack_names.isdisjoint(unrealistic_snack_items)


def test_each_option_has_distinct_menu_identity():
    retrieved = _retrieved_foods_with_realism_traps()
    triple = compose_dataset_triple_meal_plan(_macro(), retrieved)

    similarities = [
        calculate_plan_similarity(triple.option_a, triple.option_b, retrieved),
        calculate_plan_similarity(triple.option_a, triple.option_c, retrieved),
        calculate_plan_similarity(triple.option_b, triple.option_c, retrieved),
    ]

    assert max(similarities) <= SIMILARITY_THRESHOLD
    assert len(_plan_food_names(triple.option_a) ^ _plan_food_names(triple.option_b)) >= 8
    assert len(_plan_food_names(triple.option_a) ^ _plan_food_names(triple.option_c)) >= 8
    assert len(_plan_food_names(triple.option_b) ^ _plan_food_names(triple.option_c)) >= 8