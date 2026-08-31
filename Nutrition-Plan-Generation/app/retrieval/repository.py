"""
Food Repository — the single public interface for food retrieval.

The Meal Composition Agent only ever calls this class.
Swapping the underlying storage (Pandas → PostgreSQL) only requires
changing this file.
"""

import pandas as pd
from app.retrieval.loader import load_food_dataframe
from app.retrieval.filters import (
    filter_by_allergens,
    filter_by_diet_type,
    filter_by_goal_fit,
    filter_by_meal_slot_fit,
    filter_by_meal_type,
    filter_by_food_group,
)
from app.retrieval.ranking import score_foods, top_n
from app.schemas.foods import FoodItem, RetrievedFoods
from app.schemas.profile import MacroResult
from app.core.constants import MAX_CANDIDATE_FOODS
from app.core.logging import get_logger

logger = get_logger(__name__)

_ITEMS_PER_GROUP = MAX_CANDIDATE_FOODS // 6   # distribute budget across groups


def _row_to_food_item(row: pd.Series) -> FoodItem:
    return FoodItem(
        food_id=str(row["food_id"]),
        name=str(row["food_name_en"]),
        calories_per_100g=float(row["calories"]),
        protein_per_100g=float(row["protein"]),
        carbs_per_100g=float(row["carbs"]),
        fat_per_100g=float(row["fat"]),
        food_group=str(row["food_group"]),
        meal_types=list(row["meal_types"]),
        allergens=list(row["allergens"]),
        diet_types=list(row["diet_types"]),
        meal_role=str(row.get("meal_role", "General")),
        meal_slot_fit=list(row.get("meal_slot_fit", row.get("meal_types", []))),
        goal_fit_tags=list(row.get("goal_fit_tags", [])),
        primary_macro_type=str(row.get("primary_macro_type", "balanced")),
        macro_gap_utility_profile=str(row.get("macro_gap_utility_profile", "balanced_macro")),
        best_with=list(row.get("best_with", [])),
        diet_profile=list(row.get("diet_profile", row.get("diet_types", []))),
        selection_priority=float(row.get("selection_priority", 0)),
    )


def _get_group(
    df: pd.DataFrame,
    group: str,
    preferences: list[str],
    goal: str,
    diet_type: str,
    macro_focus: str,
    n: int,
    meal_slot: str | None = None,
) -> list[FoodItem]:
    """Filter by food_group, rank, and return top-n as FoodItem objects."""
    subset = filter_by_food_group(df, group)
    if subset.empty:
        return []
    scored = score_foods(subset, preferences, goal, diet_type, macro_focus, meal_slot)
    best = top_n(scored, n)
    return [_row_to_food_item(row) for _, row in best.iterrows()]


class FoodRepository:
    """
    Repository abstraction over the in-memory food DataFrame.
    Instantiated once and injected via FastAPI dependency.
    """

    def __init__(self) -> None:
        self._df: pd.DataFrame = load_food_dataframe()
        logger.info("FoodRepository initialised with %d foods", len(self._df))

    def get_candidate_foods(self, macro_result: MacroResult) -> RetrievedFoods:
        """
        Main retrieval entry point.
        Applies allergen + diet filters, then retrieves top candidates
        for each food group.
        """
        df = self._df.copy()

        # ── Hard filters ─────────────────────────────────────────────────────
        df = filter_by_allergens(df, macro_result.allergies)
        df = filter_by_diet_type(df, macro_result.diet_type)
        df = filter_by_goal_fit(df, macro_result.goal)

        if df.empty:
            logger.warning("No foods left after hard filters; returning empty retrieval")
            return RetrievedFoods()

        prefs = macro_result.preferences
        macro_focus = max(
            [("protein", macro_result.protein_g * 4), ("carb", macro_result.carbs_g * 4), ("fat", macro_result.fat_g * 9)],
            key=lambda item: item[1],
        )[0]

        retrieved = RetrievedFoods(
            proteins=_get_group(df, "protein", prefs, macro_result.goal, macro_result.diet_type, "protein", _ITEMS_PER_GROUP + 2),
            carbohydrates=_get_group(df, "carbohydrate", prefs, macro_result.goal, macro_result.diet_type, "carb", _ITEMS_PER_GROUP),
            vegetables=_get_group(df, "vegetable", prefs, macro_result.goal, macro_result.diet_type, macro_focus, _ITEMS_PER_GROUP),
            fruits=_get_group(filter_by_meal_slot_fit(df, "snack"), "fruit", prefs, macro_result.goal, macro_result.diet_type, "carb", _ITEMS_PER_GROUP - 1, "snack"),
            dairy=_get_group(df, "dairy", prefs, macro_result.goal, macro_result.diet_type, macro_focus, _ITEMS_PER_GROUP - 1),
            healthy_fats=_get_group(df, "fat", prefs, macro_result.goal, macro_result.diet_type, "fat", _ITEMS_PER_GROUP - 1),
        )

        total = len(retrieved.all_foods)
        logger.info(
            "Retrieved %d candidate foods | proteins=%d  carbs=%d  veg=%d  fruit=%d  dairy=%d  fats=%d",
            total,
            len(retrieved.proteins),
            len(retrieved.carbohydrates),
            len(retrieved.vegetables),
            len(retrieved.fruits),
            len(retrieved.dairy),
            len(retrieved.healthy_fats),
        )
        return retrieved


# ─── Parquet Food Repository (llm_arabic_parquet mode) ───────────────────────

from app.retrieval.loader import load_parquet_dataframe
from app.retrieval.filters import (
    filter_parquet_by_meal_slot,
    filter_parquet_by_goal,
    filter_parquet_by_diet,
    filter_parquet_by_allergens,
    filter_parquet_composites,
    filter_parquet_heavy_meats_from_light_slots,
    get_balanced_parquet_candidates_for_slot,
    rank_parquet_foods,
)
from app.schemas.foods import ParquetFoodItem, ParquetRetrievedFoods
from app.schemas.profile import MacroResult, MealSlotTarget

# How many foods per slot to pass to the LLM as context
_PARQUET_FOODS_PER_SLOT: int = 18


def _row_to_parquet_food_item(row: pd.Series) -> ParquetFoodItem:
    """Convert a parquet DataFrame row to a ParquetFoodItem Pydantic model."""
    return ParquetFoodItem(
        food_id=str(row.get("food_id", "")),
        food_name_en=str(row.get("food_name_en", "")),
        food_name_ar=str(row.get("food_name_ar", "")),
        food_group=str(row.get("food_group", "")),
        serving_name=str(row.get("serving_name", "100 g")),
        serving_weight_g=float(row.get("serving_weight_g", 100.0)),
        calories=float(row.get("calories", 0.0)),
        protein=float(row.get("protein", 0.0)),
        carbs=float(row.get("carbs", 0.0)),
        fat=float(row.get("fat", 0.0)),
        fiber=float(row.get("fiber", 0.0)),
        meal_role=str(row.get("meal_role", "")),
        meal_slot_fit=list(row.get("meal_slot_fit", [])),
        goal_fit_tags=list(row.get("goal_fit_tags", [])),
        diet_profile=list(row.get("diet_profile", [])),
        allergens=list(row.get("allergens", [])),
        best_with=list(row.get("best_with", [])),
        is_composite_dish=bool(row.get("is_composite_dish", False)),
        selection_priority=int(row.get("selection_priority", 3)),
        primary_macro_type=str(row.get("primary_macro_type", "balanced")),
        diet_tags=list(row.get("diet_tags", [])),
    )


class ParquetFoodRepository:
    """
    Repository for the rich parquet food dataset.

    Used exclusively in the `llm_arabic_parquet` generation mode.
    Applies multi-column filtering (meal slot, goal, diet, allergens,
    composite dish suitability, slot-appropriate heavy meat exclusions)
    and a role-balanced candidate selector before returning foods to the LLM.
    """

    def __init__(self) -> None:
        self._df: pd.DataFrame = load_parquet_dataframe()
        logger.info(
            "ParquetFoodRepository initialised with %d foods (%d columns)",
            len(self._df), len(self._df.columns),
        )

    def get_candidate_foods_for_slot(
        self,
        macro_result: MacroResult,
        slot_key: str,
        n: int = _PARQUET_FOODS_PER_SLOT,
    ) -> list[ParquetFoodItem]:
        """
        Return the top-N foods for a given meal slot, applying all filters:

        Hard filters (remove items that violate constraints):
          1. allergens        — exclude user allergens
          2. diet_profile     — respect diet type (vegetarian / vegan / keto…)
          3. meal_slot_fit    — foods appropriate for this slot
          4. heavy_meats      — exclude chicken/beef/fish/steak from Breakfast & Snack
          5. composites       — exclude composite dishes from Breakfast & Snack

        Soft candidate balancing & ranking:
          6. Role-balanced food group selection (proteins, carbs, veggies, fats)
        """
        df = self._df.copy()

        # ── Hard filters ─────────────────────────────────────────────────────
        df = filter_parquet_by_allergens(df, macro_result.allergies)
        df = filter_parquet_by_diet(df, macro_result.diet_type)
        df = filter_parquet_by_meal_slot(df, slot_key)
        df = filter_parquet_heavy_meats_from_light_slots(df, slot_key)
        df = filter_parquet_composites(df, slot_key)

        if df.empty:
            logger.warning(
                "ParquetFoodRepository: no foods left after hard filters for slot=%s; "
                "falling back to allergen-only filter",
                slot_key,
            )
            df = self._df.copy()
            df = filter_parquet_by_allergens(df, macro_result.allergies)

        # ── Role-balanced selection ──────────────────────────────────────────
        ranked = get_balanced_parquet_candidates_for_slot(
            df, slot_key=slot_key, goal=macro_result.goal, n_total=n
        )

        items = [_row_to_parquet_food_item(row) for _, row in ranked.iterrows()]
        logger.info(
            "ParquetFoodRepository slot=%s → %d candidate foods "
            "(goal=%s, diet=%s, allergies=%s)",
            slot_key, len(items), macro_result.goal,
            macro_result.diet_type, macro_result.allergies,
        )
        return items

    def get_all_slots(
        self,
        macro_result: MacroResult,
        n: int = _PARQUET_FOODS_PER_SLOT,
    ) -> ParquetRetrievedFoods:
        """Retrieve candidate foods for all 4 meal slots at once."""
        return ParquetRetrievedFoods(
            breakfast=self.get_candidate_foods_for_slot(macro_result, "breakfast", n),
            lunch=self.get_candidate_foods_for_slot(macro_result, "lunch", n),
            dinner=self.get_candidate_foods_for_slot(macro_result, "dinner", n),
            snack=self.get_candidate_foods_for_slot(macro_result, "snack", n),
        )

