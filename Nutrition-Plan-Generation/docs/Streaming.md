# Streaming Architecture

> **Document Version:** 1.0.0
> **Status:** MVP Design
> **Technology:** Server-Sent Events (SSE)

---

# 1. Overview

Generating a personalized nutrition plan involves multiple sequential components that may take several seconds to complete.

Instead of forcing users to wait for a single HTTP response, the system streams execution progress in real time.

This approach improves user experience by displaying the current execution stage, progress updates, and the final meal plan as soon as it becomes available.

---

# 2. Why Streaming?

Traditional REST APIs require the client to wait until the entire workflow finishes.

```
Client

↓

POST /generate

↓

Wait...

↓

Wait...

↓

Wait...

↓

Receive Result
```

With streaming:

```
Client

↓

POST /generate

↓

Receive Run ID

↓

Open Stream

↓

Profile Agent Running...

↓

Calories Calculated...

↓

Foods Retrieved...

↓

Meal Generated...

↓

Validation Passed...

↓

Final Response
```

Users always know what the system is doing.

---

# 3. Streaming Architecture

```
                Frontend
                    │
                    │ HTTP
                    ▼
          POST /nutrition/generate
                    │
                    ▼
              FastAPI Backend
                    │
                    ▼
           LangGraph Orchestrator
                    │
                    ▼
         Publish Streaming Events
                    │
                    ▼
          Server-Sent Events (SSE)
                    │
                    ▼
               Frontend UI
```

---

# 4. Workflow

```
Generate Request

↓

Create Run ID

↓

Start LangGraph

↓

Execute Nodes

↓

Publish Events

↓

Return Final Plan

↓

Close Stream
```

---

# 5. Streaming Lifecycle

Each workflow execution creates a unique Run ID.

Example:

```
Run ID

↓

abc123xyz
```

The frontend subscribes using:

```
GET /api/v1/nutrition/stream/{run_id}
```

---

# 6. Event Types

The system publishes different event types during execution.

| Event | Description |
|--------|-------------|
| workflow_started | Workflow has started |
| node_started | Node execution started |
| node_completed | Node completed successfully |
| node_failed | Node failed |
| retry_started | Retry initiated |
| retry_completed | Retry completed |
| workflow_completed | Entire workflow completed |
| workflow_failed | Workflow terminated |

---

# 7. Event Flow

```
workflow_started

↓

Profile Agent Started

↓

Profile Agent Completed

↓

Calories Calculator Started

↓

Calories Calculator Completed

↓

Macro Calculator Started

↓

Macro Calculator Completed

↓

Food Retrieval Started

↓

Food Retrieval Completed

↓

Meal Composition Started

↓

Meal Composition Completed

↓

Validation Started

↓

Validation Completed

↓

Explanation Started

↓

Explanation Completed

↓

workflow_completed
```

---

# 8. Event Structure

Every event follows the same schema.

```json
{
    "run_id": "abc123",
    "event": "node_completed",
    "node": "Macro Calculator",
    "status": "completed",
    "timestamp": "2026-07-17T14:30:15Z"
}
```

---

# 9. Progress Updates

The backend may optionally include progress percentages.

Example:

```json
{
    "progress": 57
}
```

Suggested mapping:

| Node | Progress |
|------|----------|
| Profile Agent | 10% |
| Calories Calculator | 20% |
| Macro Calculator | 35% |
| Food Retrieval | 50% |
| Meal Composition | 75% |
| Validation | 90% |
| Explanation | 100% |

---

# 10. Retry Events

If validation fails, retry events are emitted.

Example:

```json
{
    "event": "retry_started",
    "node": "Meal Composition Agent",
    "attempt": 2,
    "reason": "Protein target not satisfied"
}
```

After retry:

```json
{
    "event": "retry_completed",
    "attempt": 2
}
```

---

# 11. Final Result Event

When the workflow finishes successfully:

```json
{
    "event": "workflow_completed",
    "run_id": "abc123",
    "status": "success",
    "plan_id": "plan_987"
}
```

The frontend can then retrieve the plan or receive it directly in the stream.

---

# 12. Error Events

Unexpected failures are streamed immediately.

Example:

```json
{
    "event": "workflow_failed",
    "error": "Food dataset unavailable"
}
```

Possible failures include:

- Dataset loading failure
- Invalid profile
- LLM timeout
- Validation failure
- Internal server error

---

# 13. Frontend Responsibilities

The frontend should:

- Open the SSE connection.
- Display the active execution stage.
- Update progress indicators.
- Show retry notifications.
- Handle connection failures.
- Display the final nutrition plan.

---

# 14. Backend Responsibilities

The backend should:

- Generate unique Run IDs.
- Maintain active workflow state.
- Publish events immediately.
- Close completed streams.
- Handle disconnected clients.
- Clean expired runs.

---

# 15. Stream Completion

A stream is closed when:

- Workflow completes successfully.
- Workflow fails.
- Maximum retries are exceeded.
- Client disconnects.
- Request timeout occurs.

---

# 16. Future Improvements

Future versions may replace or complement SSE with:

- WebSockets
- Redis Pub/Sub
- Kafka
- RabbitMQ
- Multi-worker event broadcasting

The event format will remain unchanged, ensuring frontend compatibility.

---

# 17. Design Decisions

| Decision | Reason |
|----------|--------|
| Server-Sent Events | Lightweight one-way communication |
| Unique Run ID | Track workflow execution |
| Event-based updates | Better user experience |
| Standard event schema | Simplified frontend integration |
| Retry events | Improve transparency |
| Progress tracking | Real-time execution monitoring |

---

# 18. Summary

The Streaming layer provides real-time visibility into the execution of the Multi-Agent Nutrition System.

By publishing standardized events throughout the workflow, users receive continuous feedback while the backend executes profile analysis, nutritional calculations, food retrieval, meal composition, validation, and explanation.

This architecture improves responsiveness, simplifies debugging, and creates a modern interactive user experience.

---

# Next Document

➡ **10_Project_Structure.md**