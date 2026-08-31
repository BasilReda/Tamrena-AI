"""
Explanation Agent — LLM-powered node.

Generates a human-readable explanation of the validated meal plan using Google GenAI / Gemini.
LangSmith tracing is enabled automatically via LANGCHAIN_* env vars.
"""

import json
from collections import Counter

from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.explanation.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.schemas.profile import MealPlan, MacroResult, ValidationReport, Explanation
from app.core.config import settings
from app.core.logging import get_logger
from app.core.json_parser import extract_json
from app.core.llm import GoogleGenAIChat

logger = get_logger(__name__)

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = GoogleGenAIChat(
            temperature=0.4,
        )
    return _llm


def _summarise_meal_plan(plan: MealPlan) -> str:
    lines = []
    for meal in [plan.breakfast, plan.lunch, plan.dinner]:
        lines.append(f"\n{meal.meal_name} ({meal.total_calories:.0f} kcal):")
        for food in meal.foods:
            lines.append(
                f"  - {food.name}: {food.serving_grams:.0f}g | "
                f"P={food.protein_g:.1f}g C={food.carbs_g:.1f}g F={food.fat_g:.1f}g"
            )
    if plan.snack:
        lines.append(f"\nSnack ({plan.snack.total_calories:.0f} kcal):")
        for food in plan.snack.foods:
            lines.append(
                f"  - {food.name}: {food.serving_grams:.0f}g | "
                f"P={food.protein_g:.1f}g C={food.carbs_g:.1f}g F={food.fat_g:.1f}g"
            )
    return "\n".join(lines)


def _food_reasoning_hints(plan: MealPlan) -> str:
    all_foods = [
        *plan.breakfast.foods,
        *plan.lunch.foods,
        *plan.dinner.foods,
        *(plan.snack.foods if plan.snack else []),
    ]
    counts = Counter(food.name for food in all_foods)
    repeated = [name for name, count in counts.items() if count > 1]
    hints = [
        "- Mention the actual foods selected and connect each one to its nutritional role.",
        "- Prefer concrete reasoning such as protein support, fiber, healthy fats, or slower-digesting carbohydrates.",
        "- Mention meal-to-meal variety and avoid generic 'balanced' language unless tied to specific foods.",
    ]
    if repeated:
        hints.append(f"- If repeated foods exist, explain why the repetition is practical: {', '.join(repeated)}.")
    return "\n".join(hints)


async def run_explanation_agent(
    meal_plan: MealPlan,
    macro_result: MacroResult,
    validation_report: ValidationReport,
) -> Explanation:
    """Call the Explanation Agent and return a structured Explanation."""
    meal_summary = _summarise_meal_plan(meal_plan)
    validation_status = (
        "PASSED ✓" if validation_report.passed else "PASSED with warnings"
    )
    issues_text = ""
    if validation_report.issues:
        issues_text = "Issues noted: " + "; ".join(
            f"{i.rule}: {i.actual}" for i in validation_report.issues
        )

    user_msg = USER_PROMPT_TEMPLATE.format(
        goal=macro_result.goal,
        target_calories=macro_result.target_calories,
        protein_g=macro_result.protein_g,
        carbs_g=macro_result.carbs_g,
        fat_g=macro_result.fat_g,
        meal_plan_summary=meal_summary,
        validation_status=validation_status,
        validation_issues=issues_text + ("\n" + _food_reasoning_hints(meal_plan) if meal_summary else ""),
    )

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)]

    last_error = None
    for attempt in range(1, 4):
        try:
            active_model = _get_llm().model_name
            logger.info("Explanation Agent → calling Gemini (%s, attempt=%d)", active_model, attempt)
            response = await _get_llm().ainvoke(messages)
            raw = response.content.strip()

            if not raw:
                meta = getattr(response, "response_metadata", {})
                finish_reason = meta.get("finish_reason", "unknown")
                logger.warning("Attempt %d produced empty content (finish_reason=%s)", attempt, finish_reason)
                raise ValueError(f"LLM returned empty content (finish_reason={finish_reason}).")

            data = extract_json(raw)
            explanation = Explanation(**data)
            logger.info("Explanation Agent completed")
            return explanation
        except Exception as exc:
            last_error = exc
            logger.warning("Explanation Agent attempt %d failed: %s", attempt, exc)
            if attempt < 3:
                messages.append(HumanMessage(content="Your previous output was empty or invalid JSON. Please provide ONLY the complete, valid JSON object without truncation."))

    raise ValueError(f"Explanation Agent failed after 3 attempts: {last_error}") from last_error
