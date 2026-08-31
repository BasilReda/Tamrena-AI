"""Unit tests for meal composition candidate prompt context."""

from app.agents.meal_composition.agent import _build_candidate_context
from app.schemas.foods import FoodItem, RetrievedFoods


def _food(
    name: str,
    role: str,
    slots: list[str],
    priority: float,
    macro_type: str = "balanced",
    utility: str = "balanced_macro",
    best_with: list[str] | None = None,
) -> FoodItem:
    return FoodItem(
        food_id=name.lower().replace(" ", "_"),
        name=name,
        calories_per_100g=100,
        protein_per_100g=10,
        carbs_per_100g=10,
        fat_per_100g=2,
        food_group="general",
        meal_types=slots,
        allergens=[],
        diet_types=["normal"],
        meal_role=role,
        meal_slot_fit=slots,
        goal_fit_tags=["fat_loss", "maintenance"],
        primary_macro_type=macro_type,
        macro_gap_utility_profile=utility,
        best_with=best_with or [],
        diet_profile=["normal", "omnivore"],
        selection_priority=priority,
    )


def test_candidate_context_is_grouped_by_meal_slot_and_role():
    foods = RetrievedFoods(
        proteins=[
            _food("Chicken Breast", "Main Protein", ["lunch", "dinner"], 5, "protein", "lean_protein", ["Rice", "Salad"]),
        ],
        carbohydrates=[
            _food("Oats", "Main Carb", ["breakfast", "snack"], 5, "carb", "healthy_carb", ["Yogurt", "Banana"]),
        ],
        fruits=[
            _food("Banana", "Fruit", ["breakfast", "snack"], 4, "carb", "healthy_carb", ["Oats"]),
        ],
    )

    context = _build_candidate_context(foods, "fat_loss", "normal")

    assert "[Breakfast candidates]" in context
    assert "[Lunch candidates]" in context
    assert "[Dinner candidates]" in context
    assert "[Snack candidates]" in context
    assert "[Main Carb]" in context
    assert "[Main Protein]" in context
    assert "macro=protein/lean_protein" in context
    assert "best pairings: Rice, Salad" in context
    assert "priority=5" in context


def test_ingredient_like_foods_are_deprioritized():
    foods = RetrievedFoods(
        proteins=[_food("Soy Flour, Defatted", "Protein Snack", ["snack"], 5, utility="processing_ingredient")],
        carbohydrates=[_food("Oats", "Main Carb", ["breakfast"], 4)],
    )

    breakfast_context = _build_candidate_context(foods, "fat_loss", "normal").split("[Breakfast candidates]", 1)[1]
    assert breakfast_context.index("Oats") < breakfast_context.index("Soy Flour, Defatted")
