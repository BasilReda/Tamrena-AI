# System Architecture

> **Document Version:** 1.0.0  
> **Status:** Design Phase  
> **Related Document:** 01_Project_Overview.md

---

# 1. Architecture Overview

The Nutrition AI System follows a modular, service-oriented architecture centered around a **Multi-Agent AI Engine**.

Instead of allowing a single AI model to make all nutrition-related decisions, the application decomposes the entire workflow into multiple specialized agents orchestrated through LangGraph.

Each component is designed to be independent, reusable, and easily maintainable.

---

# 2. High-Level Architecture

```
                              User
                                │
                                ▼
                     ┌────────────────────┐
                     │     Web Client     │
                     └────────────────────┘
                                │
                         HTTP / SSE
                                │
                                ▼
                     ┌────────────────────┐
                     │      FastAPI       │
                     └────────────────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │  Orchestrator (Graph)   │
                  └─────────────────────────┘
                                │
        ┌──────────────┬─────────┼─────────┬──────────────┐
        ▼              ▼         ▼         ▼              ▼
 Profile Agent   Calories   Macro Agent Retrieval   Planning Agent
                     │                      │              │
                     └──────────────┬───────┘              │
                                    ▼                      │
                          Validation Agent                 │
                                    │                      │
                          ┌─────────┴──────────┐           │
                          │                    │           │
                     Validation Pass      Validation Fail  │
                          │                    │           │
                          ▼                    │           │
                 Explanation Agent            │           │
                          │                    │           │
                          ▼                    │           │
                 Personalized Nutrition Plan ◄┘
```

---

# 3. Architecture Layers

The system is divided into multiple logical layers.

```
Presentation Layer
        │
API Layer
        │
Application Layer
        │
AI Agent Layer
        │
Knowledge Layer
        │
Data Layer
```

Each layer has a clearly defined responsibility.

---

# 4. Layer Responsibilities

## 4.1 Presentation Layer

Responsible for user interaction.

Components:

- Website (Current Version)
- Mobile Application (Future)

Responsibilities:

- User Authentication
- Nutrition Profile Forms
- Meal Plan Visualization
- Streaming Progress
- History

---

## 4.2 API Layer

Implemented using FastAPI.

Responsibilities:

- Receive HTTP Requests
- Validate Inputs
- Authentication
- Invoke LangGraph Workflow
- Stream Agent Progress
- Return Final Results

---

## 4.3 Application Layer

Contains business logic.

Responsibilities:

- Service Layer
- Repository Layer
- Configuration
- Dependency Injection
- Error Handling

---

## 4.4 AI Layer

This is the core of the application.

Responsible for:

- User understanding
- Nutrition reasoning
- Meal generation
- Validation
- Explanation

Implemented using:

- LangGraph
- LangChain
- OpenAI / Compatible LLM

---

## 4.5 Knowledge Layer

Contains all external knowledge sources.

```
Knowledge Layer

│

├── Food Database

├── Nutrition Guidelines

└── Meal Templates
```

The AI agents retrieve structured information from these sources before generating responses.

---

## 4.6 Data Layer

Stores all persistent application data.

Includes:

- User Profiles
- Nutrition Plans
- Food Database
- Execution History
- Preferences

Database:

PostgreSQL

---

# 5. Component Architecture

```
                FastAPI

                   │

        ┌──────────┴──────────┐

        ▼                     ▼

 Authentication          Nutrition API

                                │

                                ▼

                     LangGraph Orchestrator

                                │

          ┌─────────────────────┼─────────────────────┐

          ▼                     ▼                     ▼

     AI Agents           Database Layer         Streaming

          │                     │                    │

          ▼                     ▼                    ▼

        LLM                PostgreSQL            SSE / WS
```

---

# 6. Multi-Agent Communication

Agents **do not directly modify each other's internal state**.

Instead:

1. Every agent receives a typed input model.
2. Performs one responsibility.
3. Produces a typed output.
4. The Orchestrator passes the output to the next agent.

```
Profile Agent

↓

NutritionProfile

↓

Calories Agent

↓

CaloriesResult

↓

Macro Agent

↓

MacroResult

↓

Retrieval Agent

↓

RetrievedFoods

↓

Planning Agent

↓

MealPlan

↓

Validation Agent

↓

ValidationResult

↓

Explanation Agent

↓

Final Response
```

This approach ensures loose coupling between agents.

---

# 7. Agent Execution Strategy

The workflow is managed by LangGraph.

```
START

↓

Profile

↓

Calories

↓

Macro

↓

Retrieve Foods

↓

Generate Meals

↓

Validate

↓

Explain

↓

END
```

Conditional execution is supported.

```
Validation

↓

Pass ?

      │

  YES │ NO

      │

      ▼

 Explain

      ▲

      │

Meal Planner
```

The graph can automatically retry failed planning attempts before returning the final response.

---

# 8. Request Lifecycle

A typical nutrition generation request follows this sequence:

```
User

↓

POST /nutrition/generate

↓

FastAPI

↓

Input Validation

↓

LangGraph

↓

Execute Agents

↓

Generate Meal Plan

↓

Validation

↓

Explanation

↓

Streaming Updates

↓

Final Response
```

---

# 9. Data Flow

```
User Input

↓

Profile Agent

↓

Nutrition Profile

↓

Calories Agent

↓

Daily Calories

↓

Macro Agent

↓

Macro Targets

↓

Food Retrieval Agent

↓

Candidate Foods

↓

Planning Agent

↓

Meal Plan

↓

Validation Agent

↓

Validated Meal Plan

↓

Explanation Agent

↓

Client
```

---

# 10. Error Handling

The architecture supports graceful error recovery.

Examples:

- Invalid profile data
- Missing food results
- Invalid macro distribution
- LLM generation failure
- Validation failure

The Orchestrator determines whether to:

- Retry
- Execute another node
- Return an error
- Return a fallback response

---

# 11. Streaming Architecture

Instead of waiting for the entire workflow to finish, every completed agent publishes execution events.

```
Client

↓

SSE Connection

↓

FastAPI

↓

LangGraph

↓

Agent Completed

↓

Publish Event

↓

Frontend Updates UI
```

Example events:

```json
{
  "agent": "Profile Agent",
  "status": "completed"
}
```

```json
{
  "agent": "Macro Agent",
  "status": "running"
}
```

```json
{
  "agent": "Validation Agent",
  "status": "completed"
}
```

---

# 12. Scalability

The architecture is designed for horizontal expansion.

Future agents can be added without changing existing implementations.

Examples:

- Grocery Agent
- Supplement Agent
- Hydration Agent
- Shopping Agent
- Budget Optimization Agent
- Recommendation Agent
- User Memory Agent

Each new agent becomes another LangGraph node.

---

# 13. Design Decisions

| Decision | Reason |
|----------|--------|
| Multi-Agent Architecture | Separation of responsibilities |
| LangGraph | Stateful workflow orchestration |
| LangChain | Prompt management and tool integration |
| PostgreSQL | Reliable structured storage |
| SSE/WebSocket | Real-time execution updates |
| Typed Models | Strong validation between agents |
| Retrieval Before Generation | Reduce hallucinations |
| Validation Before Response | Ensure nutritional correctness |

---

# 14. Non-Functional Characteristics

The architecture emphasizes:

- Scalability
- Maintainability
- Explainability
- Modularity
- Reliability
- Reusability
- Extensibility
- Testability

Each module can be developed, tested, and deployed independently.

---

