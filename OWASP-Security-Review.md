# OWASP Security Review — Tamrena AI

**Date:** 2026-08-09
**Scope:** The three AI-driven services — Computer-Vision (pose analysis), Nutrition-Plan-Generation (LangGraph meal planning), and the coach chat agent in Tamrena-Workout — plus the tamreena-web backend (BFF) that fronts all of them for the browser.
**Method:** Installed the `owasp-security` skill (OWASP Top 10:2025, ASVS 5.0, LLM Top 10 2025, Agentic AI Top 10 2026) and ran three parallel code reviews, one per AI service, then fixed the highest-severity findings.

This document explains what was found, what was fixed, and what's still open — written so you can follow the reasoning without re-reading the code yourself.

---

## The big picture: how these services trust each other

```
Browser → tamreena-web (BFF) → Tamrena-Workout (coach agent)
                              → Nutrition-Plan-Generation (meal planner)
                              → Computer-Vision (pose analysis)
```

The BFF ("Backend For Frontend") is the **only** service that authenticates real users — it issues and checks JWTs. The three services behind it were built assuming *"nothing but the BFF will ever talk to me"* — none of them checked who was calling. That assumption is the root cause behind almost every finding below: it's fine as long as it's actually true, and a real vulnerability the moment it isn't (a misconfigured firewall, a port accidentally exposed, a network change six months from now).

---

## Findings, ranked by severity

### 1. Cross-tenant IDOR in Computer-Vision — HIGH (fixed)
Any logged-in user could view **another user's** workout video and rep-count report. Session IDs are predictable filenames (`Exercise_Name_YYYYMMDD_HHMMSS`), and neither Computer-Vision nor the BFF's proxy checked that the session belonged to the person asking for it.

### 2. Missing auth on Nutrition-Plan-Generation — HIGH (fixed)
`GET /history` returned **every user's** nutrition and health data to any caller, and individual plans were readable by `run_id` with no ownership check.

### 3. No authentication on either service's own API — HIGH (fixed)
Both Computer-Vision and Nutrition-Plan-Generation trusted "if a request reaches me, it must be from the BFF" — a network-placement assumption, not an enforced rule. If either service's port were ever reachable directly (a firewall misconfiguration, a debug port left open, a future infra change), all of their data — and Computer-Vision's ability to rewrite server config — would be openly accessible.

### 4. Unauthenticated settings mutation in Computer-Vision — MEDIUM (not yet fixed)
`PUT /api/settings` let anyone rewrite server-wide config, including the file path the engine reads video from — a local-file-read primitive. *(Now behind the new internal-auth gate as a side effect of fix #3, but not independently hardened — see "Still open" below.)*

### 5. Prompt injection — MEDIUM (not yet fixed)
Both the coach chat agent and the nutrition planner mix user-supplied free text directly into LLM prompts with no clear "this is untrusted data" boundary. The nutrition planner's default mode has no independent code-level allergen check, so a crafted note could in theory talk the model out of respecting a listed allergy.

### 6. No rate limiting on LLM-calling endpoints — MEDIUM (not yet fixed)
Neither the coach chat nor the nutrition generation endpoint caps request size or frequency — a cost-amplification risk, worse before fix #2 closed off unauthenticated access.

### 7. Lower-severity items (not yet fixed)
- Computer-Vision accepts uploaded video content based on file extension only, not actual content — a theoretical codec-parser attack surface.
- Live video-tracking has no per-session length/resolution cap, and only one session can run at a time globally — one user can inadvertently or deliberately block everyone else.
- Nutrition-Plan-Generation's CORS combined a wildcard origin with credentials, a combination browsers reject — tightened as a quick adjacent fix while touching that code.

### What turned out fine
JWT handling across all services is correct (pinned algorithm, verified signature and expiry). No hardcoded secrets anywhere. All database access is parameterized — no SQL/NoSQL injection. No `eval`, `exec`, `pickle`, or `shell=True` found in any service. The coach agent has no tool-calling ability, so prompt injection there can't escalate beyond changing its own reply text. React auto-escapes all LLM-generated text on the frontend, so no XSS from generated content.

---

## What was actually fixed

### Fix 1 — Cross-tenant IDOR (tamreena-web)
Computer-Vision has no concept of "users," so ownership had to be tracked on the BFF side, which does. A new table (`live_session_ownership`) records who uploaded a video or completed a session; the report endpoint and the live-tracking websocket now reject any ID the caller doesn't own.

*Bug caught along the way:* the first version of this fix listened for a websocket event type of `"complete"` to know when to record ownership — but Computer-Vision actually sends `"end"`. Ownership was silently never being recorded, which would have made the fix a no-op (every report request would 404). Caught by writing a test that actually exercised the record-then-read path, not just the message-relaying behavior. Fixed, with that test now in place permanently.

### Fix 2 — IDOR in Nutrition-Plan-Generation (tamreena-web)
The BFF already tracked each user's most recent `run_id`. `GET /result/{run_id}` and the SSE progress stream now check that the requested `run_id` matches the caller's own before proxying the request through, instead of trusting any ID handed to them.

### Fix 3 — Internal service authentication (all three repos)
Added a shared-secret header (`X-Internal-Auth`) that the BFF now sends on every call to Computer-Vision and Nutrition-Plan-Generation, and that both services now require on every route — including the live-tracking websocket handshake. **If the secret isn't configured, every request is rejected** (fail closed) rather than silently allowing everything through, so a forgotten environment variable surfaces immediately as errors instead of as a silent security gap.

### Fix 4 — `/history` route-shadowing bug (Nutrition-Plan-Generation)
Discovered as a side effect of testing fix #2: `GET /history` was being silently swallowed by a more generic route (`GET /{run_id}`) registered before it, due to how the framework matches routes in the order they're defined. `/history` always 404'd instead of ever running — meaning the original "leaks everyone's data" finding was, in practice, unreachable until this was fixed. Fixed the ordering and added tests for both the fixed route and the alias it shares code with.

---

## What's still open

In roughly the order I'd tackle them next:

1. **Rate limiting** on `/coach/chat` and `/generate` — currently uncapped request size and frequency.
2. **Prompt injection hardening** — wrap user-supplied text in explicit "untrusted data" delimiters in both the coach and nutrition prompts; add a code-level allergen re-check after generation in the nutrition planner's default mode (mirroring the guard that already exists for its other modes).
3. **Computer-Vision `/api/settings`** — now requires internal auth, but the endpoint itself still has no allowlist on what paths it'll accept; worth adding one so a compromised internal caller can't still point it at arbitrary files.
4. **Video content validation** in Computer-Vision — check actual file content, not just the extension, before handing uploads to the decoder.
5. **Per-session resource limits** in Computer-Vision's live tracking — cap video length/resolution, and make the "one session at a time" gate per-user instead of global.

---

## Deploying these fixes

Two things need to happen for the auth fixes to actually take effect in production, not just pass tests:

1. **Run the new table-creation script** for the Computer-Vision ownership table:
   ```
   cd tamreena-web/backend && python scripts/create_live_session_ownership_table.py
   ```
2. **Set `INTERNAL_SERVICE_TOKEN`** (tamreena-web and Computer-Vision) / **`internal_service_token`** (Nutrition-Plan-Generation, note the lowercase — pydantic-settings convention in that repo) to the **same value** in all three services' environments. Until this is set, Computer-Vision and Nutrition-Plan-Generation will reject every request — including from the BFF itself — by design (fail closed), so this has to land before or alongside the deploy, not after.

---

## Where the code lives

| Repo | Branch/PR | Status |
|---|---|---|
| tamreena-web | `main` | Pushed directly |
| Computer-Vision | PR [#1](https://github.com/TamrenaAI/Computer-Vision/pull/1) | Via fork (no direct write access) |
| Nutrition-Plan-Generation | PR [#6](https://github.com/TamrenaAI/Nutrition-Plan-Generation/pull/6) | Via fork (no direct write access) |
