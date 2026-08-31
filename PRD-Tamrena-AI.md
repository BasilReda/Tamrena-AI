# Tamrena AI — Product Requirements Document

**Status:** Living document, reflects state as of 2026-08-09
**Owner:** Basil Reda
**Scope:** Full-Project workspace — `tamreena-web`, `Tamrena-Workout`, `Computer-Vision`, `Nutrition-Plan-Generation`

---

## 1. Summary

Tamrena AI is a fitness platform that combines AI-driven workout plan generation, real-time computer-vision form coaching, and personalized nutrition planning behind a unified web frontend. The system is composed of four sibling services, each independently deployable, connected through a backend-for-frontend (BFF) and shared authentication.

## 2. Problem Statement

Users want a single place to get a personalized training program, receive real-time feedback on exercise form during a workout (via webcam/video), track session history, and get a science-backed nutrition plan — without needing a personal trainer or nutritionist. Existing point solutions (fitness apps, form-checking apps, diet apps) are fragmented; Tamrena AI aims to unify plan generation, live coaching, and nutrition into one product.

## 3. Goals

- Provide a single web entry point (`tamreena-web`) for signup/login, workout plans, live coaching sessions, and nutrition plans.
- Generate individualized workout programs from a user intake profile ("Hunter Profile") via `Tamrena-Workout`.
- Analyze live or uploaded workout videos for rep counting, form scoring, and rule-violation feedback via `Computer-Vision`.
- Generate personalized, scientifically validated daily meal plans (with Egyptian cuisine focus) via `Nutrition-Plan-Generation`.
- Keep services independently deployable on AWS (ECS/ECR) while sharing auth (JWT) and user data (DynamoDB).

## 4. Non-Goals

- Native mobile apps (current frontends are web-only; `Tamrena-Workout` frontend is vanilla JS/CSS, no build step).
- Multi-tenant/enterprise features (gyms, trainers managing multiple clients) — not in current scope.
- Payments/subscriptions — not present in current architecture.

## 5. System Architecture

### 5.1 Services

| Service | Path | Role | Stack |
|---|---|---|---|
| **Tamreena Web** | `tamreena-web/` | Primary frontend + BFF; auth (signup/login), home/workout/progress screens | Frontend + FastAPI-style BFF backend, MongoDB (own DB), Vite dev frontend |
| **Tamrena Workout** | `Tamrena-Workout/` | Workout plan generation engine ("Hunter Profile" intake → Training Protocol) | Python backend (agents/api/auth), DynamoDB for user storage, vanilla JS/CSS frontend, deployed to AWS ECS |
| **Computer Vision (AI-GYM)** | `Computer-Vision/` | Real-time pose-estimation coaching: webcam/video → skeleton overlay, rep counting, form scoring, per-rule feedback over WebSocket; session reports as JSON | Python analytics engine (source of truth) + FastAPI/WebSocket server + dark-first React UI |
| **Nutrition Plan Generation** | `Nutrition-Plan-Generation/` | Personalized daily meal plans via 7-node multi-agent pipeline (BMR/TDEE/macro calculators, food retrieval, meal composition, validation, explanation) | FastAPI, LangGraph, Groq, LangSmith, React/Vite frontend, SSE streaming |

### 5.2 Integration model

- **BFF pattern**: frontends do not talk to databases directly; `tamreena-web`'s backend brokers requests to sibling services.
- **Shared auth**: JWT tokens issued by `tamreena-web` must be verifiable by `Tamrena-Workout` — both share the same `JWT_SECRET`. See `Tamreena_AI/docs/superpowers/specs/2026-07-25-bff-auth-handoff-design.md`.
- **Data storage**: `Tamrena-Workout` persists users in **DynamoDB** (migrated from Mongo — idempotent table creation via `scripts/create_dynamo_tables.py`); `tamreena-web` uses its own **MongoDB** instance, separate from `Tamrena-Workout`'s data.
- **Deployment**: Backend and frontend services are containerized (Docker) and deployed to **AWS ECS** with images pushed to **ECR**; nginx reverse-proxies `/auth`, `/api`, `/ws` from the frontend container to backend services using runtime env-var substitution (`VITE_API_BASE_URL` / relative-path default) rather than build-time baking, so the same image can point at different backend hosts per environment.

### 5.3 Local ports (dev)

- `tamreena-web` backend: `localhost:8010`
- `tamreena-web` frontend: `localhost:5174`
- `tamreena-web` MongoDB: `localhost:27018`

## 6. Core User Flows

1. **Sign up / Log in** (`tamreena-web`) — username/password auth, JWT issued and shared across services.
2. **Generate a workout plan** (`Tamrena-Workout`) — user completes an intake form (Hunter Profile: goals, constraints, equipment, etc.) with optional camera capture / PDF upload for validation → system produces a structured Training Protocol (plan by day).
3. **Live/video coaching session** (`Computer-Vision`) — user starts a webcam session or uploads a video; engine streams skeleton overlay, rep counts, stage detection, joint angles, live form score, and rule-based feedback over WebSocket; on completion, a normalized JSON session report is generated and viewable via score rings, charts, and expandable rep breakdowns; history page shows trends and most-common-mistakes.
4. **Get a nutrition plan** (`Nutrition-Plan-Generation`) — user submits profile data; a 7-node LangGraph pipeline (Profile → Calorie/Macro calculators → Food Retrieval → Meal Composition → Validation loop → Explanation) streams progress via SSE and returns a validated, explainable daily meal plan.

## 7. Key Technical Decisions / Constraints (as of Aug 2026)

- DynamoDB migration for `Tamrena-Workout` user storage is complete, with dual Mongo/DynamoDB test fixtures retained during transition.
- Frontend backend URL is configurable via `VITE_API_BASE_URL`, defaulting to relative paths so nginx reverse-proxy can route without hardcoding hosts — resolves earlier hardcoded `localhost:8010` references that broke production deploys.
- `tamreena-web`'s shipped dev docker-compose is explicitly **dev-only** (wide-open CORS, Vite dev server) — not safe to deploy as-is; a separate production Dockerfile + nginx config exists for real deployment.
- Auth routes and the WebSocket endpoint intentionally sit at root-level paths (not under `/api/`), while other backend routers use a consistent `/api/` prefix.
- AWS credentials must not be stored in plaintext `.env` files long-term or echoed into command output/logs (flagged security concern).

## 8. Known Issues / Open Work (tracked as of Aug 7-9, 2026)

- **Video session analysis bug**: after fixing a 403 regression that blocked `source=video` sessions from completing, a separate pre-existing bug was exposed — the CV service's rule-violation classifier marks all reps as correct even when invalid reps are present. Root cause not yet found; next step is pulling the session's rule-violation report via `GET /api/sessions/{session_id}` and inspecting classifier output.
- Frontend/backend ECS task definitions require manual updates when backend IPs change (no service discovery in place yet) — this has caused repeated redeploys (revisions 7, 8, etc.) to point the frontend at a new backend IP.
- Multi-frontend tech stacks are inconsistent in maturity (vanilla JS for Workout, React for CV and Nutrition, Vite-based BFF frontend for tamreena-web) — no shared design system yet.

## 9. Success Metrics (proposed — not yet instrumented)

- End-to-end completion rate of video coaching sessions (upload/live → viewable report) without errors.
- Accuracy of rep/rule-violation classification vs. manual review (once the current classifier bug is fixed).
- Time from signup to first generated workout plan and first generated nutrition plan.
- Deployment stability: ECS service health-check pass rate post-deploy.

## 10. Open Questions

- Should the four services converge on a single frontend shell/design system, or remain independently developed with `tamreena-web` as the aggregation layer?
- What is the long-term plan for service discovery between ECS services (currently manual IP updates to task definitions)?
- Is a production-hardened `docker-compose` (real CORS, HTTPS) planned for `tamreena-web`, or is ECS the only production target?
- Payment/subscription model, if any, for future monetization — currently out of scope.

---

*This PRD was generated from the current repository structure, service READMEs, and recent project history. It should be revisited as the video-analysis classifier bug is resolved and as services converge further.*
