# API Design

> **Document Version:** 1.0.0
> **Status:** MVP Design

---

# 1. Overview

The Nutrition AI System exposes a RESTful API built with **FastAPI**.

The API is designed around an asynchronous workflow where long-running AI tasks execute in the background while streaming real-time progress updates to the client.

The frontend never waits silently for the final response. Instead, it receives continuous execution events until the nutrition plan is completed.

---

# 2. API Architecture

```

Client (React)

│

├────────────── HTTP ───────────────┐

│                                   │

▼                                   ▼

REST API                      Streaming API

│                                   │

└────────────── FastAPI ─────────────┘

│

▼

LangGraph Orchestrator

```

---

# 3. Authentication APIs

## Register

```

POST /api/v1/auth/register

```

Purpose

Create a new account.

---

## Login

```

POST /api/v1/auth/login

```

Returns

```

JWT Access Token

Refresh Token

```

---

## Refresh Token

```

POST /api/v1/auth/refresh

```

---

## Logout

```

POST /api/v1/auth/logout

```

---

# 4. User APIs

## Get Profile

```

GET /api/v1/profile

```

---

## Update Profile

```

PUT /api/v1/profile

```

---

## Delete Profile

```

DELETE /api/v1/profile

```

---

# 5. Nutrition APIs

## Generate Nutrition Plan

```

POST /api/v1/nutrition/generate

```

Purpose

Start the nutrition planning workflow.

---

Request

```json
{
    "age":24,
    "gender":"male",
    "height":180,
    "weight":82,
    "goal":"Fat Loss",
    "activity_level":"Moderate",
    "preferences":[
        "Chicken",
        "Rice"
    ],
    "allergies":[
        "Peanuts"
    ]
}
```

---

Response

```json
{
    "run_id":"ab12345",
    "status":"started"
}
```

The client should immediately connect to the streaming endpoint.

---

# 6. Streaming API

```

GET /api/v1/nutrition/stream/{run_id}

```

Protocol

Server Sent Events (SSE)

---

Example Events

```
event: started

data:
{
    "agent":"Profile Agent"
}
```

---

```
event: running

data:
{
    "agent":"Calories Calculator"
}
```

---

```
event: completed

data:
{
    "agent":"Macro Calculator"
}
```

---

```
event: failed

data:
{
    "agent":"Validation Engine",
    "reason":"Protein below target"
}
```

---

```
event: finished

data:
{
    "status":"completed"
}
```

---

# 7. Final Result API

Although the final meal plan is sent through streaming, it can also be retrieved later.

```

GET /api/v1/nutrition/result/{run_id}

```

---

# 8. Nutrition History

Retrieve all previously generated nutrition plans.

```

GET /api/v1/nutrition/history

```

---

# 9. Get Specific Plan

```

GET /api/v1/nutrition/{plan_id}

```

---

# 10. Delete Plan

```

DELETE /api/v1/nutrition/{plan_id}

```

---

# 11. Health Check

```

GET /health

```

Response

```json
{
    "status":"healthy"
}
```

---

# 12. API Flow

```

POST Generate

↓

Run ID

↓

Open Stream

↓

Receive Agent Events

↓

Workflow Completed

↓

Meal Plan

↓

Save History

```

---

# 13. Standard Response Format

Successful response

```json
{
    "success":true,
    "data":{},
    "message":"Success"
}
```

---

Error response

```json
{
    "success":false,
    "error":"Validation failed"
}
```

---

# 14. HTTP Status Codes

| Code | Meaning |
|------|---------|
|200|Success|
|201|Created|
|202|Accepted|
|400|Bad Request|
|401|Unauthorized|
|403|Forbidden|
|404|Not Found|
|422|Validation Error|
|500|Internal Server Error|

---

# 15. Security

Authentication is handled using JWT.

Protected endpoints require:

```
Authorization: Bearer <token>
```

Passwords are hashed before storage.

Rate limiting may be added in future versions.

---

# 16. Versioning

The API follows URL versioning.

Example

```
/api/v1/...
```

Future versions

```
/api/v2/...
```

---

# 17. Future APIs

Future releases may introduce:

- Workout Recommendation API
- Grocery Recommendation API
- Food Search API
- Barcode Scanner API
- Image Recognition API
- Wearable Device Integration

---

# 18. Summary

The API is designed around asynchronous execution and real-time streaming.

This architecture allows the frontend to monitor every stage of the nutrition generation workflow while maintaining a clean separation between business logic and client communication.

---

# Next Document

➡ **09_Streaming.md**