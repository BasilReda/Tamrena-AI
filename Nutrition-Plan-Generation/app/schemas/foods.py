# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Any


# ─── Food Item (dataset mode — Excel source) ─────────────────────────────────


class FoodItem(BaseModel):
    """A single food item with nutritional data (per 100 g)."""

    food_id: str
    name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    food_group: str = "general"
    meal_types: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    diet_types: list[str] = Field(default_factory=list)
    meal_role: str = "General"
    meal_slot_fit: list[str] = Field(default_factory=list)
    goal_fit_tags: list[str] = Field(default_factory=list)
    primary_macro_type: str = "balanced"
    macro_gap_utility_profile: str = "balanced_macro"
    best_with: list[str] = Field(default_factory=list)
    diet_profile: list[str] = Field(default_factory=list)
    selection_priority: float = 0.0

    @property
    def food_name_en(self) -> str:
        """Backward-compatible alias for the canonical food name."""
        return self.name


class RetrievedFoods(BaseModel):
    """Foods returned by the retrieval layer, grouped by category."""

    proteins: list[FoodItem] = Field(default_factory=list)
    carbohydrates: list[FoodItem] = Field(default_factory=list)
    vegetables: list[FoodItem] = Field(default_factory=list)
    fruits: list[FoodItem] = Field(default_factory=list)
    dairy: list[FoodItem] = Field(default_factory=list)
    healthy_fats: list[FoodItem] = Field(default_factory=list)

    @property
    def all_foods(self) -> list[FoodItem]:
        return (
            self.proteins
            + self.carbohydrates
            + self.vegetables
            + self.fruits
            + self.dairy
            + self.healthy_fats
        )


# ─── Parquet Food Item (llm_arabic_parquet mode — parquet source) ────────────


class ParquetFoodItem(BaseModel):
    """
    A richer food item sourced from foods_master_final.parquet.

    Carries Arabic names, pairing hints, goal-fit tags, and all contextual
    columns that are fed to the LLM in the llm_arabic_parquet mode.
    Nutritional values are *per 100 g* unless otherwise noted.
    """

    food_id: str
    food_name_en: str
    food_name_ar: str                       # Arabic name shown to the LLM
    food_group: str
    serving_name: str                       # e.g. "100 g"
    serving_weight_g: float                 # typical serving in grams
    calories: float                         # per 100 g
    protein: float                          # per 100 g
    carbs: float                            # per 100 g
    fat: float                              # per 100 g
    fiber: float                            # per 100 g
    meal_role: str                          # e.g. "Main Protein", "Healthy Fat"
    meal_slot_fit: list[str] = Field(default_factory=list)   # e.g. ["Lunch", "Dinner"]
    goal_fit_tags: list[str] = Field(default_factory=list)   # e.g. ["fat_loss", "maintenance"]
    diet_profile: list[str] = Field(default_factory=list)    # e.g. ["vegetarian", "vegan"]
    allergens: list[str] = Field(default_factory=list)
    best_with: list[str] = Field(default_factory=list)       # pairing suggestions
    is_composite_dish: bool = False
    selection_priority: int = 3             # 0 (avoid) → 5 (always prefer)
    primary_macro_type: str = "balanced"    # "protein" | "carb" | "fat" | "balanced" | "low_macro"
    diet_tags: list[str] = Field(default_factory=list)


class ParquetRetrievedFoods(BaseModel):
    """Per-slot food lists retrieved from the parquet dataset."""

    breakfast: list[ParquetFoodItem] = Field(default_factory=list)
    lunch: list[ParquetFoodItem] = Field(default_factory=list)
    dinner: list[ParquetFoodItem] = Field(default_factory=list)
    snack: list[ParquetFoodItem] = Field(default_factory=list)

    def for_slot(self, slot_key: str) -> list[ParquetFoodItem]:
        return getattr(self, slot_key, [])
