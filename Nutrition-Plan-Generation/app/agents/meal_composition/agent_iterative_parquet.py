"""
Iterative Meal Composition Agent — Parquet + Arabic mode (llm_arabic_parquet).

Strategy:
- 1 SINGLE LLM Call per Slot (4 calls total: breakfast, lunch, dinner, snack).
- Each slot call returns Option A, Option B, and Option C together in one structured JSON.
- Grounded in real foods from foods_master_final.parquet.
- Enforces strict culinary harmony (max 1 main animal protein per meal, no duplicate foods).
- Fast execution (~4-8 seconds total) with zero ITI Bedrock rate limits.
"""

from __future__ import annotations
import asyncio
import os

# pyrefly: ignore [missing-import]
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import ITIBedrockChat
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.profile import (
    MacroResult,
    MealSlotTarget,
    MealDistribution,
    Meal,
    MealPlan,
    TripleMealPlan,
)
from app.schemas.foods import ParquetFoodItem, ParquetRetrievedFoods
from app.agents.meal_composition.prompt_slot_parquet import (
    SYSTEM_PROMPT_SLOT_PARQUET,
    USER_PROMPT_SLOT_PARQUET_TEMPLATE,
    _format_food_catalog,
)
from app.agents.meal_composition.parser import _parse_meal
from app.core.json_parser import extract_json

logger = get_logger(__name__)


def _clean_and_deduplicate_meal_foods(meal: Meal) -> Meal:
    """
    Deduplicates foods in a meal (if the LLM outputted duplicate items)
    by combining their serving_grams, calories, and macros into a single entry.
    Also ensures no zero-serving or invalid food items exist.
    """
    deduped_foods: dict[str, dict] = {}
    for f in meal.foods:
        norm_name = f.name.strip()
        if norm_name in deduped_foods:
            existing = deduped_foods[norm_name]
            existing["serving_grams"] += f.serving_grams
            existing["calories"] += f.calories
            existing["protein_g"] += f.protein_g
            existing["carbs_g"] += f.carbs_g
            existing["fat_g"] += f.fat_g
        else:
            deduped_foods[norm_name] = {
                "name": norm_name,
                "serving_grams": f.serving_grams,
                "calories": f.calories,
                "protein_g": f.protein_g,
                "carbs_g": f.carbs_g,
                "fat_g": f.fat_g,
            }

    cleaned_list = []
    for food_dict in deduped_foods.values():
        from app.schemas.profile import MealFoodItem

        cleaned_list.append(
            MealFoodItem(
                name=food_dict["name"],
                serving_grams=round(food_dict["serving_grams"], 1),
                calories=round(food_dict["calories"], 1),
                protein_g=round(food_dict["protein_g"], 1),
                carbs_g=round(food_dict["carbs_g"], 1),
                fat_g=round(food_dict["fat_g"], 1),
            )
        )

    tot_cal = round(sum(f.calories for f in cleaned_list), 1)
    tot_prot = round(sum(f.protein_g for f in cleaned_list), 1)
    tot_carbs = round(sum(f.carbs_g for f in cleaned_list), 1)
    tot_fat = round(sum(f.fat_g for f in cleaned_list), 1)

    return Meal(
        meal_name=meal.meal_name,
        foods=cleaned_list,
        total_calories=tot_cal,
        total_protein_g=tot_prot,
        total_carbs_g=tot_carbs,
        total_fat_g=tot_fat,
    )


async def _generate_slot_options_parquet(
    slot: MealSlotTarget,
    macro_result: MacroResult,
    slot_foods: list[ParquetFoodItem],
) -> tuple[Meal, Meal, Meal]:
    """
    Call the LLM ONCE for this meal slot to generate all 3 options (option_a, option_b, option_c)
    simultaneously in a single JSON response.
    """
    food_catalog = _format_food_catalog(slot_foods)

    user_msg = USER_PROMPT_SLOT_PARQUET_TEMPLATE.format(
        meal_name=slot.meal_name,
        target_calories=slot.target_calories,
        target_protein_g=slot.target_protein_g,
        target_carbs_g=slot.target_carbs_g,
        target_fat_g=slot.target_fat_g,
        goal=macro_result.goal,
        diet_type=macro_result.diet_type,
        preferences=", ".join(macro_result.preferences) or "لا يوجد",
        allergies=", ".join(macro_result.allergies) or "لا يوجد",
        food_catalog=food_catalog,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT_SLOT_PARQUET),
        HumanMessage(content=user_msg),
    ]

    model_id = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or getattr(settings, "gemini_model", "gemini-3.5-flash-lite")
    llm = ITIBedrockChat(model_id=model_id, temperature=0.8)

    last_error = None
    for attempt in range(1, 4):
        try:
            logger.info(
                "Parquet Slot=%s attempt=%d — calling LLM (1 call for 3 options, %d candidate foods)",
                slot.slot_key,
                attempt,
                len(slot_foods),
            )
            response = await llm.ainvoke(messages)
            raw = response.content.strip()

            if not raw:
                meta = getattr(response, "response_metadata", {})
                finish_reason = meta.get("finish_reason", "unknown")
                raise ValueError(
                    f"Empty LLM response for slot={slot.slot_key} (finish_reason={finish_reason})"
                )

            data = extract_json(raw)

            # Extract option_a, option_b, option_c
            raw_a = data.get("option_a", data)
            raw_b = data.get("option_b", raw_a)
            raw_c = data.get("option_c", raw_a)

            # Ensure meal_name is populated
            if "meal_name" not in raw_a:
                raw_a["meal_name"] = slot.meal_name
            if "meal_name" not in raw_b:
                raw_b["meal_name"] = slot.meal_name
            if "meal_name" not in raw_c:
                raw_c["meal_name"] = slot.meal_name

            meal_a = _clean_and_deduplicate_meal_foods(_parse_meal(raw_a))
            meal_b = _clean_and_deduplicate_meal_foods(_parse_meal(raw_b))
            meal_c = _clean_and_deduplicate_meal_foods(_parse_meal(raw_c))

            logger.info(
                "Parquet Slot=%s complete | A=%.0f kcal  B=%.0f kcal  C=%.0f kcal",
                slot.slot_key,
                meal_a.total_calories,
                meal_b.total_calories,
                meal_c.total_calories,
            )
            return meal_a, meal_b, meal_c

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Parquet Slot=%s attempt=%d failed: %s",
                slot.slot_key,
                attempt,
                exc,
            )
            if attempt < 3:
                messages.append(
                    HumanMessage(
                        content=(
                            "المخرجات السابقة بها خطأ أو JSON غير صالح. "
                            "الرجاء تقديم كائن JSON كامل وصالح يحتوي على الخيارات الثلاثة "
                            "(option_a, option_b, option_c) بدون اقتطاع."
                        )
                    )
                )

    raise ValueError(
        f"Failed to generate parquet meal options for slot={slot.slot_key} after 3 attempts: {last_error}"
    ) from last_error


def _build_meal_plan_from_slots(
    slots: dict[str, Meal],
    meal_distribution: MealDistribution,
) -> MealPlan:
    """Assemble a MealPlan from per-slot Meal objects."""
    b = slots["breakfast"]
    l = slots["lunch"]
    d = slots["dinner"]
    s = slots.get("snack")

    return MealPlan(
        breakfast=b,
        lunch=l,
        dinner=d,
        snack=s,
        total_daily_calories=round(
            b.total_calories
            + l.total_calories
            + d.total_calories
            + (s.total_calories if s else 0),
            1,
        ),
        total_daily_protein_g=round(
            b.total_protein_g
            + l.total_protein_g
            + d.total_protein_g
            + (s.total_protein_g if s else 0),
            1,
        ),
        total_daily_carbs_g=round(
            b.total_carbs_g
            + l.total_carbs_g
            + d.total_carbs_g
            + (s.total_carbs_g if s else 0),
            1,
        ),
        total_daily_fat_g=round(
            b.total_fat_g + l.total_fat_g + d.total_fat_g + (s.total_fat_g if s else 0),
            1,
        ),
        notes=None,
    )


async def run_meal_composition_iterative_parquet(
    macro_result: MacroResult,
    meal_distribution: MealDistribution,
    parquet_foods: ParquetRetrievedFoods,
) -> TripleMealPlan:
    """
    Generate 3 independent full-day meal plan options using 1 LLM call PER SLOT (4 calls total).

    - Breakfast call → returns Option A, B, C for Breakfast
    - Lunch call     → returns Option A, B, C for Lunch
    - Dinner call    → returns Option A, B, C for Dinner
    - Snack call     → returns Option A, B, C for Snack

    Total: 4 LLM calls total. Super fast (~4-8 seconds execution). Zero Bedrock rate limits.
    """
    slot_order = ["breakfast", "lunch", "dinner", "snack"]
    slot_map: dict[str, MealSlotTarget] = {
        "breakfast": meal_distribution.breakfast,
        "lunch": meal_distribution.lunch,
        "dinner": meal_distribution.dinner,
        "snack": meal_distribution.snack,
    }

    option_slots: dict[str, dict[str, Meal]] = {
        "a": {},
        "b": {},
        "c": {},
    }

    for slot_key in slot_order:
        slot = slot_map[slot_key]
        slot_foods = parquet_foods.for_slot(slot_key)

        meal_a, meal_b, meal_c = await _generate_slot_options_parquet(
            slot, macro_result, slot_foods
        )

        option_slots["a"][slot_key] = meal_a
        option_slots["b"][slot_key] = meal_b
        option_slots["c"][slot_key] = meal_c

    option_a = _build_meal_plan_from_slots(option_slots["a"], meal_distribution)
    option_b = _build_meal_plan_from_slots(option_slots["b"], meal_distribution)
    option_c = _build_meal_plan_from_slots(option_slots["c"], meal_distribution)

    logger.info(
        "Parquet TripleMealPlan complete (4 LLM calls) | A=%.0f kcal  B=%.0f kcal  C=%.0f kcal",
        option_a.total_daily_calories,
        option_b.total_daily_calories,
        option_c.total_daily_calories,
    )

    return TripleMealPlan(
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        meal_distribution=meal_distribution,
    )
