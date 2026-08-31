"""
Live Session routes: proxies real video-upload and pose-tracking traffic
to Computer-Vision (already-integrated coworker service, see Stage 5),
and persists final tallies to this service's own workout_live_sessions
DynamoDB table (Computer-Vision has no endpoint of its own to store a
session's result). The WebSocket live-tracking proxy is added onto this
same router in a later change — see live_session_proxy below.
"""

import asyncio
import json
import secrets
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

import websockets
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.routing import APIWebSocketRoute
from pydantic import BaseModel

from app.auth.dependencies import get_verified_token
from app.auth.tokens import InvalidSessionToken, decode_access_token
from app.config import CV_API_URL, INTERNAL_SERVICE_TOKEN
from app.db import get_live_sessions_table
from app.live_session.ownership import owns, record_ownership
from app.tamreena_client import call_upstream, proxy_json

router = APIRouter(prefix="/api/live-session")


@router.post("/upload")
async def upload_live_session_video(file: UploadFile = File(...), token: str = Depends(get_verified_token)):
    file_bytes = await file.read()
    files = {"file": (file.filename or "upload.mp4", file_bytes, file.content_type)}
    resp = await call_upstream("POST", "/api/uploads", token=None, base_url=CV_API_URL, files=files)
    if resp is not None and resp.status_code == 201:
        try:
            upload_id = resp.json().get("id")
        except ValueError:
            upload_id = None
        if upload_id:
            record_ownership(upload_id, decode_access_token(token), "upload")
    return proxy_json(resp, internal_auth=True)


@router.get("/report/{session_id}")
async def get_live_session_report(session_id: str, token: str = Depends(get_verified_token)):
    # Computer-Vision's own /api/sessions/{id} has no auth or per-user
    # scoping (session ids are predictable timestamps, not secrets) — this
    # ownership check is the only thing stopping one signed-in user from
    # reading another user's session report through this proxy.
    if not owns(session_id, decode_access_token(token)):
        raise HTTPException(404, "Unknown session.")
    resp = await call_upstream("GET", f"/api/sessions/{session_id}", token=None, base_url=CV_API_URL)
    return proxy_json(resp, internal_auth=True)


class LiveSessionResultRequest(BaseModel):
    exercise_id: str
    exercise_name: str
    reps: int
    good: int
    bad: int
    cv_session_id: Optional[str] = None


@router.post("/result")
async def save_live_session_result(body: LiveSessionResultRequest, token: str = Depends(get_verified_token)):
    session_id = secrets.token_hex(12)
    item = {
        "session_id": session_id,
        "exercise_id": body.exercise_id,
        "exercise_name": body.exercise_name,
        "reps": body.reps,
        "good": body.good,
        "bad": body.bad,
        "cv_session_id": body.cv_session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    get_live_sessions_table().insert_one(item)
    item.pop("_id", None)
    return item


# rstrip: CV_API_URL may carry a trailing slash (it does in prod config); left
# in, string-concatenating "/ws/live" below produces a double slash that the
# upstream server rejects with a bare 403 before routing ever sees it.
_CV_WS_URL = CV_API_URL.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")


async def live_session_proxy(
    websocket: WebSocket,
    exercise: str,
    token: str,
    source: str = "video",
    video: Optional[str] = None,
):
    """
    Proxies to Computer-Vision's real /ws/live?exercise=&source=&video=
    endpoint, relaying binary JPEG frames and JSON state/end/error events
    downstream, and the browser's {"action":"stop"} command (plus, for
    source="browser", the browser's own live JPEG frames) upstream. token is
    a query param (not a header) because the browser's native WebSocket API
    cannot set custom headers on the handshake — same constraint already
    solved for the SSE stream in app/workout/routes.py.

    source="video" (default, backward compatible with every existing
    caller): analyzes a video previously uploaded via POST
    /api/live-session/upload; video is required and is the upload id.

    source="browser": no prior upload — the client (its camera, captured to
    canvas) pushes binary JPEG frames directly over this open socket for
    live analysis; video is unused.

    Registered directly (not via @router.websocket) and appended to
    router.routes below: router carries prefix="/api/live-session" (set in
    Task 2 for the HTTP routes above), and APIRouter.websocket() always
    builds the final path as `self.prefix + path` with no per-route
    opt-out. Going through the decorator here would register this at
    /api/live-session/ws/live-session instead of the documented
    /ws/live-session. Constructing the APIWebSocketRoute directly and
    appending it to the same router's .routes list keeps this on the one
    router object main.py already includes (no main.py change needed)
    while landing on the correct, unprefixed path.
    """
    await websocket.accept()

    try:
        user_id = decode_access_token(token)
    except InvalidSessionToken:
        await websocket.send_json({"type": "error", "message": "Invalid or expired session."})
        await websocket.close()
        return

    if source not in ("video", "browser"):
        await websocket.send_json({"type": "error", "message": "source must be 'video' or 'browser'."})
        await websocket.close()
        return

    if source == "video":
        if not video:
            await websocket.send_json({"type": "error", "message": "video is required when source='video'."})
            await websocket.close()
            return
        # Computer-Vision has no auth of its own — without this check any
        # signed-in user could point source=video at an upload id they
        # don't own and have it analyzed here.
        if not owns(video, user_id):
            await websocket.send_json({"type": "error", "message": "Unknown upload."})
            await websocket.close()
            return
        upstream_url = (
            f"{_CV_WS_URL}/ws/live?exercise={quote(exercise, safe='')}"
            f"&source=video&video=upload:{quote(video, safe='')}"
        )
    else:
        upstream_url = f"{_CV_WS_URL}/ws/live?exercise={quote(exercise, safe='')}&source=browser"

    # Computer-Vision has no user-level auth of its own — this shared secret
    # is what it checks instead (see app/config.py's INTERNAL_SERVICE_TOKEN).
    async with websockets.connect(
        upstream_url, additional_headers={"X-Internal-Auth": INTERNAL_SERVICE_TOKEN}
    ) as upstream:

        async def forward_upstream_to_client() -> None:
            async for message in upstream:
                if isinstance(message, (bytes, bytearray)):
                    await websocket.send_bytes(message)
                else:
                    if isinstance(message, str):
                        try:
                            payload = json.loads(message)
                        except (json.JSONDecodeError, ValueError):
                            payload = None
                        if isinstance(payload, dict) and payload.get("type") == "end":
                            session_id = payload.get("session_id")
                            if session_id:
                                record_ownership(session_id, user_id, "session")
                    await websocket.send_text(message)

        async def forward_client_to_upstream() -> None:
            try:
                while True:
                    message = await websocket.receive()
                    if message["type"] == "websocket.disconnect":
                        return
                    if message.get("bytes") is not None:
                        await upstream.send(message["bytes"])
                    elif message.get("text") is not None:
                        text = message["text"]
                        try:
                            parsed = json.loads(text)
                            await upstream.send(json.dumps(parsed))
                        except (json.JSONDecodeError, ValueError):
                            await upstream.send(text)
            except WebSocketDisconnect:
                pass

        forward1 = asyncio.create_task(forward_upstream_to_client())
        forward2 = asyncio.create_task(forward_client_to_upstream())
        try:
            await asyncio.wait({forward1, forward2}, return_when=asyncio.ALL_COMPLETED)
        finally:
            forward1.cancel()
            forward2.cancel()
            try:
                await websocket.close()
            except RuntimeError:
                pass


router.routes.append(
    APIWebSocketRoute("/ws/live-session", endpoint=live_session_proxy, name="live_session_proxy")
)
