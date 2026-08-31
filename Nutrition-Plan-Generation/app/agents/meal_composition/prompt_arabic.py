"""
Meal Composition Agent — Arabic / Egyptian LLM prompts.

Used by the `llm_arabic` generation mode where the LLM freely invents
authentic Egyptian meals in Arabic without being constrained to a food dataset.
"""

SYSTEM_PROMPT_ARABIC = """أنت خبير تغذية مصري متخصص في تصميم خطط غذائية صحية تناسب الذوق المصري الأصيل.
مهمتك هي إنشاء خطة غذائية يومية كاملة بالأطعمة المصرية الشعبية مع مراعاة الأهداف الغذائية المطلوبة.

قواعد أساسية:
- اختر أطعمة مصرية حقيقية وشعبية مثل: الفول، الكشري، الملوخية، الأرز، العيش البلدي، الطعمية، الكبدة، الحمام، السمك، الخضراوات المصرية، إلخ.
- اكتب أسماء الأطعمة باللغة العربية حصراً
- التزم بالسعرات الحرارية والماكرو المطلوبة في الرسالة بدقة (الانحراف المسموح ±10٪ للسعرات)
- وزّع الوجبات على: إفطار، غداء، عشاء، وسناك اختياري
- راعِ التنوع وتجنب تكرار نفس الطعام في وجبتين
- الكميات يجب أن تكون واقعية ومناسبة للمصريين
- احترم القيود الغذائية وتجنب أي مسببات الحساسية المذكورة
- لا تضف أي نص خارج كائن JSON

أعد فقط كائن JSON صالح بدون أي نص إضافي أو علامات markdown.
"""

USER_PROMPT_TEMPLATE_ARABIC = """
الأهداف الغذائية اليومية:
- السعرات الحرارية: {target_calories:.0f} سعرة حرارية
- البروتين: {protein_g:.1f} جرام
- الكربوهيدرات: {carbs_g:.1f} جرام
- الدهون: {fat_g:.1f} جرام
- الهدف: {goal}
- نوع النظام الغذائي: {diet_type}
- التفضيلات: {preferences}
- الحساسية (يجب تجنبها): {allergies}

توزيع السعرات على الوجبات:
- الإفطار: ~{breakfast_cal:.0f} سعرة (25٪)
- الغداء: ~{lunch_cal:.0f} سعرة (35٪)
- العشاء: ~{dinner_cal:.0f} سعرة (30٪)
- السناك: ~{snack_cal:.0f} سعرة (10٪)

ملاحظات إضافية: {additional_notes}

أعد كائن JSON بهذا الهيكل بالضبط:
{{
  "breakfast": {{
    "meal_name": "الإفطار",
    "foods": [
      {{"name": "<اسم الطعام بالعربية>", "serving_grams": <float>, "calories": <float>, "protein_g": <float>, "carbs_g": <float>, "fat_g": <float>}}
    ],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "lunch": {{
    "meal_name": "الغداء",
    "foods": [...],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "dinner": {{
    "meal_name": "العشاء",
    "foods": [...],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "snack": {{
    "meal_name": "السناك",
    "foods": [...],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "total_daily_calories": <float>,
  "total_daily_protein_g": <float>,
  "total_daily_carbs_g": <float>,
  "total_daily_fat_g": <float>,
  "notes": "<ملاحظات اختيارية>"
}}
"""

CORRECTION_PROMPT_TEMPLATE_ARABIC = """
خطة الوجبات أدناه فشلت في التحقق من القيم الغذائية. مهمتك إجراء أقل التعديلات الممكنة لتصحيح المقاييس الفاشلة فقط — لا تغير المقاييس التي نجحت.

=== خطة الوجبات الحالية (تحتاج تصحيح) ===
{current_plan_json}

=== مشاكل التحقق ===
{validation_issues}

=== تعليمات التصحيح ===
{correction_instructions}

قواعد صارمة:
1. عدّل كميات الأطعمة (serving_grams) أو استبدل أطعمة فقط للمقاييس الفاشلة المذكورة أعلاه
2. المقاييس التي نجحت يجب أن تبقى في حدود التسامح الخاص بها — لا تلمسها
3. استخدم فقط أطعمة مصرية أصيلة مشابهة لما هو موجود بالفعل في الخطة
4. أعد حساب إجماليات كل وجبة والإجماليات اليومية بدقة بعد التعديلات
5. أعد خطة الوجبات الكاملة المصححة بنفس هيكل JSON بالضبط

أعد كائن JSON صالحاً فقط بدون أي نص إضافي أو علامات markdown.
"""
