# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from enum import Enum


class Goal(str, Enum):
    fat_loss = "fat_loss"
    weight_loss = "weight_loss"
    muscle_gain = "muscle_gain"
    bulking = "bulking"
    maintenance = "maintenance"
    recomposition = "recomposition"


class Gender(str, Enum):
    male = "male"
    female = "female"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderate = "moderate"
    very_active = "very_active"
    extra_active = "extra_active"


class DietType(str, Enum):
    normal = "normal"
    vegetarian = "vegetarian"
    vegan = "vegan"
    keto = "keto"
    high_protein = "high_protein"


class MealGenerationMode(str, Enum):
    """Controls which meal composition pipeline is used."""
    dataset = "dataset"
    """Retrieve from the Egyptian food Excel DB then compose with LLM in English."""
    llm_arabic = "llm_arabic"
    """LLM freely creates authentic Egyptian meals in Arabic (no food dataset)."""
    llm_arabic_parquet = "llm_arabic_parquet"
    """
    Retrieve per-slot foods from foods_master_final.parquet (Arabic names, goal fit,
    allergens, diet profile, best-with pairings) then compose 3 options in Arabic.
    Combines real food grounding with Arabic language output.
    """


class GenerateNutritionRequest(BaseModel):
    """Input model for the nutrition generation endpoint."""

    # ── User bio ──────────────────────────────────────────────────────────────
    age: int = Field(..., ge=10, le=100, description="Age in years")
    gender: Gender = Field(..., description="Biological sex")
    height_cm: float = Field(..., ge=100, le=250, description="Height in centimetres")
    weight_kg: float = Field(..., ge=30, le=300, description="Weight in kilograms")

    # ── Goal & activity ───────────────────────────────────────────────────────
    goal: Goal = Field(..., description="Primary fitness goal")
    activity_level: ActivityLevel = Field(
        default=ActivityLevel.moderate,
        description="General physical activity level",
    )
    diet_type: DietType = Field(
        default=DietType.normal,
        description="Dietary pattern",
    )

    # ── Preferences & restrictions ────────────────────────────────────────────
    preferences: list[str] = Field(
        default_factory=list,
        description="Preferred foods or ingredients",
        examples=[["chicken", "rice", "vegetables"]],
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Foods or allergens to avoid",
        examples=[["peanuts", "dairy"]],
    )
    additional_notes: str | None = Field(
        default=None,
        description="Free-text notes (medical conditions, preferences, etc.)",
        max_length=500,
    )

    # ── Generation mode ───────────────────────────────────────────────────────
    meal_generation_mode: MealGenerationMode = Field(
        default=MealGenerationMode.llm_arabic,
        description=(
            "Meal generation pipeline: "
            "'llm_arabic' = free-form Arabic LLM (3 options) [DEFAULT]; "
            "'llm_arabic_parquet' = parquet food catalog per slot + Arabic LLM (3 options); "
            "'dataset' = Excel food DB + English LLM"
        ),
    )

    @field_validator("preferences", "allergies", mode="before")
    @classmethod
    def lowercase_list(cls, v: list[str]) -> list[str]:
        return [item.lower().strip() for item in v if item.strip()]
