"""
Correction helpers for meal composition agents.

Builds targeted correction prompts from a ValidationReport so the LLM
can surgically fix ONLY the failing metrics without disturbing the passing ones.
"""

import json
from app.schemas.profile import MealPlan, MacroResult, ValidationReport
from app.core.constants import (
    CALORIE_TOLERANCE_PCT,
    PROTEIN_TOLERANCE_PCT,
    CARBS_TOLERANCE_PCT,
    FAT_TOLERANCE_PCT,
)


def _pct_deviation(actual: float, target: float) -> float:
    if target == 0:
        return 0.0
    return (actual - target) / target


def build_correction_context(
    meal_plan: MealPlan,
    macro_result: MacroResult,
    validation_report: ValidationReport,
) -> tuple[str, str, str]:
    """
    Build the three strings needed by the correction prompt templates:
        - current_plan_json
        - validation_issues   (human-readable list of pass/fail per metric)
        - correction_instructions (specific delta + how to fix each failing metric)

    Returns (current_plan_json, validation_issues, correction_instructions).
    """
    # ── Serialize current plan ────────────────────────────────────────────────
    current_plan_json = json.dumps(meal_plan.model_dump(), indent=2, ensure_ascii=False)

    # ── Compute per-metric deviations ─────────────────────────────────────────
    metrics = [
        (
            "Calories",
            meal_plan.total_daily_calories,
            macro_result.target_calories,
            CALORIE_TOLERANCE_PCT,
            "kcal",
        ),
        (
            "Protein",
            meal_plan.total_daily_protein_g,
            macro_result.protein_g,
            PROTEIN_TOLERANCE_PCT,
            "g",
        ),
        (
            "Carbohydrates",
            meal_plan.total_daily_carbs_g,
            macro_result.carbs_g,
            CARBS_TOLERANCE_PCT,
            "g",
        ),
        (
            "Fat",
            meal_plan.total_daily_fat_g,
            macro_result.fat_g,
            FAT_TOLERANCE_PCT,
            "g",
        ),
    ]

    issues_lines: list[str] = []
    correction_lines: list[str] = []

    for name, actual, target, tolerance, unit in metrics:
        dev = _pct_deviation(actual, target)
        dev_pct = dev * 100
        status = "FAIL ❌" if abs(dev) > tolerance else "PASS ✅"
        issues_lines.append(
            f"- {name}: actual={actual:.1f}{unit}, target={target:.1f}{unit}, "
            f"deviation={dev_pct:+.1f}% — {status}"
        )

        if abs(dev) > tolerance:
            delta = target - actual  # positive = need more, negative = need less
            direction = "increase" if delta > 0 else "decrease"
            abs_delta = abs(delta)

            if name == "Calories":
                correction_lines.append(
                    f"• CALORIES ({dev_pct:+.1f}%): You need to {direction} calories by "
                    f"~{abs_delta:.0f} kcal. "
                    + (
                        "Add larger servings of calorie-dense foods spread across meals."
                        if delta > 0
                        else "Reduce serving sizes of calorie-dense foods across meals."
                    )
                    + " Prefer adjustments that keep protein, carbs, and fat proportions stable."
                )
            elif name == "Protein":
                correction_lines.append(
                    f"• PROTEIN ({dev_pct:+.1f}%): You need to {direction} protein by "
                    f"~{abs_delta:.1f}g. "
                    + (
                        "Replace some carb/fat-heavy items with protein-rich alternatives "
                        "(e.g., swap bread for chicken breast, add eggs or legumes). "
                        "Keep total calorie change minimal by balancing serving sizes."
                        if delta > 0
                        else "Reduce serving sizes of high-protein foods slightly. "
                        "Compensate calorie loss with small additions of carb/fat foods."
                    )
                )
            elif name == "Carbohydrates":
                correction_lines.append(
                    f"• CARBOHYDRATES ({dev_pct:+.1f}%): You need to {direction} carbs by "
                    f"~{abs_delta:.1f}g. "
                    + (
                        "Add more carb-rich foods (rice, bread, fruits) or increase their servings. "
                        "Compensate any excess calories by slightly reducing fat-rich items."
                        if delta > 0
                        else "Reduce carb-heavy items (rice, bread, pasta) or shrink their servings. "
                        "Keep protein and fat approximately the same."
                    )
                )
            elif name == "Fat":
                correction_lines.append(
                    f"• FAT ({dev_pct:+.1f}%): You need to {direction} fat by "
                    f"~{abs_delta:.1f}g. "
                    + (
                        "Add healthy fat sources (olive oil, nuts, avocado) or increase their servings. "
                        "Keep protein and carbs approximately the same."
                        if delta > 0
                        else "Reduce high-fat items (oils, nuts, fatty meats) or shrink their servings. "
                        "Keep protein and carbs approximately the same."
                    )
                )

    validation_issues = "\n".join(issues_lines)
    correction_instructions = (
        "\n".join(correction_lines)
        if correction_lines
        else "No corrections needed — this should not have been called."
    )

    return current_plan_json, validation_issues, correction_instructions


def build_correction_context_arabic(
    meal_plan: MealPlan,
    macro_result: MacroResult,
    validation_report: ValidationReport,
) -> tuple[str, str, str]:
    """
    Arabic version of build_correction_context.
    Returns (current_plan_json, validation_issues_ar, correction_instructions_ar).
    """
    current_plan_json = json.dumps(meal_plan.model_dump(), indent=2, ensure_ascii=False)

    metrics = [
        ("السعرات الحرارية", meal_plan.total_daily_calories, macro_result.target_calories, CALORIE_TOLERANCE_PCT, "سعرة"),
        ("البروتين", meal_plan.total_daily_protein_g, macro_result.protein_g, PROTEIN_TOLERANCE_PCT, "جرام"),
        ("الكربوهيدرات", meal_plan.total_daily_carbs_g, macro_result.carbs_g, CARBS_TOLERANCE_PCT, "جرام"),
        ("الدهون", meal_plan.total_daily_fat_g, macro_result.fat_g, FAT_TOLERANCE_PCT, "جرام"),
    ]

    issues_lines: list[str] = []
    correction_lines: list[str] = []

    for name, actual, target, tolerance, unit in metrics:
        dev = _pct_deviation(actual, target)
        dev_pct = dev * 100
        status = "فشل ❌" if abs(dev) > tolerance else "نجح ✅"
        issues_lines.append(
            f"- {name}: الفعلي={actual:.1f} {unit}, الهدف={target:.1f} {unit}, "
            f"الانحراف={dev_pct:+.1f}% — {status}"
        )

        if abs(dev) > tolerance:
            delta = target - actual
            direction = "زيادة" if delta > 0 else "تقليل"
            abs_delta = abs(delta)

            if name == "السعرات الحرارية":
                correction_lines.append(
                    f"• السعرات ({dev_pct:+.1f}%): تحتاج إلى {direction} السعرات بمقدار ~{abs_delta:.0f} سعرة. "
                    + (
                        "أضف كميات أكبر من الأطعمة الغنية بالطاقة موزعة على الوجبات مع الحفاظ على نسب الماكرو."
                        if delta > 0
                        else "قلل أحجام الأطعمة الغنية بالطاقة مع الحفاظ على نسب الماكرو."
                    )
                )
            elif name == "البروتين":
                correction_lines.append(
                    f"• البروتين ({dev_pct:+.1f}%): تحتاج إلى {direction} البروتين بمقدار ~{abs_delta:.1f}جم. "
                    + (
                        "استبدل بعض الأطعمة الغنية بالكربوهيدرات أو الدهون بأخرى غنية بالبروتين مثل "
                        "(الدجاج، البيض، الفول، العدس، السمك). حافظ على السعرات الإجمالية قريبة من الهدف."
                        if delta > 0
                        else "قلل كمية الأطعمة البروتينية قليلاً وعوّض بكميات صغيرة من الكربوهيدرات أو الدهون."
                    )
                )
            elif name == "الكربوهيدرات":
                correction_lines.append(
                    f"• الكربوهيدرات ({dev_pct:+.1f}%): تحتاج إلى {direction} الكربوهيدرات بمقدار ~{abs_delta:.1f}جم. "
                    + (
                        "أضف المزيد من الأرز أو العيش أو الفاكهة أو الكشري. قلل الدهون قليلاً لتعويض السعرات الزائدة."
                        if delta > 0
                        else "قلل كميات الأرز والعيش والمكرونة. حافظ على البروتين والدهون كما هي."
                    )
                )
            elif name == "الدهون":
                correction_lines.append(
                    f"• الدهون ({dev_pct:+.1f}%): تحتاج إلى {direction} الدهون بمقدار ~{abs_delta:.1f}جم. "
                    + (
                        "أضف مصادر الدهون الصحية مثل (زيت الزيتون، المكسرات، الأفوكادو). حافظ على البروتين والكربوهيدرات."
                        if delta > 0
                        else "قلل الأطعمة الغنية بالدهون (الزيوت، المكسرات، اللحوم الدسمة). حافظ على البروتين والكربوهيدرات."
                    )
                )

    validation_issues = "\n".join(issues_lines)
    correction_instructions = (
        "\n".join(correction_lines)
        if correction_lines
        else "لا توجد تصحيحات مطلوبة."
    )

    return current_plan_json, validation_issues, correction_instructions
