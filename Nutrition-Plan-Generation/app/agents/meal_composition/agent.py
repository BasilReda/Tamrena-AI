"""
Meal Composition Agent — LLM-powered node.

Receives MacroResult + RetrievedFoods → produces MealPlan.
On graph-level retries (retry_count > 0), uses a targeted correction prompt
that tells the LLM exactly which metrics failed and how to fix them without
disturbing the metrics that already pass.

LangSmith tracing is enabled automatically via LANGCHAIN_* env vars.
"""

import json
import os
from collections import defaultdict

# pyrefly: ignore [missing-import]
from app.core.llm import ITIBedrockChat

# pyrefly: ignore [missing-import]
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.meal_composition.prompt import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    CORRECTION_PROMPT_TEMPLATE,
)
from app.agents.meal_composition.parser import parse_meal_plan
from app.agents.meal_composition.correction import build_correction_context
from app.schemas.profile import MacroResult, MealPlan, ValidationReport
from app.schemas.foods import RetrievedFoods
from app.core.config import settings
from app.core.constants import MEAL_DISTRIBUTION
from app.core.logging import get_logger

logger = get_logger(__name__)

_llm = None

_MEAL_ROLE_GROUPS = {
    "breakfast": ["Main Carb", "Protein", "Fruit", "Dairy", "Healthy Fat", "Beverage"],
    "lunch": ["Main Protein", "Main Carb", "Vegetable", "Healthy Fat", "Dairy", "Fruit"],
    "dinner": ["Main Protein", "Vegetable", "Healthy Fat", "Main Carb", "Dairy", "Fruit"],
    "snack": ["Fruit", "Dairy", "Protein Snack", "Healthy Snack", "Healthy Fat", "Beverage"],
}

_INGREDIENT_KEYWORDS = {
    "flour",
    "starch",
    "extract",
    "powder",
    "meal",
    "bran",
    "germ",
    "shortening",
    "baking",
    "seasoning",
    "flavoring",
}


def _get_llm():
    global _llm
    if _llm is None:
        model_id = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or getattr(settings, "gemini_model", "gemini-3.5-flash-lite")
        _llm = ITIBedrockChat(model_id=model_id)
    return _llm


def _format_food_line(food) -> str:
    best_with = ", ".join(food.best_with[:4]) or "none"
    slots = ", ".join(food.meal_slot_fit) or "any"
    goals = ", ".join(food.goal_fit_tags) or "general"
    diet = ", ".join(food.diet_profile or food.diet_types) or "normal"
    return (
        f"- {food.name} | {food.calories_per_100g:.0f} kcal | "
        f"P={food.protein_per_100g:.1f}g C={food.carbs_per_100g:.1f}g F={food.fat_per_100g:.1f}g | "
        f"role={food.meal_role} | slots={slots} | goals={goals} | "
        f"macro={food.primary_macro_type}/{food.macro_gap_utility_profile} | "
        f"diet={diet} | priority={food.selection_priority:.0f} | best_with={best_with}"
    )


def _is_ingredient_like(food) -> bool:
    name = food.name.lower()
    role = food.meal_role.lower()
    utility = food.macro_gap_utility_profile.lower()
    if role in {"healthy fat", "beverage", "fruit", "vegetable", "main protein", "main carb", "dairy"}:
        return False
    return any(keyword in name for keyword in _INGREDIENT_KEYWORDS) or "processing" in utility


def _slot_score(food, meal_slot: str, goal: str, diet_type: str) -> tuple[float, float, float, float, str]:
    meal_slot = meal_slot.lower()
    goal = goal.lower()
    diet_type = diet_type.lower()

    slot_fit = 1.0 if meal_slot in food.meal_slot_fit else 0.0
    goal_fit = 1.0 if goal in food.goal_fit_tags else (0.5 if "maintenance" in food.goal_fit_tags else 0.0)
    diet_fit = 1.0 if diet_type in {"normal", "omnivore"} or diet_type in food.diet_profile or diet_type in food.diet_types else 0.0
    best_with_bonus = 0.5 if food.best_with else 0.0
    priority = float(food.selection_priority)
    ingredient_penalty = -1.0 if _is_ingredient_like(food) else 0.0
    return (slot_fit, goal_fit, diet_fit, best_with_bonus + priority / 5.0 + ingredient_penalty, food.meal_role.lower())


def _pairing_hints(foods: RetrievedFoods, meal_slot: str) -> list[str]:
    candidates = {food.name.lower(): food for food in foods.all_foods}
    hints: list[str] = []
    for food in foods.all_foods:
        if food.meal_slot_fit and meal_slot not in food.meal_slot_fit:
            continue
        pairings = [pair for pair in food.best_with[:4] if pair.lower() in candidates]
        if pairings:
            hints.append(f"- {food.name} pairs naturally with: {', '.join(pairings[:3])}")
        if len(hints) >= 5:
            break
    return hints


def _group_foods_for_prompt(foods: RetrievedFoods, meal_slot: str, goal: str, diet_type: str) -> str:
    """Render candidate foods as meal-oriented sections ordered by metadata fit."""
    sections = defaultdict(list)
    for food in foods.all_foods:
        sections[food.meal_role or "General"].append(food)

    if not sections:
        return "No candidate foods available."

    ordered_roles = _MEAL_ROLE_GROUPS.get(meal_slot.lower(), [])
    role_names = list(sections.keys())
    remaining_roles = [role for role in role_names if role not in ordered_roles]
    ordered_roles.extend(sorted(remaining_roles))

    lines = [
        f"[{meal_slot.title()} candidates]",
        "Prefer foods that match the slot, goal, diet, and complementary roles.",
        "Ingredient-like foods are listed lower; use them only as minor supporting components when appropriate.",
    ]
    pairings = _pairing_hints(foods, meal_slot.lower())
    if pairings:
        lines.append("\n[Realistic pairing hints]")
        lines.extend(pairings)
    for role in ordered_roles:
        items = sections.get(role, [])
        if not items:
            continue
        ranked = sorted(items, key=lambda food: _slot_score(food, meal_slot, goal, diet_type), reverse=True)
        lines.append(f"\n[{role}]")
        for food in ranked[:8]:
            lines.append(_format_food_line(food))
            if food.best_with:
                lines.append(f"  best pairings: {', '.join(food.best_with[:3])}")

    return "\n".join(lines)


def _build_candidate_context(foods: RetrievedFoods, goal: str, diet_type: str) -> str:
    sections = []
    for slot in ["breakfast", "lunch", "dinner", "snack"]:
        sections.append(_group_foods_for_prompt(foods, slot, goal, diet_type))
    return "\n\n".join(sections)


async def run_meal_composition_agent(
    macro_result: MacroResult,
    retrieved_foods: RetrievedFoods,
    retry_count: int = 0,
    previous_meal_plan: MealPlan | None = None,
    previous_validation: ValidationReport | None = None,
) -> MealPlan:
    """
    Call the Meal Composition Agent to generate a daily meal plan.

    On the first call (retry_count == 0): generates from scratch using the
    candidate food list.

    On retries (retry_count > 0): if a previous_meal_plan and
    previous_validation are supplied, uses a targeted CORRECTION prompt that
    tells the LLM exactly which metrics failed and how to surgically fix them
    without changing the metrics that already pass.

    Includes an internal retry loop to handle empty/truncated LLM responses.
    """
    target_cal = macro_result.target_calories
    candidate_str = _build_candidate_context(retrieved_foods, macro_result.goal, macro_result.diet_type)

    # ── Build initial message list ─────────────────────────────────────────────
    if (
        retry_count > 0
        and previous_meal_plan is not None
        and previous_validation is not None
    ):
        # Targeted correction mode — send the current broken plan + precise fix instructions
        logger.info("Meal Composition Agent → CORRECTION mode (retry=%d)", retry_count)
        current_plan_json, validation_issues, correction_instructions = (
            build_correction_context(
                previous_meal_plan, macro_result, previous_validation
            )
        )
        correction_msg = CORRECTION_PROMPT_TEMPLATE.format(
            current_plan_json=current_plan_json,
            validation_issues=validation_issues,
            correction_instructions=correction_instructions,
            candidate_foods=candidate_str,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=correction_msg),
        ]
    else:
        # Fresh generation mode
        user_msg = USER_PROMPT_TEMPLATE.format(
            target_calories=target_cal,
            protein_g=macro_result.protein_g,
            carbs_g=macro_result.carbs_g,
            fat_g=macro_result.fat_g,
            goal=macro_result.goal,
            diet_type=macro_result.diet_type,
            preferences=", ".join(macro_result.preferences) or "None",
            allergies=", ".join(macro_result.allergies) or "None",
            breakfast_cal=target_cal * MEAL_DISTRIBUTION["breakfast"],
            lunch_cal=target_cal * MEAL_DISTRIBUTION["lunch"],
            dinner_cal=target_cal * MEAL_DISTRIBUTION["dinner"],
            snack_cal=target_cal * MEAL_DISTRIBUTION["snack"],
            candidate_foods=candidate_str,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]

    # ── LLM call with internal retry for parse/empty failures ─────────────────
    last_error = None
    for attempt in range(1, 4):
        try:
            logger.info(
                "Meal Composition Agent → calling ITI Bedrock (attempt=%d, retry=%d)",
                attempt,
                retry_count,
            )
            response = await _get_llm().ainvoke(messages)
            raw = response.content.strip()

            if not raw:
                meta = getattr(response, "response_metadata", {})
                finish_reason = meta.get("finish_reason", "unknown")
                logger.warning(
                    "Attempt %d produced empty content (finish_reason=%s)",
                    attempt,
                    finish_reason,
                )
                raise ValueError(
                    f"LLM returned empty content (finish_reason={finish_reason})."
                )

            meal_plan = parse_meal_plan(raw)
            logger.info("Meal Composition Agent completed | retry=%d", retry_count)
            return meal_plan
        except Exception as exc:
            last_error = exc
            logger.warning("Meal Composition Agent attempt %d failed: %s", attempt, exc)
            if attempt < 3:
                # Append guidance asking for strict JSON without truncation
                messages.append(
                    HumanMessage(
                        content="Your previous output was empty or invalid JSON. Please provide ONLY the complete, valid JSON object matching the exact schema without truncation or missing brackets."
                    )
                )

    raise ValueError(
        f"Meal Composition Agent failed after 3 attempts: {last_error}"
    ) from last_error
