# LangGraph Implementation

> **Document Version:** 1.0.0
> **Status:** Design Phase

---

# 1. Overview

This document describes how the Nutrition AI System is implemented using **LangGraph**.

Unlike traditional chatbot workflows, our system is designed as a **Directed Execution Graph**, where every node has a single responsibility.

Each node receives a typed input, performs one task, and returns a typed output.

The Orchestrator is responsible for managing execution, retries, conditional routing, and streaming execution events.

---

# 2. Why LangGraph?

LangGraph was selected because it provides:

- Stateful workflow execution
- Conditional routing
- Retry support
- Human-in-the-loop support
- Streaming execution
- Tool integration
- Easy debugging
- Future memory support

Unlike simple LangChain chains, LangGraph models the workflow as a graph instead of a linear pipeline.

---

# 3. Graph Overview

```

START

↓

Profile Agent

↓

Calories Calculator

↓

Macro Calculator

↓

Food Retrieval Service

↓

Meal Composition Agent

↓

Validation Engine

↓

PASS ?

│

├──────── YES ───────────→ Explanation Agent → END

│

└──────── NO ───────────→ Retry Meal Composition

```

---

# 4. Graph Philosophy

Each node performs exactly one responsibility.

Nodes never call each other directly.

Instead:

```

Node

↓

Typed Output

↓

Orchestrator

↓

Next Node

```

This architecture makes every node reusable.

---

# 5. Node Definitions

## Profile Node

Input

```

GenerateNutritionRequest

```

Output

```

NutritionProfile

```

---

## Calories Node

Input

```

NutritionProfile

```

Output

```

CaloriesResult

```

---

## Macro Node

Input

```

CaloriesResult

```

Output

```

MacroResult

```

---

## Retrieval Node

Input

```

MacroResult

```

Output

```

RetrievedFoods

```

---

## Meal Composition Node

Input

```

RetrievedFoods

+

MacroResult

+

NutritionProfile

```

Output

```

MealPlan

```

---

## Validation Node

Input

```

MealPlan

```

Output

```

ValidationReport

```

---

## Explanation Node

Input

```

MealPlan

+

ValidationReport

```

Output

```

Explanation

```

---

# 6. Graph State Strategy

Unlike many LangGraph examples that use one large shared state, this project uses **Modular Typed States**.

Each node owns its own state model.

```

ProfileState

↓

CaloriesState

↓

MacroState

↓

RetrievalState

↓

PlanningState

↓

ValidationState

↓

ExplanationState

```

The Orchestrator maps outputs between these states.

Advantages:

- Easier testing
- Lower coupling
- Better maintainability
- Clear ownership

---

# 7. Node Execution Lifecycle

Every node follows the same execution pattern.

```

Receive Input

↓

Validate Input

↓

Execute Business Logic

↓

Call Tool / LLM

↓

Validate Output

↓

Return Result

```

---

# 8. Conditional Routing

LangGraph allows conditional execution.

The Validation Engine determines the next step.

```

Validation

↓

PASS ?

│

├──── YES ──────→ Explanation

│

└──── NO ───────→ Retry Planner

```

Only the Meal Composition Agent is retried.

No previous nodes are re-executed.

---

# 9. Retry Strategy

Retry policy:

Maximum Retries:

```

3

```

Flow:

```

Meal Composition

↓

Validation

↓

FAIL

↓

Retry

↓

Validation

↓

FAIL

↓

Retry

↓

Validation

↓

PASS

↓

Explanation

```

If all retries fail:

```

Return Best Candidate

+

Validation Report

```

---

# 10. Streaming Execution

Every node publishes lifecycle events.

```

Profile Started

↓

Profile Finished

↓

Calories Started

↓

Calories Finished

↓

Macro Started

↓

Macro Finished

↓

Retrieval Started

↓

Retrieval Finished

↓

Meal Planning Started

↓

Meal Planning Finished

↓

Validation Started

↓

Validation Finished

↓

Explanation Started

↓

Explanation Finished

```

These events are streamed through SSE or WebSocket.

---

# 11. Event Structure

Example event:

```json
{
  "run_id": "abc123",
  "node": "Meal Composition",
  "status": "running",
  "progress": 71
}
```

Completion event:

```json
{
  "run_id": "abc123",
  "node": "Validation",
  "status": "completed",
  "duration_ms": 243
}
```

Error event:

```json
{
  "run_id": "abc123",
  "node": "Meal Composition",
  "status": "failed",
  "reason": "Protein below target"
}
```

---

# 12. Execution Context

The Orchestrator maintains execution context.

Example:

```

Execution Context

│

├── User Profile

├── Calories Result

├── Macro Result

├── Retrieved Foods

├── Meal Plan

├── Validation Report

└── Explanation

```

This context is **not** shared directly between nodes.

The Orchestrator creates the appropriate input model for each node.

---

# 13. Error Handling

Possible node failures:

- Invalid profile
- Missing food results
- LLM timeout
- Invalid JSON output
- Validation failure

The Orchestrator decides whether to:

- Retry
- Abort
- Return fallback
- Continue

---

# 14. Future LangGraph Extensions

Future versions may introduce:

- Memory Nodes
- Human Approval Nodes
- Shopping Agent
- Supplement Agent
- Grocery Optimization
- Feedback Learning Node

Since LangGraph is graph-based, these nodes can be inserted without redesigning the workflow.

---

# 15. Graph Summary

```

START

↓

Profile

↓

Calories

↓

Macros

↓

Retrieve Foods

↓

Compose Meals

↓

Validate

↓

PASS?

│

├── YES

│      ↓

│ Explain

│      ↓

│ END

│

└── NO

↓

Retry Meal Composition

↓

Validate Again

```

---

# Next Document

The next document describes the complete **Data Architecture**, including the Master Food Database, PostgreSQL schema, ETL pipeline from USDA, metadata enrichment, and the retrieval strategy used by the Food Retrieval Service.

➡ **06_Data_Architecture.md**
