"""
Pandas-based filter functions for the food retrieval layer.
Each function takes a DataFrame and returns a filtered DataFrame.
No LLM is involved.
"""

import pandas as pd
from app.core.logging import get_logger

logger = get_logger(__name__)


def filter_by_allergens(df: pd.DataFrame, allergies: list[str]) -> pd.DataFrame:
    """Remove foods containing any of the user's allergens."""
    if not allergies:
        return df

    allergy_set = {a.lower() for a in allergies}

    def has_allergen(allergen_list: list[str]) -> bool:
        return any(a.lower() in allergy_set for a in allergen_list)

    mask = ~df["allergens"].apply(has_allergen)
    filtered = df[mask]
    logger.debug("Allergen filter: %d → %d foods", len(df), len(filtered))
    return filtered


# diet_types values the food dataset actually tags (see loader._detect_diet_types:
# every row gets "normal", plus "vegetarian"/"vegan" if its name has no meat/animal
# keywords).
#
# The value that actually reaches this function is NOT the raw request's
# DietType enum member — the Profile Agent (an LLM call, see
# agents/profile/prompt.py) re-normalises it first, into its own vocabulary of
# exactly "omnivore", "vegetarian", "vegan", or "keto" ("high_protein" and
# "normal" never survive that normalisation; a "High Protein" selection comes
# out as "omnivore"). None of "omnivore"/"keto" is ever a value the dataset
# tags foods with, so treating either as a hard tag filter matched zero rows
# every time, silently emptying the entire candidate pool. Macro-target
# fitting for "high protein"/"keto" goals already happens via
# ranking.score_foods's protein-density scoring, so all four non-restrictive
# spellings pass through unfiltered here rather than eliminating every
# candidate food. ("normal"/"high_protein" are kept too, defensively, in case
# a caller ever bypasses the Profile Agent's normalisation.)
_NON_RESTRICTIVE_DIET_TYPES = ("normal", "omnivore", "keto", "high_protein")


def filter_by_diet_type(df: pd.DataFrame, diet_type: str) -> pd.DataFrame:
    """Keep only foods compatible with the user's dietary pattern."""
    if not diet_type or diet_type.lower() in _NON_RESTRICTIVE_DIET_TYPES:
        return df

    if diet_type.lower() == "vegan":
        acceptable = {"vegan", "plant_based"}
    elif diet_type.lower() == "vegetarian":
        acceptable = {"vegetarian", "vegan", "plant_based"}
    else:
        acceptable = {diet_type.lower()}

    profile_col = "diet_types" if "diet_types" in df.columns else "diet_tags"
    mask = df[profile_col].apply(lambda d: any(tag in acceptable for tag in d))
    filtered = df[mask]
    logger.debug("Diet filter (%s): %d → %d foods", diet_type, len(df), len(filtered))
    return filtered


def filter_by_meal_type(df: pd.DataFrame, meal_type: str) -> pd.DataFrame:
    """Keep only foods tagged for this meal type."""
    meal_type = meal_type.lower()
    mask = df["meal_types"].apply(lambda m: meal_type in m)
    filtered = df[mask]
    # Fallback: if nothing survives, return unfiltered
    if filtered.empty:
        logger.warning("No foods found for meal_type=%s; relaxing filter", meal_type)
        return df
    return filtered


def filter_by_meal_slot_fit(df: pd.DataFrame, meal_slot: str) -> pd.DataFrame:
    """Keep only foods tagged for a specific meal slot fit."""
    meal_slot = meal_slot.lower()
    if "meal_slot_fit" not in df.columns:
        return df

    mask = df["meal_slot_fit"].apply(lambda slots: meal_slot in slots)
    filtered = df[mask]
    if filtered.empty:
        logger.warning("No foods found for meal_slot=%s; relaxing filter", meal_slot)
        return df
    return filtered


def filter_by_max_calories(df: pd.DataFrame, max_cal_per_100g: float) -> pd.DataFrame:
    """Keep foods below a calorie-density ceiling (per 100 g)."""
    if max_cal_per_100g <= 0:
        return df
    return df[df["calories"] <= max_cal_per_100g]


def filter_by_food_group(df: pd.DataFrame, group: str) -> pd.DataFrame:
    """Filter by a specific food group label."""
    return df[df["food_group"] == group.lower()]


def filter_by_goal_fit(df: pd.DataFrame, goal: str) -> pd.DataFrame:
    """Prefer foods tagged for the user's goal, relaxing if coverage is too low."""
    if not goal or "goal_fit_tags" not in df.columns:
        return df

    goal = goal.lower()
    filtered = df[df["goal_fit_tags"].apply(lambda tags: goal in tags or "maintenance" in tags)]
    if len(filtered) < max(10, len(df) * 0.25):
        logger.warning("Goal filter (%s) too restrictive; relaxing filter", goal)
        return df
    logger.debug("Goal filter (%s): %d → %d foods", goal, len(df), len(filtered))
    return filtered


def filter_by_preferences(df: pd.DataFrame, preferences: list[str]) -> pd.DataFrame:
    """Prefer foods matching user preference keywords (soft filter — boosts score)."""
    # This is a soft preference: just flags matching rows;
    # actual boost is done in ranking.py
    return df


# ─── Parquet-aware filters (llm_arabic_parquet mode) ─────────────────────────
# All functions below operate on the parquet DataFrame loaded by
# load_parquet_dataframe(). They use list-typed columns (already parsed from
# pipe-separated strings by the loader).


def filter_parquet_by_meal_slot(df: pd.DataFrame, slot_key: str) -> pd.DataFrame:
    """
    Keep only foods tagged for this meal slot via the `meal_slot_fit` column.
    slot_key is one of: breakfast, lunch, dinner, snack.

    The parquet column stores slot names capitalised (e.g. "Breakfast", "Lunch").
    """
    slot_cap = slot_key.capitalize()
    mask = df["meal_slot_fit"].apply(lambda lst: slot_cap in lst)
    filtered = df[mask]
    if filtered.empty:
        logger.warning(
            "filter_parquet_by_meal_slot: no foods for slot=%s; returning unfiltered", slot_key
        )
        return df
    logger.debug(
        "filter_parquet_by_meal_slot(slot=%s): %d → %d foods", slot_key, len(df), len(filtered)
    )
    return filtered


def filter_parquet_by_goal(df: pd.DataFrame, goal: str) -> pd.DataFrame:
    """
    Keep foods whose `goal_fit_tags` list includes the user's nutritional goal.
    Falls back to unfiltered if nothing matches.
    """
    if not goal:
        return df
    goal_lower = goal.lower()
    mask = df["goal_fit_tags"].apply(lambda lst: any(g.lower() == goal_lower for g in lst))
    filtered = df[mask]
    if filtered.empty:
        logger.warning(
            "filter_parquet_by_goal: no foods for goal=%s; returning unfiltered", goal
        )
        return df
    logger.debug(
        "filter_parquet_by_goal(goal=%s): %d → %d foods", goal, len(df), len(filtered)
    )
    return filtered


def filter_parquet_by_diet(df: pd.DataFrame, diet_type: str) -> pd.DataFrame:
    """
    Keep only foods compatible with the user's diet type via `diet_profile`.
    Skipped for 'normal' (no restriction).
    """
    if not diet_type or diet_type.lower() == "normal":
        return df
    diet_lower = diet_type.lower()
    mask = df["diet_profile"].apply(lambda lst: any(d.lower() == diet_lower for d in lst))
    filtered = df[mask]
    if filtered.empty:
        logger.warning(
            "filter_parquet_by_diet: no foods for diet=%s; returning unfiltered", diet_type
        )
        return df
    logger.debug(
        "filter_parquet_by_diet(diet=%s): %d → %d foods", diet_type, len(df), len(filtered)
    )
    return filtered


def filter_parquet_by_allergens(df: pd.DataFrame, allergies: list[str]) -> pd.DataFrame:
    """
    Remove foods whose `allergens` list overlaps with the user's known allergies.
    """
    if not allergies:
        return df
    allergies_lower = {a.lower() for a in allergies}
    mask = df["allergens"].apply(
        lambda lst: not any(a.lower() in allergies_lower for a in lst)
    )
    filtered = df[mask]
    logger.debug(
        "filter_parquet_by_allergens: %d → %d foods", len(df), len(filtered)
    )
    return filtered


# Keywords for heavy animal meats/fish to exclude from breakfast and snack
HEAVY_MEAT_KEYWORDS: list[str] = [
    "chicken", "beef", "steak", "turkey", "lamb", "pork", "fish", "tuna",
    "salmon", "shrimp", "crab", "kofta", "kebab", "shawarma", "duck",
]

_HEAVY_MEAT_PATTERN: str = "|".join(HEAVY_MEAT_KEYWORDS)


def filter_parquet_composites(df: pd.DataFrame, slot_key: str) -> pd.DataFrame:
    """
    Composite dishes (is_composite_dish=True) are only appropriate for
    lunch/dinner slots. For breakfast/snack, prefer non-composite items.
    This is a soft filter — if filtering leaves fewer than 5 foods, relax.
    """
    if slot_key in ("lunch", "dinner"):
        return df  # composites fine for main meals
    non_composite = df[~df["is_composite_dish"]]
    if len(non_composite) >= 5:
        logger.debug(
            "filter_parquet_composites(slot=%s): %d → %d foods (composites removed)",
            slot_key, len(df), len(non_composite),
        )
        return non_composite
    return df


def filter_parquet_heavy_meats_from_light_slots(df: pd.DataFrame, slot_key: str) -> pd.DataFrame:
    """
    Exclude heavy meats (chicken, beef, fish, steak, etc.) from Breakfast and Snack slots.
    Breakfast should feature eggs, cheese, ful, falafel, oats, bread, dairy, etc.
    Snack should feature fruits, nuts, yogurt, light snacks, dates, etc.
    """
    if slot_key not in ("breakfast", "snack"):
        return df

    mask_meat = df["food_name_en"].str.contains(_HEAVY_MEAT_PATTERN, case=False, na=False)
    filtered = df[~mask_meat]
    if filtered.empty:
        logger.warning(
            "filter_parquet_heavy_meats_from_light_slots(slot=%s): filtering removed all foods; falling back",
            slot_key,
        )
        return df

    logger.debug(
        "filter_parquet_heavy_meats_from_light_slots(slot=%s): %d → %d foods (heavy meats removed)",
        slot_key, len(df), len(filtered),
    )
    return filtered


def get_balanced_parquet_candidates_for_slot(
    df: pd.DataFrame,
    slot_key: str,
    goal: str = "",
    n_total: int = 18,
) -> pd.DataFrame:
    """
    Selects a role-balanced candidate pool of `n_total` foods for a given slot.

    Guarantees that the candidate pool sent to the LLM contains a healthy,
    culinary-sensible balance of Main Proteins, Main Carbs, Vegetables, and Fats/Fruits/Dairy
    so the LLM can compose complete, harmonious meals without over-indexing on meat.
    """
    df_slot = df.copy()

    if slot_key in ("lunch", "dinner"):
        # Main Protein pool: balance across chicken, beef, fish, and other proteins
        prot_pool = df_slot[df_slot["meal_role"] == "Main Protein"]
        chicken = prot_pool[prot_pool["food_name_en"].str.contains("chicken|turkey", case=False, na=False)].sort_values("selection_priority", ascending=False).head(2)
        beef = prot_pool[prot_pool["food_name_en"].str.contains("beef|meat|steak|lamb|kofta|burger", case=False, na=False)].sort_values("selection_priority", ascending=False).head(2)
        fish = prot_pool[prot_pool["food_name_en"].str.contains("fish|tuna|salmon|shrimp|seafood|tilapia|sardine|catfish", case=False, na=False)].sort_values("selection_priority", ascending=False).head(2)
        other_prot = prot_pool[~prot_pool["food_id"].isin(pd.concat([chicken, beef, fish])["food_id"])].sort_values("selection_priority", ascending=False).head(2)
        proteins = pd.concat([chicken, beef, fish, other_prot]).drop_duplicates(subset=["food_id"]).head(6)

        # Main Carbs / Grains / Legumes / Mixed Dishes
        carbs = df_slot[df_slot["meal_role"].isin(["Main Carb", "Mixed Dish"])].sort_values("selection_priority", ascending=False).head(6)

        # Vegetables & Salads
        veggies = df_slot[df_slot["meal_role"] == "Vegetable"].sort_values("selection_priority", ascending=False).head(4)

        # Fats / Dairy / Condiments
        fats = df_slot[df_slot["meal_role"].isin(["Healthy Fat", "Dairy", "Condiment"])].sort_values("selection_priority", ascending=False).head(2)

        candidates = pd.concat([proteins, carbs, veggies, fats]).drop_duplicates(subset=["food_id"])
        if len(candidates) < n_total:
            remaining = df_slot[~df_slot["food_id"].isin(candidates["food_id"])].sort_values("selection_priority", ascending=False).head(n_total - len(candidates))
            candidates = pd.concat([candidates, remaining])
        return candidates.head(n_total).reset_index(drop=True)

    elif slot_key == "breakfast":
        # Breakfast proteins (eggs, cheese, ful/fava beans, falafel, dairy)
        proteins = df_slot[df_slot["meal_role"].isin(["Dairy", "Main Protein"])].sort_values("selection_priority", ascending=False).head(6)

        # Breakfast carbs (bread, oats, pita, grains)
        carbs = df_slot[df_slot["meal_role"] == "Main Carb"].sort_values("selection_priority", ascending=False).head(6)

        # Fruits & Vegetables
        fruits_veggies = df_slot[df_slot["meal_role"].isin(["Fruit", "Vegetable"])].sort_values("selection_priority", ascending=False).head(4)

        # Fats (olive oil, tahini, cream, butter)
        fats = df_slot[df_slot["meal_role"] == "Healthy Fat"].sort_values("selection_priority", ascending=False).head(2)

        candidates = pd.concat([proteins, carbs, fruits_veggies, fats]).drop_duplicates(subset=["food_id"])
        if len(candidates) < n_total:
            remaining = df_slot[~df_slot["food_id"].isin(candidates["food_id"])].sort_values("selection_priority", ascending=False).head(n_total - len(candidates))
            candidates = pd.concat([candidates, remaining])
        return candidates.head(n_total).reset_index(drop=True)

    else:  # snack
        # Fruits
        fruits = df_slot[df_slot["meal_role"] == "Fruit"].sort_values("selection_priority", ascending=False).head(6)

        # Dairy / Yogurt / Cheese
        dairy = df_slot[df_slot["meal_role"] == "Dairy"].sort_values("selection_priority", ascending=False).head(4)

        # Healthy Fats / Nuts / Seeds
        fats = df_slot[df_slot["meal_role"] == "Healthy Fat"].sort_values("selection_priority", ascending=False).head(4)

        # Other light snacks
        others = df_slot[~df_slot["food_id"].isin(pd.concat([fruits, dairy, fats])["food_id"])].sort_values("selection_priority", ascending=False).head(4)

        candidates = pd.concat([fruits, dairy, fats, others]).drop_duplicates(subset=["food_id"])
        if len(candidates) < n_total:
            remaining = df_slot[~df_slot["food_id"].isin(candidates["food_id"])].sort_values("selection_priority", ascending=False).head(n_total - len(candidates))
            candidates = pd.concat([candidates, remaining])
        return candidates.head(n_total).reset_index(drop=True)



def rank_parquet_foods(
    df: pd.DataFrame,
    goal: str,
    slot_key: str,
    n: int = 20,
) -> pd.DataFrame:
    """
    Multi-factor ranking for the parquet dataset:

    Score = 0.50 × selection_priority_norm    (curated quality signal)
           + 0.30 × goal_alignment_score      (goal_fit_tags match)
           + 0.20 × macro_slot_score          (primary_macro_type fits the slot)

    Returns the top-n rows, sorted descending by score.
    """
    df = df.copy()
    goal_lower = goal.lower() if goal else ""

    # 1. Normalise selection_priority (0–5 → 0–1)
    df["_priority_norm"] = df["selection_priority"].clip(0, 5) / 5.0

    # 2. Goal alignment: 1 if any goal_fit_tag matches, 0 otherwise
    df["_goal_score"] = df["goal_fit_tags"].apply(
        lambda lst: 1.0 if goal_lower and any(g.lower() == goal_lower for g in lst) else 0.0
    )

    # 3. Macro-slot alignment
    # For breakfast/snack: prefer carb, balanced, low_macro
    # For lunch/dinner: prefer protein, balanced, fat
    _SLOT_MACRO_PREF: dict[str, set[str]] = {
        "breakfast": {"carb", "balanced", "low_macro"},
        "snack": {"carb", "balanced", "low_macro"},
        "lunch": {"protein", "balanced", "fat"},
        "dinner": {"protein", "balanced", "fat"},
    }
    preferred_macros = _SLOT_MACRO_PREF.get(slot_key, {"balanced"})
    df["_macro_score"] = df["primary_macro_type"].apply(
        lambda m: 1.0 if m in preferred_macros else 0.0
    )

    # Composite score
    df["_score"] = (
        0.50 * df["_priority_norm"]
        + 0.30 * df["_goal_score"]
        + 0.20 * df["_macro_score"]
    )

    # Sort descending and return top-n, dropping internal score columns
    score_cols = [c for c in df.columns if c.startswith("_")]
    ranked = df.sort_values("_score", ascending=False).head(n)
    return ranked.drop(columns=score_cols, errors="ignore").reset_index(drop=True)

