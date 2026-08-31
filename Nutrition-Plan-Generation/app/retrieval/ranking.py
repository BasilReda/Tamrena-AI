"""
Ranking logic for the food retrieval layer.
Scores foods by nutritional quality and user preference match.
No LLM is involved.
"""

import pandas as pd
from app.core.logging import get_logger

logger = get_logger(__name__)


def score_foods(
    df: pd.DataFrame,
    preferences: list[str],
    goal: str | None = None,
    diet_type: str | None = None,
    macro_focus: str | None = None,
    meal_slot: str | None = None,
) -> pd.DataFrame:
    """
    Assign a composite score to each food row.

    Score components combine nutrition with production metadata:
    1. Protein density and goal-aware calorie density
    2. User preference match
    3. meal_slot_fit, goal_fit_tags, diet_profile, meal_role, macro_gap_utility_profile
    4. Dataset curation signal: selection_priority
    """
    df = df.copy()

    # Guard against divide-by-zero
    cal = df["calories"].clip(lower=1)

    # 1. Protein density score (0–1 normalised)
    df["_protein_density"] = df["protein"] / cal

    # 2. Inverse calorie density (prefer lower-calorie foods)
    df["_cal_score"] = 1.0 / cal

    # 3. Preference match bonus
    pref_lower = [p.lower() for p in preferences]

    def _pref_score(name: str) -> float:
        n = name.lower()
        return 0.3 if any(p in n for p in pref_lower) else 0.0

    df["_pref_score"] = df["food_name_en"].apply(_pref_score)

    goal = (goal or "").lower()
    diet_type = (diet_type or "normal").lower()
    macro_focus = (macro_focus or "").lower()
    meal_slot = (meal_slot or "").lower()

    if "selection_priority" in df.columns:
        df["_priority_score"] = df["selection_priority"].clip(0, 5) / 5.0
    else:
        df["_priority_score"] = 0.0

    if "goal_fit_tags" in df.columns and goal:
        df["_goal_score"] = df["goal_fit_tags"].apply(
            lambda tags: 1.0 if goal in tags else (0.5 if "maintenance" in tags else 0.0)
        )
    else:
        df["_goal_score"] = 0.0

    diet_col = "diet_types" if "diet_types" in df.columns else "diet_profile"
    if diet_col in df.columns:
        accepted_diets = {diet_type, "normal"}
        if diet_type == "normal":
            accepted_diets.add("omnivore")
        df["_diet_score"] = df[diet_col].apply(
            lambda tags: 1.0 if any(tag in accepted_diets for tag in tags) else 0.0
        )
    else:
        df["_diet_score"] = 0.0

    if "meal_slot_fit" in df.columns and meal_slot:
        df["_slot_score"] = df["meal_slot_fit"].apply(lambda slots: 1.0 if meal_slot in slots else 0.0)
    elif "meal_slot_fit" in df.columns:
        df["_slot_score"] = df["meal_slot_fit"].apply(
            lambda slots: 1.0 if any(slot in slots for slot in ["breakfast", "lunch", "dinner"]) else 0.6
        )
    else:
        df["_slot_score"] = 0.0

    if "primary_macro_type" in df.columns and macro_focus:
        df["_macro_type_score"] = df["primary_macro_type"].apply(
            lambda value: 1.0 if value == macro_focus else (0.5 if value == "balanced" else 0.0)
        )
    else:
        df["_macro_type_score"] = 0.0

    if "macro_gap_utility_profile" in df.columns:
        utility_targets = {"balanced_macro"}
        if macro_focus == "protein":
            utility_targets.add("lean_protein")
        elif macro_focus == "carb":
            utility_targets.add("healthy_carb")
        elif macro_focus == "fat":
            utility_targets.add("calorie_dense")
        df["_macro_utility_score"] = df["macro_gap_utility_profile"].apply(
            lambda value: 1.0 if value in utility_targets else 0.0
        )
    else:
        df["_macro_utility_score"] = 0.0

    if "meal_role" in df.columns:
        role_by_group = {
            "protein": {"main protein", "mixed dish"},
            "carbohydrate": {"main carb", "mixed dish"},
            "vegetable": {"vegetable"},
            "fruit": {"fruit"},
            "dairy": {"dairy"},
            "fat": {"healthy fat"},
        }
        df["_role_score"] = df.apply(
            lambda row: 1.0 if str(row["meal_role"]).lower() in role_by_group.get(str(row["food_group"]).lower(), set()) else 0.4,
            axis=1,
        )
    else:
        df["_role_score"] = 0.0

    # Composite score
    df["_score"] = (
        0.22 * df["_protein_density"]
        + 0.08 * df["_cal_score"]
        + 0.14 * df["_pref_score"]
        + 0.16 * df["_priority_score"]
        + 0.12 * df["_goal_score"]
        + 0.08 * df["_diet_score"]
        + 0.08 * df["_slot_score"]
        + 0.06 * df["_macro_type_score"]
        + 0.04 * df["_macro_utility_score"]
        + 0.02 * df["_role_score"]
    )

    return df.sort_values("_score", ascending=False)


def top_n(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Return the top-n scoring rows and drop internal score columns."""
    score_cols = [c for c in df.columns if c.startswith("_")]
    return df.head(n).drop(columns=score_cols, errors="ignore")
