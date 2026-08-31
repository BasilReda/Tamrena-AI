"""
Meal Composition Agent — LLM-Arabic mode.

This agent generates authentic Egyptian meals in Arabic WITHOUT using the food
dataset. It relies entirely on the LLM's knowledge of Egyptian cuisine.

On graph-level retries (retry_count > 0), uses a targeted Arabic correction
prompt that tells the LLM exactly which metrics failed and how to fix them
without disturbing the metrics that already pass.

Shares the same MealPlan output schema and parse_meal_plan() parser as the
dataset-backed agent so the rest of the pipeline is unaffected.
"""

import os

# pyrefly: ignore [missing-import]
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import ITIBedrockChat
from app.agents.meal_composition.prompt_arabic import (
    SYSTEM_PROMPT_ARABIC,
    USER_PROMPT_TEMPLATE_ARABIC,
    CORRECTION_PROMPT_TEMPLATE_ARABIC,
)
from app.agents.meal_composition.parser import parse_meal_plan
from app.agents.meal_composition.correction import build_correction_context_arabic
from app.agents.meal_composition.allergen_check import find_allergen_matches
from app.schemas.profile import MacroResult, MealPlan, ValidationReport
from app.core.config import settings
from app.core.constants import MEAL_DISTRIBUTION
from app.core.logging import get_logger

logger = get_logger(__name__)

_llm_arabic = None


def _get_llm_arabic():
    global _llm_arabic
    if _llm_arabic is None:
        model_id = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or getattr(settings, "gemini_model", "gemini-3.5-flash-lite")
        _llm_arabic = ITIBedrockChat(model_id=model_id)
    return _llm_arabic


async def run_meal_composition_agent_arabic(
    macro_result: MacroResult,
    retry_count: int = 0,
    previous_meal_plan: MealPlan | None = None,
    previous_validation: ValidationReport | None = None,
) -> MealPlan:
    """
    Call the LLM-Arabic Meal Composition Agent to generate a daily meal plan
    using authentic Egyptian cuisine with Arabic food names.

    On the first call (retry_count == 0): generates freely from scratch.

    On retries (retry_count > 0): if previous_meal_plan and previous_validation
    are supplied, uses a targeted Arabic CORRECTION prompt that tells the LLM
    exactly which metrics failed and how to fix them without touching the
    metrics that already pass.

    Includes an internal retry loop to handle empty/truncated LLM responses.
    """
    target_cal = macro_result.target_calories

    # ── Build initial message list ─────────────────────────────────────────────
    if (
        retry_count > 0
        and previous_meal_plan is not None
        and previous_validation is not None
    ):
        # Targeted correction mode (Arabic)
        logger.info("LLM-Arabic Meal Agent → CORRECTION mode (retry=%d)", retry_count)
        current_plan_json, validation_issues, correction_instructions = (
            build_correction_context_arabic(
                previous_meal_plan, macro_result, previous_validation
            )
        )
        correction_msg = CORRECTION_PROMPT_TEMPLATE_ARABIC.format(
            current_plan_json=current_plan_json,
            validation_issues=validation_issues,
            correction_instructions=correction_instructions,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_ARABIC),
            HumanMessage(content=correction_msg),
        ]
    else:
        # Fresh generation mode
        user_msg = USER_PROMPT_TEMPLATE_ARABIC.format(
            target_calories=target_cal,
            protein_g=macro_result.protein_g,
            carbs_g=macro_result.carbs_g,
            fat_g=macro_result.fat_g,
            goal=macro_result.goal,
            diet_type=macro_result.diet_type,
            preferences=", ".join(macro_result.preferences) or "لا يوجد",
            allergies=", ".join(macro_result.allergies) or "لا يوجد",
            additional_notes="لا يوجد",
            breakfast_cal=target_cal * MEAL_DISTRIBUTION["breakfast"],
            lunch_cal=target_cal * MEAL_DISTRIBUTION["lunch"],
            dinner_cal=target_cal * MEAL_DISTRIBUTION["dinner"],
            snack_cal=target_cal * MEAL_DISTRIBUTION["snack"],
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_ARABIC),
            HumanMessage(content=user_msg),
        ]

    # ── LLM call with internal retry for parse/empty failures ─────────────────
    last_error = None
    for attempt in range(1, 4):
        try:
            logger.info(
                "LLM-Arabic Meal Agent → calling ITI Bedrock (attempt=%d, retry=%d)",
                attempt,
                retry_count,
            )
            response = await _get_llm_arabic().ainvoke(messages)
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
            matches = find_allergen_matches(meal_plan, macro_result.allergies)
            if matches:
                raise ValueError(f"Generated plan contains listed allergens: {matches}")
            logger.info("LLM-Arabic Meal Agent completed | retry=%d", retry_count)
            return meal_plan

        except Exception as exc:
            last_error = exc
            logger.warning("LLM-Arabic Meal Agent attempt %d failed: %s", attempt, exc)
            if attempt < 3:
                content = (
                    "المخرجات السابقة كانت فارغة أو JSON غير صالح. "
                    "الرجاء تقديم كائن JSON كامل وصالح فقط يطابق الهيكل المطلوب بدون اقتطاع."
                )
                if isinstance(exc, ValueError) and "allergen" in str(exc).lower():
                    content = (
                        "الخطة السابقة تحتوي على مسببات حساسية يجب تجنبها تماماً. "
                        "أعد إنشاء الخطة بالكامل بدون استخدام أي طعام يحتوي على هذه المسببات."
                    )
                messages.append(HumanMessage(content=content))

    raise ValueError(
        f"LLM-Arabic Meal Agent failed after 3 attempts: {last_error}"
    ) from last_error
