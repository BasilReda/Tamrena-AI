"""
Food Dataset Loader

Loads the canonical food Parquet dataset once at application startup.
The enriched DataFrame is held in memory for the lifetime of the process.
No LLM is involved.
"""

import pandas as pd
from pathlib import Path
from functools import lru_cache
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_FOOD_DATA_PATH = Path(settings.food_data_path)
_FINAL_FOOD_DATA_PATH = Path("DataPrep/usedData/foods_master_final.parquet")
_LEGACY_FOOD_DATA_PATH = Path("DataPrep/usedData/foods_master.parquet")

_REQUIRED_COLUMNS = {
    "food_id",
    "food_name_en",
    "food_group",
    "meal_types",
    "serving_name",
    "serving_weight_g",
    "nutrition_basis",
    "calories",
    "protein",
    "carbs",
    "fat",
    "fiber",
    "diet_tags",
    "allergens",
    "is_composite_dish",
    "source",
    "meal_role",
    "meal_slot_fit",
    "goal_fit_tags",
    "primary_macro_type",
    "macro_gap_utility_profile",
    "best_with",
    "diet_profile",
    "selection_priority",
}

_FOOD_GROUP_MAP = {
    "protein": "protein",
    "healthy fats": "fat",
    "vegetables": "vegetable",
    "fruits": "fruit",
    "dairy": "dairy",
    "legumes": "protein",
    "grains": "carbohydrate",
    "beverages": "general",
    "snacks": "general",
    "composite dish": "general",
}

def _split_tags(value: object) -> list[str]:
    """Convert pipe-delimited Parquet tag fields into lists for filters."""
    if value is None or pd.isna(value):
        return []
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip().lower() for part in text.split("|") if part.strip()]


def _normalise_food_group(value: object) -> str:
    group = str(value).strip().lower()
    if not group:
        return "general"
    return _FOOD_GROUP_MAP.get(group, "general")


def _derive_diet_types(diet_tags: list[str]) -> list[str]:
    if "plant_based" in diet_tags:
        return ["normal", "vegetarian", "vegan"]
    return ["normal"]


def _normalise_diet_profile(diet_profile: list[str], diet_tags: list[str]) -> list[str]:
    profiles = set(diet_profile)
    if "omnivore" in profiles:
        profiles.add("normal")
    if "plant_based" in diet_tags:
        profiles.update({"vegetarian", "vegan"})
    profiles.add("normal")
    return sorted(profiles)


def _normalise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare canonical Parquet columns for in-memory retrieval."""
    missing = sorted(_REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Food dataset missing required columns: {missing}")

    df = df.copy()

    essential_cols = ["calories", "protein", "carbs", "fat"]
    df = df.dropna(subset=essential_cols).reset_index(drop=True)
    for col in essential_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=essential_cols).reset_index(drop=True)

    df["meal_types"] = df["meal_types"].apply(_split_tags)
    df["meal_slot_fit"] = df["meal_slot_fit"].apply(_split_tags)
    df["goal_fit_tags"] = df["goal_fit_tags"].apply(_split_tags)
    df["best_with"] = df["best_with"].apply(_split_tags)
    df["diet_profile"] = df["diet_profile"].apply(_split_tags)
    df["diet_tags"] = df["diet_tags"].apply(_split_tags)
    df["allergens"] = df["allergens"].apply(_split_tags)
    df["food_group"] = df["food_group"].apply(_normalise_food_group)
    df["meal_role"] = df["meal_role"].fillna("General").astype(str).str.strip()
    df["primary_macro_type"] = df["primary_macro_type"].fillna("balanced").astype(str).str.strip().str.lower()
    df["macro_gap_utility_profile"] = df["macro_gap_utility_profile"].fillna("balanced_macro").astype(str).str.strip().str.lower()
    df["selection_priority"] = pd.to_numeric(df["selection_priority"], errors="coerce").fillna(0).clip(0, 5)
    df["diet_types"] = df.apply(
        lambda row: _normalise_diet_profile(row["diet_profile"], row["diet_tags"]),
        axis=1,
    )
    return df


def _resolve_food_data_path() -> Path:
    """Prefer the configured parquet path, but fall back to the final production dataset."""
    candidates = [_FOOD_DATA_PATH, _FINAL_FOOD_DATA_PATH, _LEGACY_FOOD_DATA_PATH]
    for path in candidates:
        if path.exists() and path.suffix.lower() == ".parquet":
            return path
    raise FileNotFoundError(
        f"No usable food dataset found. Checked: {', '.join(str(p) for p in candidates)}"
    )


@lru_cache(maxsize=1)
def load_food_dataframe() -> pd.DataFrame:
    """
    Load the canonical food dataset.
    Cached so the file is only read once per process lifetime.
    """
    data_path = _resolve_food_data_path()
    df = pd.read_parquet(data_path)
    df = _normalise_dataframe(df)

    # ── Safety net: preserve existing business rule for zero-calorie rows.
    zero_cal_mask = df["calories"] == 0
    if zero_cal_mask.any():
        df.loc[zero_cal_mask, "calories"] = (
            df.loc[zero_cal_mask, "protein"] * 4.0
            + df.loc[zero_cal_mask, "carbs"] * 4.0
            + df.loc[zero_cal_mask, "fat"] * 9.0
        ).round(1)
        logger.warning(
            "Atwater fallback applied to %d foods with zero calories",
            zero_cal_mask.sum(),
        )

    logger.info("Food dataset loaded from %s: %d foods", data_path, len(df))
    return df


# ─── Parquet loader (foods_master_final.parquet) ───────────────────────────────

_PARQUET_LIST_COLS = [
    "meal_types",
    "diet_tags",
    "allergens",
    "goal_fit_tags",
    "meal_slot_fit",
    "diet_profile",
    "best_with",
]


def _parse_pipe_list(value) -> list[str]:
    """
    Convert a pipe-separated string (or NaN / None) to a Python list of stripped strings.
    Empty strings in the result are dropped.
    """
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return []
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return []
    return [item.strip() for item in s.split("|") if item.strip()]


@lru_cache(maxsize=1)
def load_parquet_dataframe() -> pd.DataFrame:
    """
    Load the rich Egyptian food parquet dataset (foods_master_final.parquet).
    Cached — read once per process lifetime.

    Post-processing:
    - Pipe-separated list columns are converted to Python lists.
    - Numeric columns are coerced (NaN rows in essential fields are dropped).
    - All column names are left as-is (they map directly to ParquetFoodItem fields).
    """
    parquet_path = Path("DataPrep/usedData/foods_master_final.parquet")
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet food dataset not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)

    # ── Convert pipe-separated string columns to lists ────────────────────────
    for col in _PARQUET_LIST_COLS:
        if col in df.columns:
            df[col] = df[col].apply(_parse_pipe_list)

    # ── Coerce essential numeric columns ──────────────────────────────────────
    essential_numeric = ["calories", "protein", "carbs", "fat", "fiber", "serving_weight_g"]
    for col in essential_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["calories", "protein", "carbs", "fat"]).reset_index(drop=True)
    df["fiber"] = df["fiber"].fillna(0.0)
    df["serving_weight_g"] = df["serving_weight_g"].fillna(100.0)

    # ── Ensure selection_priority is int ─────────────────────────────────────
    if "selection_priority" in df.columns:
        df["selection_priority"] = pd.to_numeric(df["selection_priority"], errors="coerce").fillna(3).astype(int)

    # ── Ensure is_composite_dish is bool ─────────────────────────────────────
    if "is_composite_dish" in df.columns:
        df["is_composite_dish"] = df["is_composite_dish"].fillna(False).astype(bool)

    # ── Fill string columns that may be null ─────────────────────────────────
    for col in ["food_name_ar", "food_name_en", "food_group", "serving_name",
                "meal_role", "primary_macro_type", "macro_gap_utility_profile", "source"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # ── Safety: compute missing calories via Atwater factors ──────────────────
    zero_cal_mask = df["calories"] == 0
    if zero_cal_mask.any():
        df.loc[zero_cal_mask, "calories"] = (
            df.loc[zero_cal_mask, "protein"] * 4.0
            + df.loc[zero_cal_mask, "carbs"] * 4.0
            + df.loc[zero_cal_mask, "fat"] * 9.0
        ).round(1)
        logger.warning(
            "Atwater fallback applied to %d parquet foods with zero calories",
            zero_cal_mask.sum(),
        )

    logger.info("Parquet food dataset loaded: %d foods (%d columns)", len(df), len(df.columns))
    return df

