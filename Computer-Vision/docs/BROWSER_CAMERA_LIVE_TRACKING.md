# Feature: Browser Camera Live Tracking

## Status
Draft — not yet implemented.

## Problem

The Live page (`frontend/src/features/live/page.tsx`) already offers a
`webcam` source, but it is **not** the user's device camera: `source=webcam`
tells the backend to open a camera attached to the *server host* via
`cv2.VideoCapture` (`backend/src/services/video_source.py`). That only works
when the backend process runs on the same machine as the camera (local dev /
desktop use). In a normally deployed web app, the user's laptop/phone camera
is not reachable from the backend host at all, so this mode is unusable for
real end users.

The only path that works for a remote user today is **file upload**: pick a
pre-recorded clip, upload it (`POST /api/uploads`), then stream it through
`/ws/live?source=video&video=upload:<id>` where `GymEngine` runs MediaPipe
pose detection frame-by-frame, applies the exercise's rules
(`backend/src/exercises/rules.py`), counts reps, and classifies each rep as
good/bad.

## Goal

Let a user open their **own device camera in the browser** and get the exact
same live-coaching experience they get today from video upload — same rep
counter, same good/bad classification, same rule lights, same session
summary/report — but sourced from a live `getUserMedia` stream instead of a
pre-recorded file, and without depending on server-machine hardware.

## Non-goals

- Replacing the existing host-webcam (`source=webcam`) developer/desktop mode
  — it stays for local CLI/dev use.
- On-device (browser-only) rep counting with no backend involvement. The
  scoring/rule engine (`GymEngine`, `exercises/rules.py`) is the single
  source of truth for what counts as a rep and whether it's good or bad; the
  browser must not duplicate or diverge from that logic.

## Proposed approach

### Frame transport: browser → backend, reuse `GymEngine`

1. Frontend requests `getUserMedia({ video: true })`, renders the local
   stream to a hidden `<video>`, and grabs frames from it (`canvas.drawImage`
   → JPEG blob) at a fixed capture rate (e.g. 10–15 fps — matching the
   existing "~15 Hz state" cadence already used for video/webcam sessions).
2. Frontend opens the existing `/ws/live` WebSocket but with a **new**
   `source=browser` (name TBD) instead of `webcam`/`video`. No `video`
   query param — there's no file or host device to resolve.
3. Each captured frame is sent as a **binary WebSocket message** from client
   to server. `live.py`'s `listen_commands()` loop currently only expects
   JSON (`{"action": "stop"}`); it needs a branch for binary frames that
   feeds them into the running `LiveSession`/`GymEngine` in place of the
   `cv2.VideoCapture` read loop.
4. `GymEngine`/`pose_service.py` keeps running MediaPipe pose landmarking,
   `exercises/rules.py` keeps evaluating the selected exercise's rules per
   frame, and `LiveSession` keeps emitting the same `state`/`end` events the
   frontend already renders (`state.reps`, `state.good`, `state.bad`,
   `state.rules[]`, `state.stage`, `state.live_score`, etc. — see
   `frontend/src/lib/api/live.ts` / `frontend/src/features/live/page.tsx`).
5. On completion, the session is exported and reported through the same
   analytics/report path as upload sessions.

This keeps rep counting and good/bad classification **identical** to the
upload flow by construction — same engine, same rules, same event shape.
Only the frame *source* changes.

### Why not on-device MediaPipe (browser-only)?

Running `@mediapipe/tasks-vision` in the browser and counting reps in JS
would need the entire rule set in `exercises/rules.py` (per-exercise angle
thresholds, stage machines, good/bad scoring, 3D mode, side detection)
duplicated and kept in sync in TypeScript — a maintenance and drift risk the
brainstorming discussion should weigh explicitly before committing to the
transport approach above. Documented here as the alternative, not the
recommendation.

## Backend changes (sketch)

- `backend/src/server/routes/live.py`
  - Accept `source == "browser"` alongside `"webcam"`/`"video"`.
  - Extend `listen_commands()` to route incoming **binary** frames to the
    session instead of only parsing `receive_json()`.
  - Decide whether `source=browser` shares the single-active-session gate
    that `source=webcam` uses today (it's still "one camera, one user" per
    session, but no longer a shared host resource — likely should stay
    per-session, not globally exclusive, since two browser tabs/users would
    each bring their own camera).
- `backend/src/server/live_runner.py` (`LiveSession`)
  - Add an ingest path that accepts pushed JPEG/PNG frames (decode via
    `cv2.imdecode`) instead of pulling from `cv2.VideoCapture`.
- Reuse as-is: `GymEngine`, `pose_service.py`, `exercises/rules.py`,
  `pose_segments.py`, session duration cap
  (`AppSettings.MAX_SESSION_SECONDS`), and analytics/report generation.

## Frontend changes (sketch)

- `frontend/src/features/live/page.tsx`
  - Add a third source option (`"browser"`) alongside `webcam`/`video`, or
    replace the current `webcam` option's behavior/label if the host-camera
    mode is being deprecated for end users (decision needed — see Open
    Questions).
  - Camera permission flow: request `getUserMedia`, handle
    denied/unavailable camera with a clear inline error (mirrors the
    existing `status === "error"` retry/back-to-setup pattern already on
    this page).
  - Frame capture loop: `requestAnimationFrame`/`setInterval`-driven canvas
    grab → JPEG encode → send over the existing WebSocket connection
    (`useLiveSession` hook), throttled to the agreed capture rate.
  - Local camera preview should render immediately (before the first
    processed frame streams back), matching this page's existing rule that
    "nothing shifts while streaming."
- `frontend/src/lib/api/live.ts`
  - Extend the `LiveSource` type with the new source value.

## Reused pieces (no changes needed)

- Rep counting, stage machine, good/bad scoring: `exercises/rules.py`,
  `services/gym_engine.py`.
- Live telemetry UI: reps/good/bad tiles, stage card, joint angle, form
  score ring, rule lights, feedback panel
  (`frontend/src/features/live/page.tsx`, `feedback.tsx`, `status.tsx`).
- Session completion flow: `WorkoutSummary`, `WorkoutActions`, report
  generation.
- Session duration cap and per-session resource limits already added for
  webcam sessions ([memory: Task 3 duration cap / webcam-scoped
  concurrency gate]).

## Open questions

1. Does `source=browser` need its own concurrency gate, or is per-session
   isolation (no shared hardware) sufficient?
2. Target capture rate/resolution — balance MediaPipe accuracy against
   upload bandwidth from the browser on slower connections.
3. Should the existing `source=webcam` (host-camera) option stay visible in
   production, or be dev/CLI-only once browser capture ships?
4. Frame encoding on the client: JPEG quality/size tradeoff, and whether to
   send raw frames or use a compressed video track (e.g. WebCodecs) for
   efficiency at higher fps.
5. Auth/session ownership: browser camera sessions should follow the same
   `live_session_ownership` DynamoDB tracking already in place for upload
   sessions, so a user can't see another user's live session.
