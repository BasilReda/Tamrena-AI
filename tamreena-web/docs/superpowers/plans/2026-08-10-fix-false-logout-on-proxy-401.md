# Fix: Nutrition / Computer-Vision actions log the user out

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Bug report:** Locally, generating a nutrition plan (after selecting options) and using the Computer-Vision / live-session feature both log the user out of their account.

**Root cause (confirmed by code investigation, see Investigation Notes below):** `tamreena-web`'s frontend `authFetch` helper (`frontend/src/lib/api.ts:49-60`) treats **any** `401` response from the BFF as the user's own session being invalid — it clears the stored token and hard-redirects to `/signin`. But `tamreena-web`'s backend proxies to Computer-Vision and Nutrition-Plan-Generation forward the upstream's HTTP status code verbatim (`app/tamreena_client.py`'s `proxy_json`). Both upstreams now enforce a shared-secret `X-Internal-Auth` header (added in the 2026-08-09 OWASP hardening plan) and fail closed with a `401` if that secret is missing/mismatched. That upstream-auth `401` is indistinguishable, on the wire, from the user's own JWT expiring — so any internal-auth misconfiguration between services (e.g. `INTERNAL_SERVICE_TOKEN` not yet loaded because a service wasn't restarted after `.env` changed) silently logs every user out the moment they touch Nutrition or Computer-Vision.

**Immediate local diagnostic:** if you're hitting this locally right now, restart the Computer-Vision and Nutrition-Plan-Generation containers (`docker compose restart` in each repo) — both load `INTERNAL_SERVICE_TOKEN` once at process start via `pydantic-settings`, so if the token was added to their `.env` after the containers were already running, they're still fail-closing on every request. This plan fixes the underlying design flaw regardless.

**Architecture:** Two tasks, both in `tamreena-web`. Task 1 (backend) stops a proxied upstream auth failure from ever reaching the client as a bare `401` — it's the primary fix and closes the bug on its own. Task 2 (frontend) is defense-in-depth: it makes `authFetch` only treat a `401` as a genuine session-expiry when the backend explicitly says so, instead of trusting the raw status code, so no future proxy route can trigger the same false logout by accident.

**Tech Stack:** FastAPI backend (`tamreena-web/backend`), React/TypeScript frontend (`tamreena-web/frontend`). No new dependencies.

---

### Task 1: Backend — never forward a raw upstream auth-failure as a bare 401

Computer-Vision and Nutrition-Plan-Generation have no user-level auth of their own (see `app/tamreena_client.py`'s module docstring) — every `401` they can possibly return is *always* an internal-service-auth failure (`X-Internal-Auth` missing/mismatched), never a signal about the end user's session. The BFF should translate that into a `502`/`503` so it can't be confused with the BFF's own JWT check failing.

**Files:**
- Modify: `tamreena-web/backend/app/tamreena_client.py` (`proxy_json`)
- Modify: `tamreena-web/backend/app/nutrition/routes.py` (`stream_nutrition_progress` — has its own manual status-passthrough, same bug pattern, for consistency)
- Test: `tamreena-web/backend/tests/test_tamreena_client.py` (new, or extend the closest existing proxy test file if one already covers `proxy_json`/`call_upstream`)

**Interfaces:**
- Changes `proxy_json(response: Optional[httpx.Response]) -> JSONResponse` to `proxy_json(response: Optional[httpx.Response], *, internal_auth: bool = False) -> JSONResponse`. Every call site in `app/nutrition/routes.py` and `app/live_session/routes.py` that proxies to `NUTRITION_API_URL` or `CV_API_URL` passes `internal_auth=True`; the Workout proxy call sites (`WORKOUT_API_URL`, which authenticates via the user's own forwarded token, not the internal secret) are unaffected and keep the default.

- [ ] **Step 1: Write the failing test**

```python
# tamreena-web/backend/tests/test_tamreena_client.py
import httpx
import pytest

from app.tamreena_client import proxy_json


def _resp(status_code: int, json_body: dict) -> httpx.Response:
    return httpx.Response(status_code, json=json_body, request=httpx.Request("GET", "http://upstream/x"))


def test_internal_auth_401_is_translated_to_503():
    resp = proxy_json(_resp(401, {"detail": "Invalid or missing internal service credentials"}), internal_auth=True)
    assert resp.status_code == 503


def test_non_internal_auth_401_passes_through_unchanged():
    # Workout proxy calls forward the user's own token; a 401 there is real
    # and must reach the client as-is.
    resp = proxy_json(_resp(401, {"detail": "token expired"}), internal_auth=False)
    assert resp.status_code == 401


def test_non_401_status_codes_pass_through_unchanged_regardless_of_internal_auth():
    resp = proxy_json(_resp(404, {"detail": "not found"}), internal_auth=True)
    assert resp.status_code == 404
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `tamreena-web/backend/`): `python -m pytest tests/test_tamreena_client.py -v`
Expected: FAIL — `proxy_json()` doesn't accept `internal_auth` yet, and even once it does, the 401→503 translation doesn't exist.

- [ ] **Step 3: Implement the translation in `proxy_json`**

In `tamreena-web/backend/app/tamreena_client.py`, replace `proxy_json` with:

```python
def proxy_json(response: Optional[httpx.Response], *, internal_auth: bool = False) -> JSONResponse:
    if response is None:
        return JSONResponse(status_code=502, content={"detail": "Upstream service unavailable"})
    if internal_auth and response.status_code == 401:
        # This upstream has no user-level auth of its own (see module
        # docstring) — a 401 here can only mean our own X-Internal-Auth
        # secret is missing/wrong, never that the caller's session is
        # invalid. Forwarding it as a bare 401 gets misread by the
        # frontend's global authFetch as "log this user out."
        return JSONResponse(
            status_code=503,
            content={"detail": "Upstream service is misconfigured (internal auth rejected). Not a session issue."},
        )
    try:
        content = response.json()
    except ValueError:
        content = {"detail": response.text}
    return JSONResponse(status_code=response.status_code, content=content)
```

- [ ] **Step 4: Pass `internal_auth=True` at every CV/Nutrition call site**

In `tamreena-web/backend/app/nutrition/routes.py`: update the three `proxy_json(resp)` calls in `generate_nutrition_plan` and `get_nutrition_result` to `proxy_json(resp, internal_auth=True)`.

In `tamreena-web/backend/app/live_session/routes.py`: update the two `proxy_json(resp)` calls in `upload_live_session_video` and `get_live_session_report` to `proxy_json(resp, internal_auth=True)`.

Leave every `WORKOUT_API_URL` call site (in `app/workout/routes.py` and `app/coach/routes.py`) unchanged — those forward the user's real Bearer token and a `401` there is genuine.

- [ ] **Step 5: Apply the same fix to the SSE stream's manual status passthrough**

In `stream_nutrition_progress` (`app/nutrition/routes.py`, the `if upstream.status_code != 200:` block), apply the same translation before building the `JSONResponse`:

```python
    if upstream.status_code != 200:
        error_body = await upstream.aread()
        await stack.aclose()
        status_code = 503 if upstream.status_code == 401 else upstream.status_code
        if upstream.status_code == 401:
            content = {"detail": "Upstream service is misconfigured (internal auth rejected). Not a session issue."}
        else:
            try:
                content = json.loads(error_body)
            except ValueError:
                content = {"detail": error_body.decode(errors="replace")}
        return JSONResponse(status_code=status_code, content=content)
```

(Lower priority than Steps 3-4 — this path isn't wired through `authFetch` on the frontend today, per the investigation, so it can't cause the logout bug directly. Fixing it anyway keeps the two proxy paths consistent and avoids the same trap biting a future caller.)

- [ ] **Step 6: Run the full backend suite**

Run (from `tamreena-web/backend/`): `python -m pytest tests/ -q`
Expected: all tests pass, including the new ones from Step 1.

---

### Task 2: Frontend — only log out on an explicit session-expiry signal (defense-in-depth)

Even with Task 1 fixed, `authFetch`'s blanket "any 401 ⇒ logout" is fragile — any future proxy route that forwards an upstream status code without the same care reintroduces this exact bug. Make the frontend require an explicit signal instead of inferring one from the bare status code.

**Files:**
- Modify: `tamreena-web/backend/app/auth/dependencies.py` (`get_current_user`, `get_verified_token`, `get_verified_token_for_stream`)
- Modify: `tamreena-web/frontend/src/lib/api.ts` (`authFetch`)
- Test: extend `tamreena-web/backend/tests/test_auth_dependencies.py` (or closest equivalent) for the new error shape; add/extend a frontend test for `authFetch` if this repo has frontend unit tests set up (check for an existing `*.test.ts`/`*.test.tsx` alongside `api.ts` first — if none exist, a manual verification step is fine, don't introduce a new test framework for this alone).

**Interfaces:**
- The three session-verification dependencies now raise `HTTPException(401, {"error": "invalid_session", "detail": "<same human-readable message as before>"})` instead of a bare string `detail`.
- `authFetch` only clears the token and redirects when `res.status === 401` **and** the parsed body's `error` field equals `"invalid_session"`. Any other `401` (including the ones covered by Task 1, and any future one Task 1 didn't anticipate) is returned to the caller untouched, same as today's handling of non-401 errors.

- [ ] **Step 1: Update the three auth dependencies' error shape**

In `tamreena-web/backend/app/auth/dependencies.py`, change each `raise HTTPException(401, f"Invalid or expired session: {exc}")` (and the two similar raises: `"User no longer exists."`, `"Missing authentication token."`) to raise with a dict detail carrying `error: "invalid_session"`, e.g.:

```python
    except InvalidSessionToken as exc:
        raise HTTPException(401, {"error": "invalid_session", "detail": f"Invalid or expired session: {exc}"}) from exc
```

Do this for all three functions (`get_current_user`, `get_verified_token`, `get_verified_token_for_stream`) and their other 401-raising branches (`"User no longer exists."`, `"Missing authentication token."`).

- [ ] **Step 2: Update `authFetch` to require the discriminator**

In `tamreena-web/frontend/src/lib/api.ts`:

```ts
async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (res.status === 401) {
    const clone = res.clone();
    let isSessionExpiry = false;
    try {
      const body = await clone.json();
      isSessionExpiry = body?.detail?.error === 'invalid_session';
    } catch {
      // Non-JSON 401 body: not one of our own auth dependencies' responses,
      // so don't treat it as a session-expiry signal.
    }
    if (isSessionExpiry) {
      clearToken();
      window.location.href = '/signin';
    }
  }
  return res;
}
```

(`res.clone()` is required because the original `res` body still needs to be readable by the caller afterward — `Response` bodies can only be consumed once.)

- [ ] **Step 3: Update existing tests/callers that assert on the old plain-string `detail` shape**

Search the backend test suite for assertions like `resp.json()["detail"] == "Invalid or expired session..."` or similar exact-string checks against these three dependencies' 401 responses, and update them to the new `{"error": "invalid_session", "detail": "..."}` shape. Also check `parseErrorMessage` in `frontend/src/lib/api.ts:30-42` — it already handles `body?.detail` being either a string or an array; add a branch (or confirm existing fallback is acceptable) for `detail` now being an object in this one case, so error messages shown elsewhere in the UI don't regress to `"[object Object]"`.

- [ ] **Step 4: Run both test suites**

Run (from `tamreena-web/backend/`): `python -m pytest tests/ -q` — expect full pass.
Manually verify in the browser (per the earlier local test session): sign in, trigger a deliberate real session expiry (e.g. clear/corrupt the stored token, or wait out expiry) and confirm it still redirects to `/signin` as before; then trigger a nutrition/CV call and confirm a transient upstream hiccup no longer logs the user out.

---

## Investigation Notes (for context, not part of the fix)

- Frontend logout trigger: `frontend/src/lib/api.ts:49-60`, `authFetch`.
- Nutrition "select options" flow: `frontend/src/pages/nutrition/NutritionIntake.tsx` → `generateNutritionPlan()` → `POST /api/nutrition/generate` → `backend/app/nutrition/routes.py:48-67` → `call_upstream`/`proxy_json` → `NUTRITION_API_URL`.
- Computer-Vision flow: `frontend/src/pages/live-session/LiveSession.tsx` → `uploadLiveSessionVideo()` → `POST /api/live-session/upload` → `backend/app/live_session/routes.py:32-44` → `call_upstream`/`proxy_json` → `CV_API_URL`.
- The live-tracking WebSocket (`/ws/live-session`) and the nutrition SSE stream (`/api/nutrition/stream/{run_id}`) do **not** go through `authFetch` — their errors are handled entirely in local component state and cannot trigger this logout bug today. Fixed in Task 1 Step 5 anyway, for consistency, not because it's currently exploitable.
- Both `Computer-Vision` and `Nutrition-Plan-Generation` load `INTERNAL_SERVICE_TOKEN` once at process start (`pydantic-settings`). A container/process left running from before the token was added to its `.env` will fail-closed 401 every request until restarted — the most likely immediate trigger during local testing this session.
