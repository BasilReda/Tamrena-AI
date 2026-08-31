"""
Best-effort allergen safety net for the llm_arabic generation mode, which
has no candidate food list to filter (unlike dataset/llm_arabic_parquet —
see app/retrieval/filters.py for that code-level guard). This is a plain
case-insensitive substring match between each user-supplied allergy term
and each generated food's name. It is NOT translation-aware: an allergy
typed in English won't match a food name generated in Arabic, and vice
versa. It catches the case where the LLM ignores the instruction to avoid
an allergen but still names it plainly — it is a safety net, not a
guarantee.
"""

from app.schemas.profile import MealPlan


def find_allergen_matches(meal_plan: MealPlan, allergies: list[str]) -> list[str]:
    if not allergies:
        return []
    food_names = " ".join(
        food.name.lower()
        for meal in (meal_plan.breakfast, meal_plan.lunch, meal_plan.dinner, meal_plan.snack)
        if meal is not None
        for food in meal.foods
    )
    return [allergy for allergy in allergies if allergy.strip().lower() in food_names]
