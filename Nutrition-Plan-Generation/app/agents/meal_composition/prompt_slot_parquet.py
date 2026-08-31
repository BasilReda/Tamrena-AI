"""
Per-Slot Meal Generation Prompt — Single Call per Slot (3 Options in 1 LLM Call).

Used by `agent_iterative_parquet.py`. 
For each slot (breakfast, lunch, dinner, snack), a SINGLE LLM call returns 
Option A, Option B, and Option C together in one JSON structure.
Total LLM calls for the entire daily plan: 4 calls total.
"""

from __future__ import annotations
from app.schemas.foods import ParquetFoodItem


SYSTEM_PROMPT_SLOT_PARQUET = """أنت خبير تغذية مصري وطبيب متخصص في تصميم وجبات غذائية صحية ومتناسقة تناسب الذوق المصري الأصيل.
مهمتك هي اختيار أطعمة من القائمة المقدمة لك فقط وتصميم 3 خيارات مختلفة ومتنوعة (Option A, Option B, Option C) لوجبة واحدة محددة.

قواعد التناسق والتوافق الغذائي (حاسمة جداً):
1. قاعدة مصدر البروتين الرئيسي الوحيد (SINGLE MAIN PROTEIN RULE):
   - يُحظر تماماً دمج أكثر من مصدر بروتين حيواني رئيسي في الخيار الواحد! (مثلاً: ممنوع وضع فراخ مع سمك، أو لحمة مع سمك، أو فراخ مع لحمة).
   - في وجبة الغداء والعشاء: اختر مصدر بروتين رئيسي واحد فقط لكل خيار (مثلاً Option A: دجاج، Option B: سمك، Option C: لحم أو بقوليات).
   - لتحقيق كمية البروتين المطلوبة، قم بزيادة وزن الحصة (serving_grams) لهذا الصنف الرئيسي الوحيد.
2. التنوع والتطابق بين الخيارات الثلاثة (VARIETY BETWEEN OPTIONS):
   - يجب أن تكون الخيارات الثلاثة (option_a, option_b, option_c) متنوعة ومختلفة تماماً في صنف البروتين أو صنف النشويات الرئيسي.
3. عدم تكرار الأصناف داخل الخيار الواحد (NO DUPLICATES):
   - يمنع تكرار نفس الصنف أكثر من مرة داخل الخيار الواحد. اكتب الصنف مرة واحدة فقط بوزنه الإجمالي.
4. هيكل الوجبة المتوازن (BALANCED STRUCTURE):
   - وجبة الغداء والعشاء: صنف بروتين رئيسي واحد + صنف نشويات رئيسي واحد + 1-2 صنف خضار أو سلطة.
   - وجبة الإفطار: أطعمة إفطار تقليدية (بيض/جبنة/فول/شوفان/خبز/حليب). ممنوع اللحوم والدواجن والأسماك في الإفطار.
   - وجبة السناك: خفيفة وسهلة التناول (فاكهة/مكسرات/زبادي/تمر). ممنوع اللحوم والدواجن والأسماك في السناك.
5. الدقة والمخرجات:
   - احسب القيم الغذائية لكل صنف: القيمة_لكل_100جم × الوزن_المُعطى / 100.
   - أعد فقط كائن JSON يحتوي على الخيارات الثلاثة بدون أي نص إضافي.
"""


def _format_food_catalog(foods: list[ParquetFoodItem]) -> str:
    """
    Render the parquet food list as a structured Arabic-readable catalog.

    Each row shows:
      arabic_name | english_name | per-100g macros | typical serving | food_group | best_with pairings
    """
    if not foods:
        return "لا توجد أطعمة متاحة في القائمة."

    lines: list[str] = []
    lines.append(
        "الرقم | الاسم بالعربية | الاسم بالإنجليزية | سعرات/100ج | بروتين/100ج | كارب/100ج | دهون/100ج | ألياف/100ج | الحصة المعتادة | مجموعة الطعام | best_with"
    )
    lines.append("─" * 120)

    for idx, food in enumerate(foods, start=1):
        best_with_str = " / ".join(food.best_with[:3]) if food.best_with else "—"
        arabic_name = food.food_name_ar if food.food_name_ar else food.food_name_en
        lines.append(
            f"{idx:2d}. {arabic_name:<28} | {food.food_name_en:<28} | "
            f"{food.calories:6.1f} kcal | P={food.protein:5.1f}g | C={food.carbs:5.1f}g | "
            f"F={food.fat:5.1f}g | Fiber={food.fiber:4.1f}g | "
            f"حصة≈{food.serving_weight_g:.0f}ج ({food.serving_name}) | "
            f"{food.food_group} | {best_with_str}"
        )

    return "\n".join(lines)


USER_PROMPT_SLOT_PARQUET_TEMPLATE = """\
اسم الوجبة: {meal_name}

الأهداف الغذائية لهذه الوجبة (لكل خيار من الخيارات الثلاثة):
- السعرات الحرارية: {target_calories:.0f} سعرة حرارية
- البروتين: {target_protein_g:.1f} جرام
- الكربوهيدرات: {target_carbs_g:.1f} جرام
- الدهون: {target_fat_g:.1f} جرام

معلومات المستخدم:
- الهدف: {goal}
- نوع النظام الغذائي: {diet_type}
- التفضيلات: {preferences}
- الحساسية (يجب تجنبها تماماً): {allergies}

=== الأطعمة المتاحة (اختر منها فقط) ===
{food_catalog}
=== نهاية القائمة ===

تذكر:
- أنشئ 3 خيارات متنوعة ومختلفة (option_a, option_b, option_c) تحقق نفس الهدف الغذائي.
- صنف بروتين رئيسي واحد فقط لكل خيار (لا تخلط فراخ مع سمك أو لحمة!).
- لا تكرر الصنف نفسه داخل الخيار الواحد.

أعد كائن JSON بهذا الهيكل بالضبط (استخدم arabic_name للاسم):
{{
  "slot_name": "{meal_name}",
  "option_a": {{
    "foods": [
      {{"name": "<اسم الطعام بالعربية من القائمة>", "serving_grams": <float>, "calories": <float>, "protein_g": <float>, "carbs_g": <float>, "fat_g": <float>}}
    ],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "option_b": {{
    "foods": [
      {{"name": "<اسم طعام آخر بالعربية من القائمة>", "serving_grams": <float>, "calories": <float>, "protein_g": <float>, "carbs_g": <float>, "fat_g": <float>}}
    ],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "option_c": {{
    "foods": [
      {{"name": "<اسم طعام ثالث بالعربية من القائمة>", "serving_grams": <float>, "calories": <float>, "protein_g": <float>, "carbs_g": <float>, "fat_g": <float>}}
    ],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }}
}}
"""
