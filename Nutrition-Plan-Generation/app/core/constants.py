"""Application-wide constants used across calculators, validation, and agents."""

# ─── Activity Level Multipliers (TDEE = BMR × multiplier) ────────────────────
ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderate": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

# ─── Goal Calorie Adjustments (kcal/day relative to TDEE) ────────────────────
GOAL_CALORIE_ADJUSTMENTS: dict[str, int] = {
    "fat_loss": -500,
    "weight_loss": -500,
    "muscle_gain": +300,
    "bulking": +500,
    "maintenance": 0,
    "recomposition": 0,
}

# ─── Macro Ratios by Goal (protein_ratio, fat_ratio, carb_ratio) ──────────────
# Ratios are as a fraction of total daily calories
MACRO_RATIOS: dict[str, dict[str, float]] = {
    "fat_loss": {
        "protein": 0.35,
        "fat": 0.30,
        "carbs": 0.35,
        "protein_g_per_kg": 2.2,   # higher protein to preserve muscle
    },
    "weight_loss": {
        "protein": 0.35,
        "fat": 0.30,
        "carbs": 0.35,
        "protein_g_per_kg": 2.0,
    },
    "muscle_gain": {
        "protein": 0.30,
        "fat": 0.25,
        "carbs": 0.45,
        "protein_g_per_kg": 2.0,
    },
    "bulking": {
        "protein": 0.25,
        "fat": 0.25,
        "carbs": 0.50,
        "protein_g_per_kg": 1.8,
    },
    "maintenance": {
        "protein": 0.25,
        "fat": 0.30,
        "carbs": 0.45,
        "protein_g_per_kg": 1.6,
    },
    "recomposition": {
        "protein": 0.35,
        "fat": 0.30,
        "carbs": 0.35,
        "protein_g_per_kg": 2.0,
    },
}

# ─── Caloric Values per Gram ──────────────────────────────────────────────────
KCAL_PER_G_PROTEIN: float = 4.0
KCAL_PER_G_CARBS: float = 4.0
KCAL_PER_G_FAT: float = 9.0

# ─── Validation Tolerances ───────────────────────────────────────────────────
# Acceptable deviation from target macro values
CALORIE_TOLERANCE_PCT: float = 0.10   # ±10%
PROTEIN_TOLERANCE_PCT: float = 0.15   # ±15%
CARBS_TOLERANCE_PCT: float = 0.15     # ±15%
FAT_TOLERANCE_PCT: float = 0.20       # ±20%

# ─── Food Retrieval Settings ──────────────────────────────────────────────────
MAX_CANDIDATE_FOODS: int = 30          # total foods sent to Meal Composition Agent

# ─── Meal Distribution (% of daily calories per meal) ────────────────────────
MEAL_DISTRIBUTION: dict[str, float] = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.30,
    "snack": 0.10,
}

# ─── Food Group Tags (used for enrichment) ───────────────────────────────────
PROTEIN_KEYWORDS = [
    "chicken", "beef", "fish", "lamb", "turkey", "eggs", "egg",
    "shrimp", "tuna", "salmon", "sardine", "liver", "meat", "kofta",
    "kebab", "shawarma", "lentil", "bean", "beans", "hummus", "foul",
    "ful", "tofu", "cheese", "yogurt",
]

CARB_KEYWORDS = [
    "rice", "bread", "pasta", "potato", "sweet potato", "corn", "oat",
    "cereal", "pita", "flatbread", "noodle", "couscous", "quinoa",
    "tortilla", "crackers", "barley", "wheat",
]

VEGETABLE_KEYWORDS = [
    "tomato", "cucumber", "lettuce", "spinach", "broccoli", "cauliflower",
    "carrot", "pepper", "onion", "zucchini", "eggplant", "peas", "green",
    "beans", "cabbage", "celery", "kale", "mushroom", "beetroot",
]

FRUIT_KEYWORDS = [
    "apple", "banana", "orange", "grape", "mango", "watermelon", "melon",
    "strawberry", "peach", "apricot", "pomegranate", "guava", "fig",
    "date", "lemon", "pear", "plum",
]

DAIRY_KEYWORDS = [
    "milk", "yogurt", "cheese", "cream", "butter", "labneh", "kefir",
    "custard", "ice cream",
]

FAT_KEYWORDS = [
    "oil", "olive oil", "nuts", "almond", "walnut", "peanut", "cashew",
    "avocado", "tahini", "sesame", "seed", "coconut",
]

# ─── Allergen Keywords ────────────────────────────────────────────────────────
ALLERGEN_MAP: dict[str, list[str]] = {
    "gluten": ["wheat", "bread", "pasta", "flour", "barley", "rye", "pita", "crackers"],
    "dairy": ["milk", "cheese", "yogurt", "butter", "cream", "labneh", "lactose"],
    "nuts": ["almond", "walnut", "cashew", "pecan", "pistachio", "hazelnut"],
    "peanuts": ["peanut", "groundnut"],
    "eggs": ["egg", "eggs"],
    "fish": ["fish", "tuna", "salmon", "sardine", "tilapia", "bass", "cod"],
    "shellfish": ["shrimp", "prawn", "crab", "lobster"],
    "soy": ["soy", "tofu", "edamame"],
}
