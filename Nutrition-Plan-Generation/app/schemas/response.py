# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Any, Literal
from app.schemas.profile import MealPlan, TripleMealPlan, ValidationReport, Explanation, MacroResult, CaloriesResult


# ─── Start Response ────────────────────────────────────────────────────────────


class StartResponse(BaseModel):
    run_id: str
    status: Literal["started"] = "started"
    message: str = "Nutrition generation started. Connect to the stream endpoint."


# ─── SSE Stream Event ─────────────────────────────────────────────────────────


class StreamEvent(BaseModel):
    run_id: str
    node: str
    status: Literal["started", "running", "completed", "failed", "retrying"]
    progress: int = Field(ge=0, le=100)
    message: str | None = None
    duration_ms: int | None = None
    reason: str | None = None


# ─── Final Nutrition Plan Response ────────────────────────────────────────────


class NutritionPlanResponse(BaseModel):
    run_id: str
    success: bool
    macro_result: MacroResult | None = None
    calories_result: CaloriesResult | None = None
    meal_plan: MealPlan | None = None
    triple_meal_plan: TripleMealPlan | None = None
    validation_report: ValidationReport | None = None
    explanation: Explanation | None = None
    retry_count: int = 0
    error: str | None = None


# ─── Generic API Wrapper ──────────────────────────────────────────────────────


class APIResponse(BaseModel):
    success: bool
    data: Any | None = None
    message: str = "Success"
    error: str | None = None
