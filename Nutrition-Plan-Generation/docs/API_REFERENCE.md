# Nutrition AI — API Reference

> **Base URL:** `http://<host>:8000`  
> **API Version:** `v1`  
> **Content-Type:** `application/json`  

---

## Overview

The Nutrition AI service is a **multi-agent LangGraph pipeline** that accepts a user biometrics profile and generates a fully validated, clinical nutrition plan. The pipeline runs asynchronously: you **start** a run, **stream** live progress via SSE, then **fetch** the final result when complete.

### Typical Integration Flow

```
1. POST /api/v1/nutrition/generate          → { run_id }
2. GET  /api/v1/nutrition/stream/{run_id}    → SSE events (live execution progress)
3. GET  /api/v1/nutrition/result/{run_id}    → Complete JSON NutritionPlanResponse
```

---

## Endpoints Summary

### 1. Health Check
```
GET /health
GET /api/v1/health
```
**Response 200**
```json
{ "status": "healthy" }
```

---

### 2. Start Nutrition Plan Generation
```
POST /api/v1/nutrition/generate
```
**Request body:** `GenerateNutritionRequest` (JSON)  
**Response 202** – `StartResponse` containing a `run_id` to track generation.

---

### 3. Stream Agent Progress (SSE)
```
GET /api/v1/nutrition/stream/{run_id}
```
Opens a **Server-Sent Events** connection. Each event is a JSON `StreamEvent` prefixed with `data:`.

#### SSE Event Example
```
data: {"run_id":"b7ada077-a320-4b8e-80a6-8d72691454b5","node":"profile","status":"started","progress":10,"message":null,"duration_ms":null,"reason":null}

data: {"run_id":"b7ada077-a320-4b8e-80a6-8d72691454b5","node":"profile","status":"completed","progress":10,"message":"Profile processed","duration_ms":1240,"reason":null}
```

---

### 4. Get Final Result
```
GET /api/v1/nutrition/result/{run_id}
GET /api/v1/nutrition/{run_id}   # alias
```
Returns `NutritionPlanResponse` (200) or 404 while still running.

---

### 5. List All Past Plans
```
GET /api/v1/nutrition/history
```
Returns an `APIResponse` object containing an array of completed plans kept in memory.

---

### 6. Delete a Plan
```
DELETE /api/v1/nutrition/{run_id}
```
Removes a stored plan from memory.

---

## Request Schema

### `GenerateNutritionRequest`
| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `age` | integer | ✅ | — | Age in years (10–100) |
| `gender` | `Gender` | ✅ | — | `male` or `female` |
| `height_cm` | float | ✅ | — | Height in cm (100–250) |
| `weight_kg` | float | ✅ | — | Weight in kg (30–300) |
| `goal` | `Goal` | ✅ | — | Fitness goal |
| `activity_level` | `ActivityLevel` | ❌ | `moderate` | Physical activity level |
| `diet_type` | `DietType` | ❌ | `normal` | Dietary pattern |
| `preferences` | string[] | ❌ | `[]` | Preferred foods |
| `allergies` | string[] | ❌ | `[]` | Foods to avoid |
| `additional_notes` | string\|null | ❌ | `null` | Free-text clinical notes |
| `meal_generation_mode` | `MealGenerationMode` | ❌ | `llm_arabic` | `llm_arabic` [DEFAULT], `llm_arabic_parquet`, or `dataset` |

---

## Enum Values

### `Goal`
- `fat_loss` (-500 kcal)
- `weight_loss` (-500 kcal)
- `muscle_gain` (+300 kcal)
- `bulking` (+500 kcal)
- `maintenance` (0 kcal)
- `recomposition` (0 kcal)

### `Gender`
- `male`, `female`

### `ActivityLevel`
- `sedentary` (x1.2)
- `lightly_active` (x1.375)
- `moderate` (x1.55)
- `very_active` (x1.725)
- `extra_active` (x1.9)

### `DietType`
- `normal`, `vegetarian`, `vegan`, `keto`, `high_protein`

### `MealGenerationMode`
- `dataset`: Egyptian Excel Food DB + English LLM composition (returns single `meal_plan`).
- `llm_arabic`: Free-form Arabic LLM generation (returns `triple_meal_plan` with 3 options: `option_a`, `option_b`, `option_c`).
- `llm_arabic_parquet`: **(Recommended)** Real Egyptian foods filtered from `foods_master_final.parquet` (793 foods) per slot + Arabic LLM (returns `triple_meal_plan` with 3 options).

---

## Full Response JSON Schema & Examples

The backend team can use the exact JSON samples below to predict and map the API outputs.

### Example A: Triple Option Response (`llm_arabic` & `llm_arabic_parquet` modes)

When `meal_generation_mode` is `llm_arabic` or `llm_arabic_parquet`, the API populates `triple_meal_plan` with 3 complete meal options (`option_a`, `option_b`, `option_c`) along with the `meal_distribution` target budgets.

```json
{
  "run_id": "e08dff61-c104-4c70-996f-849981e1d4a5",
  "success": true,
  "calories_result": {
    "bmr": 1810.0,
    "tdee": 2805.5,
    "target_calories": 2305.5,
    "formula_used": "Mifflin-St Jeor",
    "goal": "fat_loss",
    "activity_level": "moderate",
    "weight_kg": 80.0,
    "goal_adjustment_kcal": -500
  },
  "macro_result": {
    "target_calories": 2305.5,
    "protein_g": 201.7,
    "carbs_g": 201.7,
    "fat_g": 76.9,
    "goal": "fat_loss",
    "weight_kg": 80.0,
    "protein_per_kg": 2.2,
    "diet_type": "normal",
    "preferences": ["chicken"],
    "allergies": []
  },
  "meal_plan": {
    "breakfast": {
      "meal_name": "الإفطار",
      "foods": [
        {
          "name": "جبنة بيضاء نصف دسم",
          "serving_grams": 150.0,
          "calories": 180.0,
          "protein_g": 24.0,
          "carbs_g": 3.0,
          "fat_g": 9.0
        },
        {
          "name": "عيش بلدي",
          "serving_grams": 100.0,
          "calories": 250.0,
          "protein_g": 8.0,
          "carbs_g": 50.0,
          "fat_g": 1.5
        }
      ],
      "total_calories": 430.0,
      "total_protein_g": 32.0,
      "total_carbs_g": 53.0,
      "total_fat_g": 10.5
    },
    "lunch": {
      "meal_name": "الغداء",
      "foods": [
        {
          "name": "صدر فراخ مشوي",
          "serving_grams": 250.0,
          "calories": 412.5,
          "protein_g": 77.5,
          "carbs_g": 0.0,
          "fat_g": 9.0
        },
        {
          "name": "أرز أبيض مطبوخ",
          "serving_grams": 200.0,
          "calories": 260.0,
          "protein_g": 5.4,
          "carbs_g": 56.0,
          "fat_g": 0.6
        },
        {
          "name": "سلطة خضراء",
          "serving_grams": 150.0,
          "calories": 37.5,
          "protein_g": 1.5,
          "carbs_g": 7.5,
          "fat_g": 0.3
        }
      ],
      "total_calories": 710.0,
      "total_protein_g": 84.4,
      "total_carbs_g": 63.5,
      "total_fat_g": 9.9
    },
    "dinner": {
      "meal_name": "العشاء",
      "foods": [
        {
          "name": "فيليه سمك بلطي مشوي",
          "serving_grams": 250.0,
          "calories": 320.0,
          "protein_g": 65.0,
          "carbs_g": 0.0,
          "fat_g": 6.5
        },
        {
          "name": "بطاطس مسلوقة",
          "serving_grams": 200.0,
          "calories": 174.0,
          "protein_g": 4.0,
          "carbs_g": 40.0,
          "fat_g": 0.2
        }
      ],
      "total_calories": 494.0,
      "total_protein_g": 69.0,
      "total_carbs_g": 40.0,
      "total_fat_g": 6.7
    },
    "snack": {
      "meal_name": "السناك",
      "foods": [
        {
          "name": "تفاح",
          "serving_grams": 150.0,
          "calories": 78.0,
          "protein_g": 0.4,
          "carbs_g": 21.0,
          "fat_g": 0.3
        },
        {
          "name": "لوز raw",
          "serving_grams": 25.0,
          "calories": 145.0,
          "protein_g": 5.2,
          "carbs_g": 5.4,
          "fat_g": 12.5
        }
      ],
      "total_calories": 223.0,
      "total_protein_g": 5.6,
      "total_carbs_g": 26.4,
      "total_fat_g": 12.8
    },
    "total_daily_calories": 1857.0,
    "total_daily_protein_g": 191.0,
    "total_daily_carbs_g": 182.9,
    "total_daily_fat_g": 39.9,
    "notes": null
  },
  "triple_meal_plan": {
    "option_a": {
      "breakfast": {
        "meal_name": "الإفطار",
        "foods": [
          { "name": "جبنة بيضاء نصف دسم", "serving_grams": 150.0, "calories": 180.0, "protein_g": 24.0, "carbs_g": 3.0, "fat_g": 9.0 },
          { "name": "عيش بلدي", "serving_grams": 100.0, "calories": 250.0, "protein_g": 8.0, "carbs_g": 50.0, "fat_g": 1.5 }
        ],
        "total_calories": 430.0, "total_protein_g": 32.0, "total_carbs_g": 53.0, "total_fat_g": 10.5
      },
      "lunch": {
        "meal_name": "الغداء",
        "foods": [
          { "name": "صدر فراخ مشوي", "serving_grams": 250.0, "calories": 412.5, "protein_g": 77.5, "carbs_g": 0.0, "fat_g": 9.0 },
          { "name": "أرز أبيض مطبوخ", "serving_grams": 200.0, "calories": 260.0, "protein_g": 5.4, "carbs_g": 56.0, "fat_g": 0.6 },
          { "name": "سلطة خضراء", "serving_grams": 150.0, "calories": 37.5, "protein_g": 1.5, "carbs_g": 7.5, "fat_g": 0.3 }
        ],
        "total_calories": 710.0, "total_protein_g": 84.4, "total_carbs_g": 63.5, "total_fat_g": 9.9
      },
      "dinner": {
        "meal_name": "العشاء",
        "foods": [
          { "name": "فيليه سمك بلطي مشوي", "serving_grams": 250.0, "calories": 320.0, "protein_g": 65.0, "carbs_g": 0.0, "fat_g": 6.5 },
          { "name": "بطاطس مسلوقة", "serving_grams": 200.0, "calories": 174.0, "protein_g": 4.0, "carbs_g": 40.0, "fat_g": 0.2 }
        ],
        "total_calories": 494.0, "total_protein_g": 69.0, "total_carbs_g": 40.0, "total_fat_g": 6.7
      },
      "snack": {
        "meal_name": "السناك",
        "foods": [
          { "name": "تفاح", "serving_grams": 150.0, "calories": 78.0, "protein_g": 0.4, "carbs_g": 21.0, "fat_g": 0.3 },
          { "name": "لوز raw", "serving_grams": 25.0, "calories": 145.0, "protein_g": 5.2, "carbs_g": 5.4, "fat_g": 12.5 }
        ],
        "total_calories": 223.0, "total_protein_g": 5.6, "total_carbs_g": 26.4, "total_fat_g": 12.8
      },
      "total_daily_calories": 1857.0,
      "total_daily_protein_g": 191.0,
      "total_daily_carbs_g": 182.9,
      "total_daily_fat_g": 39.9,
      "notes": null
    },
    "option_b": {
      "breakfast": {
        "meal_name": "الإفطار",
        "foods": [
          { "name": "بيض مسلوق", "serving_grams": 150.0, "calories": 232.5, "protein_g": 19.5, "carbs_g": 1.6, "fat_g": 16.5 },
          { "name": "شوفان مع حليب", "serving_grams": 200.0, "calories": 200.0, "protein_g": 10.0, "carbs_g": 32.0, "fat_g": 3.5 }
        ],
        "total_calories": 432.5, "total_protein_g": 29.5, "total_carbs_g": 33.6, "total_fat_g": 20.0
      },
      "lunch": {
        "meal_name": "الغداء",
        "foods": [
          { "name": "فيليه سمك بلطي مشوي", "serving_grams": 300.0, "calories": 384.0, "protein_g": 78.0, "carbs_g": 0.0, "fat_g": 7.8 },
          { "name": "بطاطس مسلوقة", "serving_grams": 250.0, "calories": 217.5, "protein_g": 5.0, "carbs_g": 50.0, "fat_g": 0.25 },
          { "name": "سلطة طماطم وخيار", "serving_grams": 150.0, "calories": 30.0, "protein_g": 1.2, "carbs_g": 6.0, "fat_g": 0.2 }
        ],
        "total_calories": 631.5, "total_protein_g": 84.2, "total_carbs_g": 56.0, "total_fat_g": 8.25
      },
      "dinner": {
        "meal_name": "العشاء",
        "foods": [
          { "name": "لحم بقري مطبوخ", "serving_grams": 220.0, "calories": 440.0, "protein_g": 61.6, "carbs_g": 0.0, "fat_g": 21.0 },
          { "name": "أرز أبيض مطبوخ", "serving_grams": 150.0, "calories": 195.0, "protein_g": 4.0, "carbs_g": 42.0, "fat_g": 0.5 }
        ],
        "total_calories": 635.0, "total_protein_g": 65.6, "total_carbs_g": 42.0, "total_fat_g": 21.5
      },
      "snack": {
        "meal_name": "السناك",
        "foods": [
          { "name": "موز", "serving_grams": 120.0, "calories": 106.8, "protein_g": 1.3, "carbs_g": 27.4, "fat_g": 0.4 },
          { "name": "زبادي سادة", "serving_grams": 150.0, "calories": 90.0, "protein_g": 7.5, "carbs_g": 9.0, "fat_g": 3.0 }
        ],
        "total_calories": 196.8, "total_protein_g": 8.8, "total_carbs_g": 36.4, "total_fat_g": 3.4
      },
      "total_daily_calories": 1895.8,
      "total_daily_protein_g": 188.1,
      "total_daily_carbs_g": 168.0,
      "total_daily_fat_g": 53.15,
      "notes": null
    },
    "option_c": {
      "breakfast": {
        "meal_name": "الإفطار",
        "foods": [
          { "name": "فول مدمس", "serving_grams": 200.0, "calories": 196.0, "protein_g": 11.2, "carbs_g": 35.0, "fat_g": 1.2 },
          { "name": "عيش بلدي", "serving_grams": 100.0, "calories": 250.0, "protein_g": 8.0, "carbs_g": 50.0, "fat_g": 1.5 }
        ],
        "total_calories": 446.0, "total_protein_g": 19.2, "total_carbs_g": 85.0, "total_fat_g": 2.7
      },
      "lunch": {
        "meal_name": "الغداء",
        "foods": [
          { "name": "لحم بقري مطبوخ", "serving_grams": 250.0, "calories": 500.0, "protein_g": 70.0, "carbs_g": 0.0, "fat_g": 24.0 },
          { "name": "أرز أبيض مطبوخ", "serving_grams": 200.0, "calories": 260.0, "protein_g": 5.4, "carbs_g": 56.0, "fat_g": 0.6 }
        ],
        "total_calories": 760.0, "total_protein_g": 75.4, "total_carbs_g": 56.0, "total_fat_g": 24.6
      },
      "dinner": {
        "meal_name": "العشاء",
        "foods": [
          { "name": "صدر فراخ مشوي", "serving_grams": 220.0, "calories": 363.0, "protein_g": 68.2, "carbs_g": 0.0, "fat_g": 7.9 },
          { "name": "بطاطس مسلوقة", "serving_grams": 200.0, "calories": 174.0, "protein_g": 4.0, "carbs_g": 40.0, "fat_g": 0.2 }
        ],
        "total_calories": 537.0, "total_protein_g": 72.2, "total_carbs_g": 40.0, "total_fat_g": 8.1
      },
      "snack": {
        "meal_name": "السناك",
        "foods": [
          { "name": "تمرة ناشفة", "serving_grams": 50.0, "calories": 138.0, "protein_g": 1.2, "carbs_g": 37.5, "fat_g": 0.2 },
          { "name": "لوز raw", "serving_grams": 20.0, "calories": 116.0, "protein_g": 4.2, "carbs_g": 4.3, "fat_g": 10.0 }
        ],
        "total_calories": 254.0, "total_protein_g": 5.4, "total_carbs_g": 41.8, "total_fat_g": 10.2
      },
      "total_daily_calories": 1997.0,
      "total_daily_protein_g": 172.2,
      "total_daily_carbs_g": 222.8,
      "total_daily_fat_g": 45.6,
      "notes": null
    },
    "meal_distribution": {
      "breakfast": {
        "meal_name": "الإفطار",
        "slot_key": "breakfast",
        "target_calories": 576.4,
        "target_protein_g": 50.4,
        "target_carbs_g": 50.4,
        "target_fat_g": 19.2
      },
      "lunch": {
        "meal_name": "الغداء",
        "slot_key": "lunch",
        "target_calories": 806.9,
        "target_protein_g": 70.6,
        "target_carbs_g": 70.6,
        "target_fat_g": 26.9
      },
      "dinner": {
        "meal_name": "العشاء",
        "slot_key": "dinner",
        "target_calories": 691.7,
        "target_protein_g": 60.5,
        "target_carbs_g": 60.5,
        "target_fat_g": 23.1
      },
      "snack": {
        "meal_name": "السناك",
        "slot_key": "snack",
        "target_calories": 230.5,
        "target_protein_g": 20.2,
        "target_carbs_g": 20.2,
        "target_fat_g": 7.7
      },
      "total_calories": 2305.5
    },
    "notes": null
  },
  "validation_report": {
    "passed": true,
    "issues": [],
    "calorie_deviation_pct": -3.2,
    "protein_deviation_pct": -5.3,
    "carbs_deviation_pct": -9.3,
    "fat_deviation_pct": -48.1
  },
  "explanation": {
    "summary": "خطة غذائية متكاملة تعتمد على تقليل السعرات الحرارية بنسبة مناسبة للتخسيس مع الحفاظ على الكتلة العضلية.",
    "calorie_rationale": "تم تحديد 2305 سعرة حرارية بخصم 500 سعرة من الاحتياج اليومي لضمان خسارة الدهون بأمان.",
    "macro_rationale": "تم اختيار نسبة بروتين مرتفعة (2.2g لكل كجم) لحماية العضلات أثناء العجز السعري.",
    "food_selection_rationale": "تم اختيار أطعمة مصرية حقيقية ومتنوعة عبر الخيارات الثلاثة لضمان الالتزام والاستمتاع.",
    "adherence_tips": [
      "احرص على شرب 3 لتر ماء يومياً.",
      "زن الأطعمة قبل الطهي للحصول على أعلى دقة."
    ]
  },
  "retry_count": 0,
  "error": null
}
```

---

### Example B: Single Plan Response (`dataset` mode)

When `meal_generation_mode` is `dataset`, `triple_meal_plan` is `null` and only `meal_plan` is returned:

```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "success": true,
  "calories_result": {
    "bmr": 1780.0,
    "tdee": 2759.0,
    "target_calories": 2259.0,
    "formula_used": "Mifflin-St Jeor",
    "goal": "fat_loss",
    "activity_level": "moderate",
    "weight_kg": 76.0,
    "goal_adjustment_kcal": -500
  },
  "macro_result": {
    "target_calories": 2259.0,
    "protein_g": 197.7,
    "carbs_g": 197.7,
    "fat_g": 75.3,
    "goal": "fat_loss",
    "weight_kg": 76.0,
    "protein_per_kg": 2.2,
    "diet_type": "normal",
    "preferences": [],
    "allergies": []
  },
  "meal_plan": {
    "breakfast": {
      "meal_name": "Breakfast",
      "foods": [
        { "name": "eggs, whole", "serving_grams": 150.0, "calories": 214.5, "protein_g": 18.9, "carbs_g": 1.1, "fat_g": 14.2 },
        { "name": "oats", "serving_grams": 60.0, "calories": 233.4, "protein_g": 10.1, "carbs_g": 40.6, "fat_g": 4.1 }
      ],
      "total_calories": 447.9, "total_protein_g": 29.0, "total_carbs_g": 41.7, "total_fat_g": 18.3
    },
    "lunch": {
      "meal_name": "Lunch",
      "foods": [
        { "name": "chicken breast, grilled", "serving_grams": 250.0, "calories": 412.5, "protein_g": 77.5, "carbs_g": 0.0, "fat_g": 9.0 },
        { "name": "rice, white", "serving_grams": 200.0, "calories": 260.0, "protein_g": 5.4, "carbs_g": 56.0, "fat_g": 0.6 }
      ],
      "total_calories": 672.5, "total_protein_g": 82.9, "total_carbs_g": 56.0, "total_fat_g": 9.6
    },
    "dinner": {
      "meal_name": "Dinner",
      "foods": [
        { "name": "tilapia fillet", "serving_grams": 250.0, "calories": 320.0, "protein_g": 65.0, "carbs_g": 0.0, "fat_g": 6.5 },
        { "name": "potatoes, boiled", "serving_grams": 200.0, "calories": 174.0, "protein_g": 4.0, "carbs_g": 40.0, "fat_g": 0.2 }
      ],
      "total_calories": 494.0, "total_protein_g": 69.0, "total_carbs_g": 40.0, "total_fat_g": 6.7
    },
    "snack": {
      "meal_name": "Snack",
      "foods": [
        { "name": "apples", "serving_grams": 150.0, "calories": 78.0, "protein_g": 0.4, "carbs_g": 21.0, "fat_g": 0.3 }
      ],
      "total_calories": 78.0, "total_protein_g": 0.4, "total_carbs_g": 21.0, "total_fat_g": 0.3
    },
    "total_daily_calories": 1692.4,
    "total_daily_protein_g": 181.3,
    "total_daily_carbs_g": 158.7,
    "total_daily_fat_g": 34.9,
    "notes": null
  },
  "triple_meal_plan": null,
  "validation_report": {
    "passed": true,
    "issues": [],
    "calorie_deviation_pct": -25.1,
    "protein_deviation_pct": -8.3,
    "carbs_deviation_pct": -19.7,
    "fat_deviation_pct": -53.6
  },
  "explanation": {
    "summary": "Single plan generated using the Excel dataset.",
    "calorie_rationale": "Calorie target set at 2259 kcal.",
    "macro_rationale": "Macros split for fat loss.",
    "food_selection_rationale": "Selected foods from Excel DB.",
    "adherence_tips": ["Drink water regularly."]
  },
  "retry_count": 0,
  "error": null
}
```

---

## Error Responses
| HTTP | Situation | Body Example |
|------|-----------|--------------|
| `202` | Generation started | `{ "run_id": "...", "status": "started", "message": "..." }` |
| `404` | `run_id` not found or still running | `{ "detail": "Result not ready yet. Please wait for completion." }` |
| `422` | Request validation failed | `{ "detail": [ { "loc": ["body", "age"], "msg": "value is not a valid integer", "type": "type_error.integer" } ] }` |
| `500` | Internal server error | `{ "detail": "Nutrition plan generation failed after 3 attempts: ..." }` |

---

## Usage Examples

### cURL (start → stream → result)
```bash
# 1. Start generation
RUN_ID=$(curl -s -X POST http://localhost:8000/api/v1/nutrition/generate \
  -H "Content-Type: application/json" \
  -d '{"age":28,"gender":"male","height_cm":178,"weight_kg":82,"goal":"fat_loss","activity_level":"moderate","diet_type":"normal","preferences":["chicken"],"allergies":[],"meal_generation_mode":"llm_arabic_parquet"}' | jq -r .run_id)

echo "Run ID: $RUN_ID"

# 2. Stream SSE events until completed
curl -N http://localhost:8000/api/v1/nutrition/stream/$RUN_ID

# 3. Fetch final JSON result
curl http://localhost:8000/api/v1/nutrition/result/$RUN_ID | jq .
```

### Python (httpx)
```python
import httpx, json

BASE = "http://localhost:8000"

# 1. Start run
resp = httpx.post(f"{BASE}/api/v1/nutrition/generate", json={
    "age": 30, "gender": "male", "height_cm": 178, "weight_kg": 80,
    "goal": "fat_loss", "activity_level": "moderate", "diet_type": "normal",
    "meal_generation_mode": "llm_arabic_parquet"
})
run_id = resp.json()["run_id"]
print("Started run:", run_id)

# 2. Listen to SSE stream
with httpx.stream("GET", f"{BASE}/api/v1/nutrition/stream/{run_id}") as stream:
    for line in stream.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            print(f"[{event['node']}] {event['status']} {event['progress']}%")
            if event["node"] == "completed":
                break

# 3. Fetch final JSON result
result = httpx.get(f"{BASE}/api/v1/nutrition/result/{run_id}").json()

# Access Option A
option_a = result["triple_meal_plan"]["option_a"]
print(f"Option A Total Kcal: {option_a['total_daily_calories']} kcal")

# Access Option B & C
option_b = result["triple_meal_plan"]["option_b"]
option_c = result["triple_meal_plan"]["option_c"]
```

---

## Integration Guidelines for Backend & Mobile Teams

1. **Check `meal_generation_mode`**:
   - For `llm_arabic_parquet` or `llm_arabic` → parse `triple_meal_plan.option_a`, `option_b`, `option_c`.
   - For `dataset` → parse `meal_plan`.
2. **Food Item Properties**:
   Each item in `foods` contains: `name`, `serving_grams`, `calories`, `protein_g`, `carbs_g`, `fat_g`.
3. **Arabic Text Encoding**:
   The API returns UTF-8 encoded Arabic strings (e.g. `"جبنة بيضاء"`, `"فيليه سمك بلطي مشوي"`). Ensure JSON parsers do not escape UTF-8 strings.
