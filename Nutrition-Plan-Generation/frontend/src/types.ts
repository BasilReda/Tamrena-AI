export type GoalType = "fat_loss" | "weight_loss" | "muscle_gain" | "bulking" | "maintenance" | "recomposition";
export type ActivityLevel = "sedentary" | "lightly_active" | "moderate" | "very_active" | "extra_active";
export type DietType = "normal" | "vegetarian" | "vegan" | "keto" | "high_protein";
export type GenderType = "male" | "female";
export type MealGenerationMode = "dataset" | "llm_arabic" | "llm_arabic_parquet";

export interface GenerateNutritionRequest {
  age: number;
  gender: GenderType;
  height_cm: number;
  weight_kg: number;
  goal: GoalType;
  activity_level: ActivityLevel;
  diet_type: DietType;
  preferences: string[];
  allergies: string[];
  additional_notes?: string;
  meal_generation_mode: MealGenerationMode;
}

export interface MealFoodItem {
  name: string;
  serving_grams: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface Meal {
  meal_name: string;
  foods: MealFoodItem[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
}

export interface MealPlan {
  breakfast: Meal;
  lunch: Meal;
  dinner: Meal;
  snack?: Meal;
  total_daily_calories: number;
  total_daily_protein_g: number;
  total_daily_carbs_g: number;
  total_daily_fat_g: number;
  notes?: string;
}

export interface MealSlotTarget {
  meal_name: string;
  slot_key: string;
  target_calories: number;
  target_protein_g: number;
  target_carbs_g: number;
  target_fat_g: number;
}

export interface MealDistribution {
  breakfast: MealSlotTarget;
  lunch: MealSlotTarget;
  dinner: MealSlotTarget;
  snack: MealSlotTarget;
  total_calories: number;
}

export interface TripleMealPlan {
  option_a: MealPlan;
  option_b: MealPlan;
  option_c: MealPlan;
  meal_distribution: MealDistribution;
  notes?: string;
}

export interface ValidationIssue {
  rule: string;
  expected: string;
  actual: string;
  severity: "error" | "warning";
}

export interface ValidationReport {
  passed: boolean;
  issues: ValidationIssue[];
  calorie_deviation_pct: number;
}

export interface Explanation {
  summary: string;
  calorie_rationale: string;
  macro_rationale: string;
}

export interface CaloriesResult {
  bmr: number;
  tdee: number;
  target_calories: number;
  formula_used: string;
  goal: string;
  activity_level: string;
}

export interface MacroResult {
  target_calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface NutritionPlanResponse {
  run_id: string;
  success: boolean;
  profile?: any;
  calories_result?: CaloriesResult;
  macro_result?: MacroResult;
  retrieved_foods?: any;
  meal_plan?: MealPlan;
  triple_meal_plan?: TripleMealPlan;
  validation_report?: ValidationReport;
  explanation?: Explanation;
  error?: string;
}

export interface StreamEvent {
  run_id: string;
  node: string;
  status: "started" | "completed" | "failed" | "error";
  timestamp: string;
  data?: any;
}
