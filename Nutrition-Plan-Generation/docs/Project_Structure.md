# Project Structure

> **Document Version:** 1.0.0
> **Status:** MVP Design

---

# 1. Overview

The Nutrition AI System follows a modular, domain-driven architecture to ensure maintainability, scalability, and clear separation of responsibilities.

Each layer has a single responsibility, making the system easier to test, extend, and deploy.

---

# 2. High-Level Structure

```
nutrition-ai-system/
│
├── app/
│
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── profile.py
│   │   │   ├── nutrition.py
│   │   │   └── health.py
│   │   │
│   │   ├── dependencies.py
│   │   └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   └── constants.py
│   │
│   ├── agents/
│   │   ├── profile/
│   │   ├── meal_composition/
│   │   └── explanation/
│   │
│   ├── calculators/
│   │   ├── calories.py
│   │   └── macros.py
│   │
│   ├── retrieval/
│   │   ├── repository.py
│   │   ├── filters.py
│   │   ├── ranking.py
│   │   └── loader.py
│   │
│   ├── validation/
│   │   ├── validator.py
│   │   └── rules.py
│   │
│   ├── graph/
│   │   ├── graph.py
│   │   ├── builder.py
│   │   ├── routing.py
│   │   └── streaming.py
│   │
│   ├── state/
│   │   ├── profile_state.py
│   │   ├── calories_state.py
│   │   ├── macro_state.py
│   │   ├── retrieval_state.py
│   │   ├── planning_state.py
│   │   ├── validation_state.py
│   │   └── explanation_state.py
│   │
│   ├── prompts/
│   │   ├── meal_prompt.py
│   │   ├── profile_prompt.py
│   │   └── explanation_prompt.py
│   │
│   ├── schemas/
│   │   ├── request.py
│   │   ├── response.py
│   │   ├── foods.py
│   │   └── profile.py
│   │
│   ├── services/
│   │   ├── nutrition_service.py
│   │   └── stream_service.py
│   │
│   ├── data/
│   │   ├── foods.parquet
│   │   └── metadata/
│   │
│   ├── utils/
│   │   ├── units.py
│   │   ├── converters.py
│   │   └── helpers.py
│   │
│   ├── main.py
│   │
│   └── __init__.py
│
├── tests/
│
│   ├── agents/
│   ├── calculators/
│   ├── retrieval/
│   ├── validation/
│   └── api/
│
├── docs/
│
├── scripts/
│   ├── build_food_dataset.py
│   ├── clean_dataset.py
│   └── import_usda.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
```

---

# 3. Directory Responsibilities

## api/

Contains all REST API endpoints exposed by FastAPI.

Responsible for:

- Authentication
- Profile APIs
- Nutrition APIs
- Health Checks

---

## agents/

Contains all LLM-powered agents.

Current agents:

- Profile Agent
- Meal Composition Agent
- Explanation Agent

Each agent owns:

- Prompt
- Node Logic
- Output Parsing

---

## calculators/

Contains deterministic business logic.

Examples:

- Calories Calculator
- Macro Calculator

No AI model is used inside this directory.

---

## retrieval/

Responsible for retrieving candidate foods.

Contains:

- Dataset Loader
- Repository
- Filters
- Ranking Logic

The Meal Composition Agent interacts only with the Repository.

---

## validation/

Responsible for validating generated meal plans.

Examples:

- Calories validation
- Protein validation
- Allergy validation
- Meal completeness

No LLM is used.

---

## graph/

Contains the LangGraph implementation.

Responsible for:

- Graph creation
- Node registration
- Conditional routing
- Retry logic
- Streaming integration

---

## state/

Defines typed state models exchanged between graph nodes.

Each node has its own dedicated state object.

Examples:

- ProfileState
- MacroState
- PlanningState

---

## prompts/

Stores all prompt templates.

Keeping prompts separate from business logic makes prompt engineering easier.

---

## schemas/

Contains all Pydantic request and response models.

Examples:

- API requests
- API responses
- Food models
- User profile models

---

## services/

Application-level services coordinating APIs and graph execution.

Examples:

- Nutrition Service
- Streaming Service

---

## data/

Stores local datasets used by the MVP.

Examples:

- foods.parquet
- food metadata
- aliases

Future versions may replace this layer with PostgreSQL.

---

## utils/

Reusable helper functions.

Examples:

- Unit conversion
- Date utilities
- Common helper methods

---

## tests/

Contains automated tests.

Suggested structure:

```
tests/

├── unit/

├── integration/

└── api/
```

Every major component should have dedicated unit tests.

---

# 4. LangGraph Organization

The graph implementation is isolated from business logic.

```
graph/

├── builder.py
├── graph.py
├── routing.py
└── streaming.py
```

Responsibilities:

- Build workflow
- Register nodes
- Connect edges
- Handle retries
- Publish events

---

# 5. Agent Organization

Each agent should have its own package.

Example:

```
agents/

└── meal_composition/

    ├── agent.py
    ├── node.py
    ├── prompt.py
    ├── parser.py
    └── models.py
```

Benefits:

- Independent testing
- Easier maintenance
- Clear ownership

---

# 6. Retrieval Organization

```
retrieval/

├── loader.py
├── repository.py
├── filters.py
├── ranking.py
└── models.py
```

The repository abstracts the data source, allowing migration from Pandas to PostgreSQL without affecting downstream components.

---

# 7. Configuration Management

Application settings are centralized.

```
core/

config.py
```

Configuration examples:

- API Keys
- Model Names
- File Paths
- Retry Limits
- Streaming Settings

Environment-specific values should be loaded from `.env`.

---

# 8. Design Principles

The project follows these principles:

- Single Responsibility Principle (SRP)
- Dependency Injection
- Repository Pattern
- Separation of Concerns
- Modular LangGraph Nodes
- Typed Data Models
- Deterministic Calculations
- LLM for Reasoning Only

---

# 9. Future Expansion

The structure is designed to support future additions without major refactoring.

Potential future modules:

- workout/
- vision/
- grocery/
- shopping/
- wearable/
- recommendations/
- analytics/
- memory/

Each new domain can be added as an independent module.

---

# 10. Summary

The proposed project structure separates API endpoints, AI agents, deterministic services, retrieval logic, validation, and workflow orchestration into independent modules.

This modular design simplifies development, testing, collaboration, and future scaling while keeping the codebase clean and maintainable.

---

# Next Document

➡ **11_Deployment.md**