# Food Retrieval

> **Document Version:** 1.0.0
> **Status:** MVP Design
> **Related Documents**
>
> - 05_LangGraph_Implementation.md
> - 06_Data_Architecture.md

---

# 1. Overview

The Food Retrieval component is responsible for supplying the Meal Composition Agent with a list of food candidates that satisfy the user's nutritional requirements.

Instead of allowing the LLM to generate foods from its internal knowledge, the system retrieves verified food items from a structured dataset.

For the first MVP, the food dataset is stored locally as a **CSV/Parquet** file and queried using **Pandas**.

This design keeps the implementation simple while remaining fully replaceable with PostgreSQL in future versions.

---

# 2. Why Pandas?

The initial food database contains only a few thousand food items.

For datasets of this size, Pandas provides:

- Extremely fast filtering
- Simple implementation
- No database setup
- Easy debugging
- Easy data inspection
- Fast iteration during development

The repository layer isolates the data source, allowing migration to PostgreSQL without changing business logic.

---

# 3. Architecture

```
                  User Profile
                        │
                        ▼
              Calories Calculator
                        │
                        ▼
               Macro Calculator
                        │
                        ▼
               Food Repository
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Load Dataset   Apply Filters     Rank Foods
        │               │                │
        └───────────────┼────────────────┘
                        ▼
              Candidate Food List
                        │
                        ▼
          Meal Composition Agent
```

---

# 4. Food Repository Pattern

The Meal Composition Agent never reads the dataset directly.

Instead, all food access is handled through the Food Repository.

```
Meal Composition Agent

        │

        ▼

Food Repository

        │

        ▼

Pandas Dataset
```

This abstraction allows changing the storage implementation without modifying any AI components.

---

# 5. Repository Responsibilities

The Food Repository is responsible for:

- Loading the dataset
- Applying nutritional filters
- Applying dietary restrictions
- Filtering allergens
- Selecting meal categories
- Ranking candidate foods
- Returning structured food objects

It does not generate meal plans or perform reasoning.

---

# 6. Dataset

The repository loads a single master dataset.

Example:

```
foods.parquet
```

or

```
foods.csv
```

The dataset is loaded once during application startup.

---

# 7. Expected Dataset Schema

| Column | Description |
|---------|-------------|
| food_id | Internal ID |
| food_name | Food Name |
| arabic_name | Arabic Name |
| calories | Calories per 100g |
| protein | Protein |
| carbohydrates | Carbohydrates |
| fat | Fat |
| fiber | Fiber |
| food_group | Protein, Carb, Dairy... |
| meal_type | Breakfast, Lunch, Dinner, Snack |
| cuisine | Egyptian, International |
| diet_type | Normal, Vegetarian, Vegan |
| allergens | Allergens |
| serving_size | Standard Serving |

Additional metadata may be added as needed.

---

# 8. Retrieval Pipeline

The retrieval process follows multiple filtering stages.

```
Load Dataset

↓

Calories Filter

↓

Protein Filter

↓

Carbohydrate Filter

↓

Fat Filter

↓

Meal Type Filter

↓

Diet Filter

↓

Allergy Filter

↓

Preference Filter

↓

Ranking

↓

Top Candidate Foods
```

Each stage reduces the search space before ranking.

---

# 9. Filtering Strategy

Typical filters include:

### Calories

Example:

```
Calories <= 250
```

---

### Protein

```
Protein >= 20g
```

---

### Meal Type

```
Breakfast
```

---

### Cuisine

```
Egyptian
```

---

### Diet

```
High Protein
```

---

### Allergies

Remove foods containing:

- Nuts
- Dairy
- Gluten

depending on the user's profile.

---

# 10. Ranking

After filtering, foods are ranked according to:

- Protein density
- Calorie efficiency
- Nutritional quality
- User preferences
- Meal suitability

Only the highest-ranked candidates are returned.

Typical output:

```
Top 20 Foods
```

---

# 11. Output Format

The repository returns structured food objects.

Example:

```python
Food(
    id=15,
    name="Chicken Breast",
    calories=165,
    protein=31,
    carbs=0,
    fat=3.6,
    meal_type="Lunch"
)
```

The Meal Composition Agent never interacts with raw DataFrames.

---

# 12. Future Database Migration

The Repository Pattern isolates storage implementation.

Current implementation:

```
Food Repository

↓

Pandas
```

Future implementation:

```
Food Repository

↓

PostgreSQL
```

Later:

```
Food Repository

↓

PostgreSQL

+

Redis Cache

+

Vector Search

+

External Food APIs
```

The public interface remains unchanged.

---

# 13. Repository Interface

Example responsibilities:

```
load_dataset()

get_candidate_foods()

filter_by_calories()

filter_by_macros()

filter_by_preferences()

filter_by_allergies()

rank_foods()
```

These methods form the core API of the retrieval layer.

---

# 14. Performance Considerations

To improve performance:

- Load the dataset only once during startup.
- Store it in memory as a DataFrame.
- Avoid reading the file for every request.
- Apply vectorized Pandas operations.
- Return only the required columns.

For the expected dataset size, this approach is sufficient for real-time inference.

---

# 15. Future Enhancements

Future versions may introduce:

- PostgreSQL storage
- Redis caching
- pgvector semantic search
- BM25 ranking
- Food popularity scoring
- Seasonal food availability
- Budget-aware filtering
- Personalized ranking based on user history

The repository abstraction ensures these upgrades require no changes to the Meal Composition Agent.

---

# 16. Design Decisions

| Decision | Reason |
|----------|--------|
| Pandas for MVP | Simple and fast for small datasets |
| Repository Pattern | Decouple data access from business logic |
| In-memory DataFrame | Minimize file I/O |
| Filtering before LLM | Reduce prompt size and hallucinations |
| Structured outputs | Simplify downstream processing |
| Replaceable storage | Easy migration to PostgreSQL |

---

# 17. Return Schema

{
    "proteins": [...],
    "carbohydrates": [...],
    "healthy_fats": [...],
    "vegetables": [...],
    "fruits": [...],
    "dairy": [...]
}

# Next Document

The next document describes the REST API endpoints, request/response models, streaming events, and integration with the frontend.

➡ **08_API_Design.md**