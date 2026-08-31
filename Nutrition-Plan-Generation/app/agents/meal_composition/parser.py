"""
Meal Composition Agent output parser.
Parses the LLM's raw JSON response into a validated MealPlan.
"""

import json
from app.schemas.profile import MealPlan, Meal, MealFoodItem
from app.core.logging import get_logger
from app.core.json_parser import extract_json

logger = get_logger(__name__)


def _parse_meal(data: dict) -> Meal:
    foods = []
    for f in data.get("foods", []):
        serving = float(f.get("serving_grams", f.get("serving", 100)))
        p = float(f.get("protein_g", f.get("protein", 0)))
        c = float(f.get("carbs_g", f.get("carbs", 0)))
        fat = float(f.get("fat_g", f.get("fat", 0)))

        # Check all common calorie keys returned by LLMs
        cal = float(f.get("calories", f.get("calories_kcal", f.get("kcal", f.get("energy_kcal", f.get("energy", 0))))))

        # If LLM returned 0 or omitted calories but provided macros, compute via Atwater factors (4*P + 4*C + 9*F)
        if cal <= 0 and (p > 0 or c > 0 or fat > 0):
            cal = round(p * 4.0 + c * 4.0 + fat * 9.0, 1)

        foods.append(MealFoodItem(
            name=f["name"],
            serving_grams=serving,
            calories=cal,
            protein_g=p,
            carbs_g=c,
            fat_g=fat,
        ))

    total_cal = float(data.get("total_calories", 0))
    if total_cal <= 0 or total_cal != sum(f.calories for f in foods):
        total_cal = sum(f.calories for f in foods)

    return Meal(
        meal_name=data["meal_name"],
        foods=foods,
        total_calories=round(total_cal, 1),
        total_protein_g=round(float(data.get("total_protein_g", sum(f.protein_g for f in foods))), 1),
        total_carbs_g=round(float(data.get("total_carbs_g", sum(f.carbs_g for f in foods))), 1),
        total_fat_g=round(float(data.get("total_fat_g", sum(f.fat_g for f in foods))), 1),
    )


def parse_meal_plan(raw_response: str) -> MealPlan:
    """
    Parse the LLM JSON output into a strongly-typed MealPlan.
    Raises ValueError on parse failure.
    """
    data = extract_json(raw_response)

    breakfast = _parse_meal(data["breakfast"])
    lunch = _parse_meal(data["lunch"])
    dinner = _parse_meal(data["dinner"])
    snack = _parse_meal(data["snack"]) if data.get("snack") else None

    plan = MealPlan(
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        snack=snack,
        total_daily_calories=float(data.get("total_daily_calories", 0)),
        total_daily_protein_g=float(data.get("total_daily_protein_g", 0)),
        total_daily_carbs_g=float(data.get("total_daily_carbs_g", 0)),
        total_daily_fat_g=float(data.get("total_daily_fat_g", 0)),
        notes=data.get("notes"),
    )

    # Recompute totals from meals to catch LLM rounding errors
    plan.total_daily_calories = round(
        breakfast.total_calories + lunch.total_calories + dinner.total_calories
        + (snack.total_calories if snack else 0), 1
    )
    plan.total_daily_protein_g = round(
        breakfast.total_protein_g + lunch.total_protein_g + dinner.total_protein_g
        + (snack.total_protein_g if snack else 0), 1
    )
    plan.total_daily_carbs_g = round(
        breakfast.total_carbs_g + lunch.total_carbs_g + dinner.total_carbs_g
        + (snack.total_carbs_g if snack else 0), 1
    )
    plan.total_daily_fat_g = round(
        breakfast.total_fat_g + lunch.total_fat_g + dinner.total_fat_g
        + (snack.total_fat_g if snack else 0), 1
    )

    logger.info(
        "Parsed MealPlan | %.0f kcal  P=%.1fg  C=%.1fg  F=%.1fg",
        plan.total_daily_calories,
        plan.total_daily_protein_g,
        plan.total_daily_carbs_g,
        plan.total_daily_fat_g,
    )
    return plan
