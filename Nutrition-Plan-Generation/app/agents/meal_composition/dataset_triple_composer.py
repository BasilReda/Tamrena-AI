"""
Dataset Triple Composer.

Deterministically creates three genuinely different MealPlan options from
RetrievedFoods while preserving the existing graph/API contract:
    meal_plan = option_a
    triple_meal_plan = {option_a, option_b, option_c}

No LLM calls are made here. The composer scores dataset candidates using the
retrieval metadata and applies increasing repetition/similarity penalties from
Option A → B → C.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import isfinite

from app.calculators.meal_distribution import run_meal_distribution
from app.core.logging import get_logger
from app.schemas.foods import FoodItem, RetrievedFoods
from app.schemas.profile import (
    MacroResult,
    Meal,
    MealDistribution,
    MealFoodItem,
    MealPlan,
    MealSlotTarget,
    TripleMealPlan,
)

logger = get_logger(__name__)

SIMILARITY_THRESHOLD = 0.62
VERY_LARGE_RECOMMENDATION_PENALTY = 10_000.0

_SLOT_ORDER = ["breakfast", "lunch", "dinner", "snack"]

_ROLE_PLANS: dict[str, dict[str, list[str]]] = {
    "balanced": {
        "breakfast": ["main carb", "protein", "fruit", "dairy", "healthy fat"],
        "lunch": ["main protein", "main carb", "vegetable", "healthy fat"],
        "dinner": ["main protein", "vegetable", "main carb", "healthy fat"],
        "snack": ["fruit", "dairy", "protein snack", "healthy snack"],
    },
    "high_protein": {
        "breakfast": ["protein", "dairy", "main carb", "fruit"],
        "lunch": ["main protein", "vegetable", "main carb", "healthy fat"],
        "dinner": ["main protein", "protein", "vegetable", "main carb"],
        "snack": ["protein snack", "dairy", "fruit"],
    },
    "max_diversity": {
        "breakfast": ["dairy", "fruit", "main carb", "healthy fat"],
        "lunch": ["main carb", "vegetable", "main protein", "healthy fat"],
        "dinner": ["vegetable", "main protein", "healthy fat", "main carb"],
        "snack": ["healthy snack", "fruit", "dairy", "protein snack"],
    },
}

_STRATEGY_NAMES = {
    "balanced": "Option A: balanced conservative dataset plan using highest-fit foods.",
    "high_protein": "Option B: higher-protein dataset plan with different food families.",
    "max_diversity": "Option C: maximum-diversity dataset plan avoiding earlier foods where possible.",
}

_PROTEIN_ROLES = {"main protein", "protein", "protein snack", "dairy"}
_CARB_ROLES = {"main carb", "healthy snack"}
_VEG_ROLES = {"vegetable"}
_FRUIT_ROLES = {"fruit"}
_FAT_ROLES = {"healthy fat"}

_INGREDIENT_KEYWORDS = {
    "additive",
    "flour",
    "defatted",
    "powder",
    "starch",
    "syrup",
    "molasses",
    "salt",
    "extract",
    "bran",
    "germ",
    "raw",
    "seed",
    "seeds",
    "meal",
    "baking",
    "cocoa",
    "glucose",
    "tapioca",
    "seasoning",
}

_ALWAYS_INGREDIENT_NAME_KEYWORDS = {
    "additive",
    "baking",
    "cocoa",
    "extract",
    "flour",
    "glucose",
    "molasses",
    "powder",
    "salt",
    "seasoning",
    "starch",
    "syrup",
    "tapioca",
}

_PREPARED_DISH_KEYWORDS = {
    "stuffed",
    "soup",
    "stew",
    "salad",
    "sandwich",
    "casserole",
    "grilled",
    "roasted",
    "cooked",
}

_SNACK_FRIENDLY_ROLES = {"fruit", "dairy", "protein snack", "healthy snack", "healthy fat", "beverage"}
_MEAL_ONLY_ROLES = {"main protein", "main carb", "vegetable"}


@dataclass(frozen=True)
class _FoodUse:
    food: FoodItem
    grams: float


def _norm(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def _role(food: FoodItem) -> str:
    return _norm(food.meal_role or "general")


def _safe(value: float) -> float:
    return value if isfinite(value) else 0.0


def _macro_density(food: FoodItem, macro: str) -> float:
    if macro == "protein":
        return food.protein_per_100g
    if macro == "carbs":
        return food.carbs_per_100g
    if macro == "fat":
        return food.fat_per_100g
    return food.calories_per_100g / 10.0


def _role_macro(role: str) -> str:
    if role in _PROTEIN_ROLES:
        return "protein"
    if role in _CARB_ROLES or role in _FRUIT_ROLES or role in _VEG_ROLES:
        return "carbs"
    if role in _FAT_ROLES:
        return "fat"
    return "calories"


def _category_for_desired_role(role: str) -> str:
    if role == "dairy":
        return "dairy"
    if role in _PROTEIN_ROLES:
        return "protein"
    if role in _CARB_ROLES:
        return "carb"
    if role in _VEG_ROLES:
        return "vegetable"
    if role in _FRUIT_ROLES:
        return "fruit"
    if role in _FAT_ROLES:
        return "fat"
    return "general"


def _category_for_food(food: FoodItem) -> str:
    role = _role(food)
    primary = _norm(food.primary_macro_type or "")
    group = _norm(food.food_group or "")
    if role == "dairy" or "dairy" in group:
        return "dairy"
    if role in _PROTEIN_ROLES or "protein" in primary:
        return "protein"
    if role in _CARB_ROLES or "carb" in primary or "grain" in group:
        return "carb"
    if role in _VEG_ROLES or "vegetable" in group:
        return "vegetable"
    if role in _FRUIT_ROLES or "fruit" in group:
        return "fruit"
    if role in _FAT_ROLES or "fat" in primary:
        return "fat"
    return role or "general"


def _food_signature_name(food_name: str) -> str:
    tokens = _norm(food_name).split()
    stop = {"breast", "cooked", "fresh", "raw", "low", "fat", "whole"}
    kept = [token for token in tokens if token not in stop]
    return kept[0] if kept else _norm(food_name)


def _is_family_name_match(a: str, b: str) -> bool:
    tokens_a = set(_norm(a).split())
    tokens_b = set(_norm(b).split())
    meaningful = {token for token in tokens_a & tokens_b if len(token) > 3}
    return bool(meaningful)


def _concept_key(food: FoodItem) -> str:
    """Collapse near-duplicate concepts like 'Stuffed Grape Leaves' and 'Grape Leaves'."""
    tokens = _norm(food.name).split()
    stop = {
        "stuffed",
        "plain",
        "fresh",
        "raw",
        "cooked",
        "grilled",
        "roasted",
        "boiled",
        "sliced",
        "whole",
        "low",
        "fat",
    }
    kept = [token for token in tokens if token not in stop]
    return " ".join(kept[-2:] if len(kept) >= 2 else kept) or _norm(food.name)


def _same_culinary_concept(food: FoodItem, other: FoodItem) -> bool:
    return _concept_key(food) == _concept_key(other) or _is_family_name_match(food.name, other.name)


def _is_ingredient_like(food: FoodItem) -> bool:
    name = _norm(food.name)
    role = _role(food)
    utility = _norm(food.macro_gap_utility_profile)
    group = _norm(food.food_group)
    if any(keyword in name for keyword in _PREPARED_DISH_KEYWORDS):
        return False
    if role in {"fruit", "vegetable", "main protein", "main carb", "dairy", "protein snack", "healthy snack"}:
        return any(keyword in name for keyword in _ALWAYS_INGREDIENT_NAME_KEYWORDS)
    return (
        any(keyword in name for keyword in _INGREDIENT_KEYWORDS)
        or "ingredient" in utility
        or "processing" in utility
        or "additive" in utility
        or "industrial" in utility
        or "baking" in utility
        or "seasoning" in utility
        or "flour" in group
        or "starch" in group
        or "ingredient" in group
        or "additive" in group
    )


def _is_prepared_dish(food: FoodItem) -> bool:
    name = _norm(food.name)
    return any(keyword in name for keyword in _PREPARED_DISH_KEYWORDS)


def _is_snack_suitable(food: FoodItem) -> bool:
    role = _role(food)
    if _is_ingredient_like(food):
        return False
    if role in _SNACK_FRIENDLY_ROLES:
        return True
    return "snack" in [_norm(slot) for slot in food.meal_slot_fit] and role not in {"vegetable", "main protein"}


def _meal_compatibility_score(food: FoodItem, chosen: list[FoodItem], slot_key: str) -> float:
    """Deterministic culinary coherence score for adding food to a partially built meal."""
    if not chosen:
        return 0.0

    category = _category_for_food(food)
    role = _role(food)
    chosen_categories = [_category_for_food(item) for item in chosen]
    chosen_roles = [_role(item) for item in chosen]
    chosen_names = {_norm(item.name) for item in chosen}
    score = 0.0

    if any(_norm(pair) in chosen_names for pair in food.best_with):
        score += 20.0
    if any(_norm(food.name) in {_norm(pair) for pair in item.best_with} for item in chosen):
        score += 16.0

    if category in chosen_categories:
        score -= 10.0
    if role in chosen_roles:
        score -= 12.0
    if _concept_key(food) in {_concept_key(item) for item in chosen}:
        score -= 45.0

    has_protein = "protein" in chosen_categories
    has_carb = "carb" in chosen_categories
    has_veg = "vegetable" in chosen_categories
    has_fruit = "fruit" in chosen_categories

    if slot_key == "breakfast":
        if category in {"carb", "fruit"} and any(_category_for_food(item) == "dairy" for item in chosen):
            score += 8.0
        if category == "vegetable" and has_fruit:
            score -= 14.0
    elif slot_key in {"lunch", "dinner"}:
        if category == "protein" and (has_carb or has_veg):
            score += 8.0
        if category == "carb" and (has_protein or has_veg):
            score += 8.0
        if category == "vegetable" and (has_protein or has_carb):
            score += 8.0
        if category == "fruit" and len(chosen) >= 2:
            score -= 10.0
    elif slot_key == "snack":
        if category in {"fruit", "dairy", "fat"}:
            score += 8.0
        if category in {"vegetable", "carb"} and has_fruit:
            score -= 8.0

    if _is_prepared_dish(food) and chosen:
        score -= 18.0
    if any(_is_prepared_dish(item) for item in chosen) and category not in {"vegetable", "fruit", "dairy"}:
        score -= 14.0

    return score


class DatasetTripleComposer:
    """Create deterministic, diverse TripleMealPlan objects from retrieved foods."""

    def __init__(self, macro_result: MacroResult, retrieved_foods: RetrievedFoods):
        self.macro_result = macro_result
        self.retrieved_foods = retrieved_foods
        self.meal_distribution = run_meal_distribution(macro_result)
        self.foods = retrieved_foods.all_foods
        self._candidate_by_name = {_norm(food.name): food for food in self.foods}

    def compose(self) -> TripleMealPlan:
        if not self.foods:
            raise ValueError("DatasetTripleComposer requires at least one retrieved food.")

        used_counts: Counter[str] = Counter()
        previous_plans: list[MealPlan] = []

        option_a = self._compose_option("balanced", used_counts, previous_plans)
        self._record_usage(option_a, used_counts)
        previous_plans.append(option_a)

        option_b = self._compose_option("high_protein", used_counts, previous_plans)
        self._record_usage(option_b, used_counts)
        previous_plans.append(option_b)

        option_c = self._compose_option("max_diversity", used_counts, previous_plans)
        previous_plans.append(option_c)

        logger.info(
            "DatasetTripleComposer complete | sim(A,B)=%.2f sim(A,C)=%.2f sim(B,C)=%.2f",
            calculate_plan_similarity(option_a, option_b, self.retrieved_foods),
            calculate_plan_similarity(option_a, option_c, self.retrieved_foods),
            calculate_plan_similarity(option_b, option_c, self.retrieved_foods),
        )

        return TripleMealPlan(
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            meal_distribution=self.meal_distribution,
            notes=" | ".join(_STRATEGY_NAMES.values()),
        )

    def _compose_option(
        self,
        strategy: str,
        used_counts: Counter[str],
        previous_plans: list[MealPlan],
    ) -> MealPlan:
        selected: dict[str, Meal] = {}
        plan_food_names: set[str] = set()
        slot_targets = {
            "breakfast": self.meal_distribution.breakfast,
            "lunch": self.meal_distribution.lunch,
            "dinner": self.meal_distribution.dinner,
            "snack": self.meal_distribution.snack,
        }

        for slot_key in _SLOT_ORDER:
            selected[slot_key] = self._compose_meal(
                slot_targets[slot_key], strategy, used_counts, previous_plans, plan_food_names
            )
            plan_food_names.update(_norm(item.name) for item in selected[slot_key].foods)

        plan = _build_plan(selected, self.meal_distribution, _STRATEGY_NAMES[strategy])
        if previous_plans and self._is_too_similar(plan, previous_plans):
            plan = self._compose_with_stronger_diversity(strategy, used_counts, previous_plans)
        return plan

    def _compose_with_stronger_diversity(
        self,
        strategy: str,
        used_counts: Counter[str],
        previous_plans: list[MealPlan],
    ) -> MealPlan:
        amplified = Counter({name: count + 2 for name, count in used_counts.items()})
        selected: dict[str, Meal] = {}
        plan_food_names: set[str] = set()
        for slot in [
            self.meal_distribution.breakfast,
            self.meal_distribution.lunch,
            self.meal_distribution.dinner,
            self.meal_distribution.snack,
        ]:
            selected[slot.slot_key] = self._compose_meal(
                slot, strategy, amplified, previous_plans, plan_food_names
            )
            plan_food_names.update(_norm(item.name) for item in selected[slot.slot_key].foods)
        return _build_plan(selected, self.meal_distribution, _STRATEGY_NAMES[strategy])

    def _compose_meal(
        self,
        slot: MealSlotTarget,
        strategy: str,
        used_counts: Counter[str],
        previous_plans: list[MealPlan],
        current_plan_food_names: set[str],
    ) -> Meal:
        roles = _ROLE_PLANS[strategy][slot.slot_key]
        chosen: list[FoodItem] = []

        for desired_role in roles:
            candidate = self._best_candidate(
                slot=slot,
                desired_role=desired_role,
                strategy=strategy,
                used_counts=used_counts,
                chosen=chosen,
                previous_plans=previous_plans,
                current_plan_food_names=current_plan_food_names,
            )
            if (
                candidate is not None
                and _norm(candidate.name) not in {_norm(food.name) for food in chosen}
                and not any(_same_culinary_concept(candidate, food) for food in chosen)
                and (slot.slot_key != "snack" or _is_snack_suitable(candidate))
            ):
                chosen.append(candidate)

        if not chosen:
            chosen.append(max(self.foods, key=lambda food: self._score_food(food, slot, "general", strategy, used_counts, [], previous_plans, current_plan_food_names)))

        uses = self._assign_servings(chosen, slot)
        meal_items = [_to_meal_food_item(use) for use in uses]
        return Meal(
            meal_name=slot.meal_name,
            foods=meal_items,
            total_calories=round(sum(item.calories for item in meal_items), 1),
            total_protein_g=round(sum(item.protein_g for item in meal_items), 1),
            total_carbs_g=round(sum(item.carbs_g for item in meal_items), 1),
            total_fat_g=round(sum(item.fat_g for item in meal_items), 1),
        )

    def _best_candidate(
        self,
        slot: MealSlotTarget,
        desired_role: str,
        strategy: str,
        used_counts: Counter[str],
        chosen: list[FoodItem],
        previous_plans: list[MealPlan],
        current_plan_food_names: set[str],
    ) -> FoodItem | None:
        desired = _norm(desired_role)
        exact = [food for food in self.foods if _role(food) == desired]
        pool = exact if exact else self.foods

        day_foods = self._foods_from_names(current_plan_food_names)

        # If a strict role bucket only contains foods already used today, broaden
        # within the same culinary category before accepting a visible repeat.
        if exact and day_foods and all(any(_same_culinary_concept(food, used) for used in day_foods) for food in exact):
            desired_category = _category_for_desired_role(desired)
            broader = [food for food in self.foods if _category_for_food(food) == desired_category]
            if broader:
                pool = broader

        # Ingredient-like foods are fallback-only. Apply this before diversity
        # filters so rotation pressure cannot accidentally force flours/powders.
        edible_pool = [food for food in pool if not _is_ingredient_like(food)]
        if edible_pool:
            pool = edible_pool

        if strategy != "balanced" and previous_plans:
            previous_foods = self._foods_from_previous_plans(previous_plans)
            unseen_pool = [
                food
                for food in pool
                if not any(_same_culinary_concept(food, previous_food) for previous_food in previous_foods)
            ]
            if unseen_pool and any(
                not any(_same_culinary_concept(food, day_food) for day_food in day_foods)
                for food in unseen_pool
            ):
                pool = unseen_pool

        if chosen:
            chosen_concepts = {_concept_key(food) for food in chosen}
            concept_distinct = [food for food in pool if _concept_key(food) not in chosen_concepts]
            if concept_distinct:
                pool = concept_distinct

            chosen_categories = [_category_for_food(food) for food in chosen]
            category_distinct = [food for food in pool if _category_for_food(food) not in chosen_categories]
            if category_distinct and (slot.slot_key == "snack" or desired in {"main protein", "main carb", "vegetable", "fruit"}):
                pool = category_distinct

        # Prefer replacement over serving-size tricks: once a culinary concept is
        # already used in the day, choose another identity when the pool allows it.
        concept_pool = [
            food
            for food in pool
            if not any(_same_culinary_concept(food, day_food) for day_food in day_foods)
        ]
        if concept_pool:
            pool = concept_pool

        # Rotate visible anchors by category so a day looks like a menu rather
        # than repeated high-scoring staples.
        category_pool = self._category_rotated_pool(pool, day_foods, slot.slot_key)
        if category_pool:
            pool = category_pool

        # Snacks need stricter culinary filtering. If enough snack-like foods exist,
        # avoid forcing meal-only items just because they score well nutritionally.
        if slot.slot_key == "snack":
            snack_pool = [food for food in pool if _is_snack_suitable(food)]
            if snack_pool:
                pool = snack_pool

        return max(
            pool,
            key=lambda food: self._score_food(
                food, slot, desired, strategy, used_counts, chosen, previous_plans, current_plan_food_names
            ),
            default=None,
        )

    def _foods_from_names(self, names: set[str]) -> list[FoodItem]:
        return [food for name in names if (food := self._candidate_by_name.get(name))]

    def _foods_from_previous_plans(self, previous_plans: list[MealPlan]) -> list[FoodItem]:
        foods: list[FoodItem] = []
        for plan in previous_plans:
            foods.extend(
                food for item in _plan_items(plan) if (food := self._candidate_by_name.get(_norm(item.name)))
            )
        return foods

    def _category_rotated_pool(
        self,
        pool: list[FoodItem],
        day_foods: list[FoodItem],
        slot_key: str,
    ) -> list[FoodItem]:
        if not day_foods:
            return pool

        rotated = pool
        for category in ["protein", "carb", "vegetable", "fruit", "dairy"]:
            if not any(_category_for_food(food) == category for food in pool):
                continue
            used_in_category = [food for food in day_foods if _category_for_food(food) == category]
            if not used_in_category:
                continue
            candidates = [
                food
                for food in rotated
                if _category_for_food(food) != category
                or not any(_same_culinary_concept(food, used) for used in used_in_category)
            ]
            if candidates:
                rotated = candidates

        if slot_key == "snack":
            snack_candidates = [food for food in rotated if _is_snack_suitable(food)]
            if snack_candidates:
                return snack_candidates
        return rotated

    def _score_food(
        self,
        food: FoodItem,
        slot: MealSlotTarget,
        desired_role: str,
        strategy: str,
        used_counts: Counter[str],
        chosen: list[FoodItem],
        previous_plans: list[MealPlan],
        current_plan_food_names: set[str],
    ) -> float:
        name = _norm(food.name)
        role = _role(food)
        goal = _norm(self.macro_result.goal)
        diet = _norm(self.macro_result.diet_type)
        primary = _norm(food.primary_macro_type)
        utility = _norm(food.macro_gap_utility_profile)

        score = 0.0
        score += _safe(food.selection_priority) * 3.0
        score += 18.0 if role == desired_role else 0.0
        score += 12.0 if slot.slot_key in [_norm(s) for s in food.meal_slot_fit] else 0.0
        score += 8.0 if goal in [_norm(tag) for tag in food.goal_fit_tags] else 0.0
        score += 4.0 if "maintenance" in [_norm(tag) for tag in food.goal_fit_tags] else 0.0
        score += 7.0 if diet in {"normal", "omnivore"} or diet in [_norm(d) for d in food.diet_profile + food.diet_types] else -12.0

        desired_macro = _role_macro(desired_role)
        score += min(_macro_density(food, desired_macro), 35.0) * 0.7
        score += 5.0 if desired_macro in primary or desired_macro in utility else 0.0

        chosen_names = {_norm(chosen_food.name) for chosen_food in chosen}
        chosen_roles = {_role(chosen_food) for chosen_food in chosen}
        chosen_concepts = {_concept_key(chosen_food) for chosen_food in chosen}
        chosen_best_with = {
            _norm(pair)
            for chosen_food in chosen
            for pair in chosen_food.best_with
        }

        score += _meal_compatibility_score(food, chosen, slot.slot_key)

        if any(_norm(pair) in chosen_names for pair in food.best_with):
            score += 18.0
        if name in chosen_best_with:
            score += 14.0
        if role in chosen_roles:
            score -= 18.0
        if _concept_key(food) in chosen_concepts:
            score -= 60.0
        if name in current_plan_food_names:
            score -= 34.0

        day_foods = self._foods_from_names(current_plan_food_names)
        same_day_concepts = sum(1 for day_food in day_foods if _same_culinary_concept(food, day_food))
        if same_day_concepts:
            score -= same_day_concepts * 75.0

        category = _category_for_food(food)
        same_day_category = sum(1 for day_food in day_foods if _category_for_food(day_food) == category)
        rotation_penalty = {"protein": 28.0, "carb": 24.0, "vegetable": 22.0, "fruit": 26.0, "dairy": 18.0}.get(category, 8.0)
        score -= same_day_category * rotation_penalty

        if _is_ingredient_like(food):
            score -= VERY_LARGE_RECOMMENDATION_PENALTY
            if chosen:
                score -= 35.0

        if slot.slot_key == "snack":
            if _is_snack_suitable(food):
                score += 18.0
            if role in _MEAL_ONLY_ROLES or _is_ingredient_like(food):
                score -= 70.0
        elif slot.slot_key in {"lunch", "dinner"} and role in {"fruit", "dairy"} and len(chosen) >= 2:
            score -= 14.0

        # Prefer coherent category balance: one anchor protein/carb/vegetable/fat
        # instead of multiple foods from the same family.
        chosen_categories = [_category_for_food(chosen_food) for chosen_food in chosen]
        if category in chosen_categories:
            score -= 16.0
        if slot.slot_key in {"lunch", "dinner"} and category in {"protein", "carb", "vegetable", "fat"}:
            score += 6.0
        if slot.slot_key == "breakfast" and category in {"carb", "protein", "dairy", "fruit", "fat"}:
            score += 5.0

        repetition_multiplier = {"balanced": 16.0, "high_protein": 30.0, "max_diversity": 46.0}[strategy]
        score -= used_counts[name] * repetition_multiplier
        score -= sum(used_counts[prior_name] for prior_name, prior_food in self._candidate_by_name.items() if _concept_key(prior_food) == _concept_key(food)) * 18.0
        score -= self._source_seen_count(food, previous_plans) * (8.0 if strategy != "max_diversity" else 18.0)

        if strategy == "high_protein" and (role in _PROTEIN_ROLES or "protein" in primary):
            score += 14.0
        if strategy == "max_diversity":
            score += 4.0 - min(food.selection_priority, 4.0) * 0.3

        return score

    def _source_seen_count(self, food: FoodItem, previous_plans: list[MealPlan]) -> int:
        source = _food_signature_name(food.name)
        category = _category_for_food(food)
        count = 0
        for plan in previous_plans:
            for item in _plan_items(plan):
                prior = self._candidate_by_name.get(_norm(item.name))
                if prior and _category_for_food(prior) == category and (
                    _food_signature_name(prior.name) == source or _same_culinary_concept(food, prior)
                ):
                    count += 1
        return count

    def _assign_servings(self, foods: list[FoodItem], slot: MealSlotTarget) -> list[_FoodUse]:
        uses: list[_FoodUse] = []
        role_groups = {
            "protein": [f for f in foods if _role(f) in _PROTEIN_ROLES],
            "carbs": [f for f in foods if _role(f) in _CARB_ROLES or _role(f) in _FRUIT_ROLES or _role(f) in _VEG_ROLES],
            "fat": [f for f in foods if _role(f) in _FAT_ROLES],
        }

        # First pass: allocate grams from the slot target with role-aware division.
        for food in foods:
            macro = _role_macro(_role(food))
            if macro == "protein" and food.protein_per_100g > 0:
                grams = slot.target_protein_g / max(1, len(role_groups["protein"])) / food.protein_per_100g * 100
            elif macro == "carbs" and food.carbs_per_100g > 0:
                grams = slot.target_carbs_g / max(1, len(role_groups["carbs"])) / food.carbs_per_100g * 100
            elif macro == "fat" and food.fat_per_100g > 0:
                grams = slot.target_fat_g / max(1, len(role_groups["fat"])) / food.fat_per_100g * 100
            else:
                grams = slot.target_calories / max(1, len(foods)) / max(food.calories_per_100g, 1) * 100
            uses.append(_FoodUse(food, _bounded_grams(grams, food)))

        def _totals(items: list[_FoodUse]) -> tuple[float, float, float, float]:
            cal = sum(use.food.calories_per_100g * use.grams / 100 for use in items)
            pro = sum(use.food.protein_per_100g * use.grams / 100 for use in items)
            car = sum(use.food.carbs_per_100g * use.grams / 100 for use in items)
            fat = sum(use.food.fat_per_100g * use.grams / 100 for use in items)
            return cal, pro, car, fat

        cal, pro, car, fat = _totals(uses)
        protein_factor = slot.target_protein_g / pro if pro > 0 else 1.0
        carb_factor = slot.target_carbs_g / car if car > 0 else 1.0
        fat_factor = slot.target_fat_g / fat if fat > 0 else 1.0
        calorie_factor = slot.target_calories / cal if cal > 0 else 1.0

        adjusted: list[_FoodUse] = []
        for use in uses:
            macro = _role_macro(_role(use.food))
            if macro == "protein":
                factor = protein_factor
            elif macro == "carbs":
                factor = carb_factor
            elif macro == "fat":
                factor = fat_factor
            else:
                factor = (protein_factor + carb_factor + fat_factor + calorie_factor) / 4.0
            factor = max(0.72, min(factor, 1.18))
            adjusted.append(_FoodUse(use.food, _bounded_grams(use.grams * factor, use.food)))

        cal2, pro2, car2, fat2 = _totals(adjusted)
        if cal2 > 0:
            # Gentle calorie correction while keeping macro-specific adjustments intact.
            blend = slot.target_calories / cal2
            blend = max(0.9, min(blend, 1.1))
            adjusted = [_FoodUse(use.food, _bounded_grams(use.grams * blend, use.food)) for use in adjusted]

        return adjusted

    def _record_usage(self, plan: MealPlan, used_counts: Counter[str]) -> None:
        for item in _plan_items(plan):
            used_counts[_norm(item.name)] += 1

    def _is_too_similar(self, plan: MealPlan, previous_plans: list[MealPlan]) -> bool:
        return any(
            calculate_plan_similarity(plan, previous, self.retrieved_foods) > SIMILARITY_THRESHOLD
            for previous in previous_plans
        )


def compose_dataset_triple_meal_plan(
    macro_result: MacroResult,
    retrieved_foods: RetrievedFoods,
) -> TripleMealPlan:
    """Public entrypoint used by the dataset graph node."""
    return DatasetTripleComposer(macro_result, retrieved_foods).compose()


def calculate_plan_similarity(
    plan_a: MealPlan,
    plan_b: MealPlan,
    retrieved_foods: RetrievedFoods | None = None,
) -> float:
    """Weighted overlap score in [0, 1]; lower means more meaningfully different."""
    sig_a = _plan_signature(plan_a, retrieved_foods)
    sig_b = _plan_signature(plan_b, retrieved_foods)
    weights = {
        "foods": 0.28,
        "proteins": 0.22,
        "carbs": 0.18,
        "vegetables": 0.12,
        "fruits": 0.10,
        "role_patterns": 0.10,
    }
    return round(sum(weights[key] * _jaccard(sig_a[key], sig_b[key]) for key in weights), 4)


def _plan_signature(plan: MealPlan, retrieved_foods: RetrievedFoods | None) -> dict[str, set[str]]:
    index = {_norm(food.name): food for food in retrieved_foods.all_foods} if retrieved_foods else {}
    signature: dict[str, set[str]] = {
        "foods": set(),
        "proteins": set(),
        "carbs": set(),
        "vegetables": set(),
        "fruits": set(),
        "role_patterns": set(),
    }
    for slot, meal in _plan_meals(plan):
        roles = []
        for item in meal.foods:
            name = _norm(item.name)
            signature["foods"].add(name)
            food = index.get(name)
            role = _role(food) if food else "general"
            roles.append(role)
            source = _food_signature_name(item.name)
            category = _category_for_food(food) if food else role
            if category == "protein":
                signature["proteins"].add(source)
            elif category == "carb":
                signature["carbs"].add(source)
            elif category == "vegetable":
                signature["vegetables"].add(source)
            elif category == "fruit":
                signature["fruits"].add(source)
        signature["role_patterns"].add(f"{slot}:{'-'.join(sorted(set(roles)))}")
    return signature


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _plan_meals(plan: MealPlan) -> list[tuple[str, Meal]]:
    meals = [("breakfast", plan.breakfast), ("lunch", plan.lunch), ("dinner", plan.dinner)]
    if plan.snack:
        meals.append(("snack", plan.snack))
    return meals


def _plan_items(plan: MealPlan) -> list[MealFoodItem]:
    return [item for _, meal in _plan_meals(plan) for item in meal.foods]


def _to_meal_food_item(use: _FoodUse) -> MealFoodItem:
    factor = use.grams / 100
    return MealFoodItem(
        name=use.food.name,
        serving_grams=round(use.grams, 1),
        calories=round(use.food.calories_per_100g * factor, 1),
        protein_g=round(use.food.protein_per_100g * factor, 1),
        carbs_g=round(use.food.carbs_per_100g * factor, 1),
        fat_g=round(use.food.fat_per_100g * factor, 1),
    )


def _bounded_grams(grams: float, food: FoodItem) -> float:
    role = _role(food)
    if role in _FAT_ROLES:
        return min(max(grams, 5.0), 45.0)
    if role in _VEG_ROLES:
        return min(max(grams, 50.0), 300.0)
    if role in _FRUIT_ROLES:
        return min(max(grams, 50.0), 250.0)
    return min(max(grams, 25.0), 350.0)


def _build_plan(slots: dict[str, Meal], distribution: MealDistribution, notes: str) -> MealPlan:
    meals = [slots["breakfast"], slots["lunch"], slots["dinner"], slots["snack"]]
    return MealPlan(
        breakfast=slots["breakfast"],
        lunch=slots["lunch"],
        dinner=slots["dinner"],
        snack=slots["snack"],
        total_daily_calories=round(sum(meal.total_calories for meal in meals), 1),
        total_daily_protein_g=round(sum(meal.total_protein_g for meal in meals), 1),
        total_daily_carbs_g=round(sum(meal.total_carbs_g for meal in meals), 1),
        total_daily_fat_g=round(sum(meal.total_fat_g for meal in meals), 1),
        notes=notes,
    )