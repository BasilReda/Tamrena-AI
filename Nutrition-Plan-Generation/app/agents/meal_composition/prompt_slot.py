"""
Per-Slot Meal Generation Prompt — Free-form Arabic / Egyptian mode.

Used by `agent_iterative.py`. For each slot (breakfast, lunch, dinner, snack),
a SINGLE LLM call returns Option A, Option B, and Option C together in one JSON structure.
Total LLM calls for the entire daily plan: 4 calls total.
"""

SYSTEM_PROMPT_SLOT = """أنت خبير تغذية مصري وطبيب متخصص في تصميم وجبات غذائية صحية ومتناسقة تناسب الذوق المصري الأصيل.
مهمتك هي إنشاء 3 خيارات مختلفة ومتنوعة (Option A, Option B, Option C) لوجبة واحدة محددة بالأطعمة المصرية الشعبية مع مراعاة الأهداف الغذائية المحددة لهذه الوجبة.

قواعد أساسية:
1. التنوع بين الخيارات الثلاثة (option_a, option_b, option_c):
   - اجعل الخيارات الثلاثة متنوعة ومختلفة في صنف المكون الرئيسي.
2. التوافق والتناسق الغذائي (CULINARY HARMONY):
   - اختر أطعمة مصرية حقيقية وشعبية متناسقة معاً (مثل: الفول، الكشري، الملوخية، الأرز، العيش البلدي، الطعمية، الكبدة، السمك، الخضراوات المصرية، إلخ).
   - في وجبة الغداء والعشاء: اختر مصدر بروتين رئيسي واحد فقط لكل خيار (لا تخلط بين الدجاج والسمك أو اللحم في نفس الخيار!).
   - وجبة الإفطار: أطعمة إفطار تقليدية (بيض/جبنة/فول/شوفان/خبز/حليب). ممنوع الدواجن واللحوم والأسماك في الإفطار.
   - وجبة السناك: خفيفة وسهلة التناول (فاكهة/مكسرات/زبادي/تمر). ممنوع الوجبات الثقيلة في السناك.
3. عدم تكرار الأصناف:
   - يمنع تكرار نفس الصنف داخل الخيار الواحد.
4. الدقة والمخرجات:
   - التزم بالسعرات الحرارية والماكرو المطلوبة بدقة (لكل خيار من الخيارات الثلاثة).
   - لا تضف أي نص خارج كائن JSON.

أعد فقط كائن JSON صالح بدون أي نص إضافي أو علامات markdown.
"""

USER_PROMPT_SLOT_TEMPLATE = """\
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

أعد كائن JSON بهذا الهيكل بالضبط:
{{
  "slot_name": "{meal_name}",
  "option_a": {{
    "foods": [
      {{"name": "<اسم الطعام بالعربية>", "serving_grams": <float>, "calories": <float>, "protein_g": <float>, "carbs_g": <float>, "fat_g": <float>}}
    ],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "option_b": {{
    "foods": [
      {{"name": "<اسم طعام آخر بالعربية>", "serving_grams": <float>, "calories": <float>, "protein_g": <float>, "carbs_g": <float>, "fat_g": <float>}}
    ],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }},
  "option_c": {{
    "foods": [
      {{"name": "<اسم طعام ثالث بالعربية>", "serving_grams": <float>, "calories": <float>, "protein_g": <float>, "carbs_g": <float>, "fat_g": <float>}}
    ],
    "total_calories": <float>,
    "total_protein_g": <float>,
    "total_carbs_g": <float>,
    "total_fat_g": <float>
  }}
}}
"""
