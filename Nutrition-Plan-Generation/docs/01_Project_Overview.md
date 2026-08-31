# Nutrition AI Multi-Agent System

> **Version:** 1.0.0  
> **Status:** Design Phase  
> **Authors:** Graduation Project Team  
> **Last Updated:** July 2026

---

# 1. Project Overview

## 1.1 Introduction

The Nutrition AI Multi-Agent System is an intelligent nutrition planning platform designed to generate highly personalized meal plans based on each user's health profile, fitness goals, dietary preferences, and workout routine.

Unlike traditional nutrition applications that rely on static rules or a single Large Language Model (LLM), this project adopts a **Multi-Agent Architecture**, where each AI agent is responsible for a specialized task within the nutrition planning pipeline.

The system combines deterministic nutritional calculations, structured food databases, Retrieval-Augmented Generation (RAG), and Large Language Models to produce meal plans that are scientifically accurate, explainable, and tailored to the user's needs.

---

# 2. Problem Statement

Many existing nutrition applications suffer from one or more of the following limitations:

- Generic meal plans that ignore personal characteristics.
- Lack of scientific nutritional calculations.
- Heavy dependence on LLM-generated responses without validation.
- Poor support for local cuisines such as Egyptian food.
- No explanation of why a particular meal plan was generated.
- Difficulty adapting meal plans according to user preferences, allergies, or medical conditions.

These limitations often lead to unrealistic, nutritionally inconsistent, or impractical meal recommendations.

---

# 3. Proposed Solution

This project proposes a **Multi-Agent AI Nutrition Planning System** that decomposes the nutrition planning process into multiple specialized agents.

Instead of allowing a single AI model to generate an entire meal plan, each agent performs a dedicated responsibility, including:

- Building the user's nutrition profile.
- Calculating caloric requirements.
- Computing macronutrient distribution.
- Retrieving appropriate food items from nutritional databases.
- Generating nutritionally balanced Egyptian-style meals.
- Validating nutritional consistency.
- Explaining the reasoning behind the generated plan.

This modular architecture improves:

- Accuracy
- Explainability
- Scalability
- Maintainability
- Reliability

---

# 4. Project Objectives

The primary objectives of the project are:

- Generate personalized nutrition plans.
- Support multiple fitness goals.
- Consider dietary preferences and restrictions.
- Support Egyptian food recommendations.
- Produce explainable AI-generated meal plans.
- Ensure nutritional correctness through validation.
- Build a modular Multi-Agent architecture.
- Provide real-time execution status through streaming APIs.
- Support future integration with the Workout AI System.

---

# 5. Scope

## In Scope

The system will support:

- User nutrition profile analysis
- Daily calorie calculation
- Macronutrient calculation
- Personalized meal planning
- Egyptian food recommendations
- Food retrieval from structured databases
- Nutrition validation
- AI explanation generation
- Streaming execution status
- REST APIs
- Future mobile integration

---

## Out of Scope

The following features are excluded from the first release:

- Grocery ordering
- Meal delivery
- Barcode scanning
- Image-based food recognition
- Blood test analysis
- Medical diagnosis
- Wearable device synchronization

These features may be considered in future versions.

---

# 6. Key Features

The platform provides the following capabilities:

- AI-powered nutrition planning
- Personalized meal generation
- Multi-Agent workflow
- Scientific calorie calculations
- Macro distribution
- Egyptian food support
- Food database retrieval
- Explainable AI
- Validation pipeline
- Streaming execution events
- Modular architecture

---

# 7. Why Multi-Agent?

Instead of asking one LLM to generate an entire meal plan, the system distributes responsibilities among specialized AI agents.

Benefits include:

- Independent decision-making
- Better debugging
- Easier testing
- Higher accuracy
- Modular development
- Easier maintenance
- Better scalability
- Explainable execution pipeline

Each agent becomes responsible for solving one well-defined problem rather than attempting to solve everything at once.

---

# 8. High-Level Workflow

```
User
   │
   ▼
Nutrition API
   │
   ▼
Orchestrator Agent
   │
   ├──────────────► Profile Agent
   │
   ├──────────────► Calories Agent
   │
   ├──────────────► Macro Agent
   │
   ├──────────────► Food Retrieval Agent
   │
   ├──────────────► Nutrition Planning Agent
   │
   ├──────────────► Validation Agent
   │
   └──────────────► Explanation Agent
                     │
                     ▼
             Personalized Nutrition Plan
```

---

# 9. Core Technologies

The project is built using modern AI and backend technologies.

| Layer | Technology |
|---------|------------|
| Backend | FastAPI |
| AI Framework | LangGraph |
| LLM Framework | LangChain |
| Language | Python |
| Database | PostgreSQL |
| Vector Database | pgvector |
| ORM | SQLAlchemy |
| Streaming | Server-Sent Events (SSE) / WebSocket |
| Validation | Pydantic |
| Deployment | Docker |
| Monitoring | LangSmith (Optional) |

---

# 10. High-Level System Components

The platform consists of several independent layers.

```
Client (Web)

        │

FastAPI Backend

        │

Orchestrator

        │

Multi-Agent System

        │

Knowledge Layer

        │

PostgreSQL + Food Database

        │

LLM
```

Each layer has a clear responsibility and communicates through well-defined interfaces.

---

# 11. Knowledge Sources

The nutrition planning system relies on three primary knowledge sources.

## Food Database

Contains structured nutritional information for food items, including:

- Calories
- Protein
- Carbohydrates
- Fat
- Food Groups
- Meal Categories

---

## Nutrition Guidelines

Scientific nutritional references such as:

- WHO
- Dietary Guidelines
- Sports Nutrition Recommendations

---

## Meal Templates

Example meal structures used to guide meal generation while allowing the LLM to create personalized combinations.

---

# 12. Design Principles

The architecture follows the following principles:

- Separation of Responsibilities
- Single Responsibility Principle
- Explainable AI
- Retrieval before Generation
- Validation before Response
- Stateless APIs
- Modular Agents
- Strong Typing
- Streaming-first Design
- Production-ready Architecture

---

# 13. Future Vision

Although the first version targets a web application, the architecture has been intentionally designed to support future expansion.

Future versions may include:

- Mobile applications (Android & iOS)
- Grocery recommendation agents
- Shopping list generation
- Meal rating feedback loops
- Personalized long-term nutrition memory
- Integration with wearable devices
- Adaptive nutrition planning using user history
- Continuous learning from user behavior

---

