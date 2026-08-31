"""Live coaching stream — one WebSocket per workout.

Protocol
--------
Client connects to
``/ws/live?exercise=<key>&source=webcam|video[&video=<ref>]``.

``video`` reference forms (only with ``source=video``):

* ``upload:<id>`` — a video previously uploaded via ``POST /api/uploads``
  (the **web app flow**; ids resolve strictly inside ``uploads/videos/``);
* an explicit path — developer escape hatch / CLI parity (local, single-user);
* omitted — falls back to ``VIDEO_PATH`` from ``.env``.

Server → client::

    binary frame  — one JPEG per processed frame (~capture rate)
    {"type": "state", ...}  — metrics/feedback, ~15 Hz while active
    {"type": "end",  ...}   — workout finished; carries session_id of export
                              and rendered_video when rendering is enabled
    {"type": "error", ...}  — fatal problem (unknown exercise, no camera, ...)

Client → server::

    {"action": "stop"}      — finish now (rep history so far is exported)

Only ONE ``source=webcam`` session may run at a time (a webcam is a
single-user device); a second webcam connection while one is active is
rejected with an error event and closed. ``source=video`` sessions don't
share a hardware resource and are not serialized behind this gate.
"""

import asyncio
import queue
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...exercises.registry import registry
from ..auth import internal_auth_ok
from ..live_runner import LiveSession
from .uploads import stored_path

router = APIRouter(tags=["live"])

# All currently-active sessions (webcam AND video). A single slot isn't
# enough once multiple video sessions can run concurrently: the webcam
# gate must know whether ANY session is still alive, not just the most
# recently connected one — otherwise a still-running video session's slot
# can be silently overwritten (and then cleared) by a second, unrelated
# video session finishing first, letting a webcam connection through while
# the first video session is still using CPU/GPU.
_active_sessions: set[LiveSession] = set()


@router.websocket("/ws/live")
async def live_session(websocket: WebSocket, exercise: str, source: str = "webcam", video: Optional[str] = None):
    await websocket.accept()

    if not internal_auth_ok(websocket.headers.get("x-internal-auth", "")):
        await websocket.send_json({"type": "error", "message": "Missing or invalid internal service credentials."})
        return await websocket.close()

    if exercise not in registry.list():
        await websocket.send_json({"type": "error", "message": f"Unknown exercise '{exercise}'"})
        return await websocket.close()
    if source not in ("webcam", "video", "browser"):
        await websocket.send_json({"type": "error", "message": "source must be 'webcam', 'video', or 'browser'"})
        return await websocket.close()

    # Resolve upload references to real paths inside uploads/videos/.
    if video is not None and video.startswith("upload:"):
        upload_id = video[len("upload:"):]
        resolved = stored_path(upload_id)
        if resolved is None:
            await websocket.send_json({"type": "error", "message": f"Unknown upload '{upload_id}'"})
            return await websocket.close()
        video = str(resolved)

    if source == "webcam" and any(s.is_alive() for s in _active_sessions):
        await websocket.send_json({"type": "error", "message": "Another live session is already running"})
        return await websocket.close()

    events: "queue.Queue" = queue.Queue(maxsize=120)
    frame_queue: Optional["queue.Queue"] = queue.Queue(maxsize=30) if source == "browser" else None
    session = LiveSession(exercise, source, events, video_path=video, frame_queue=frame_queue)
    # Tracked for every session (not just webcam) so a webcam session
    # started while any video session is running is still correctly
    # blocked by the check above — only the check itself is source-scoped.
    _active_sessions.add(session)
    session.start()

    async def forward_events() -> None:
        """Pump runner events to the socket without blocking the loop."""
        loop = asyncio.get_running_loop()
        while True:
            event = await loop.run_in_executor(None, events.get)
            if isinstance(event, (bytes, bytearray)):
                await websocket.send_bytes(bytes(event))
            else:
                await websocket.send_json(event)
                if event.get("type") in ("end", "error"):
                    return

    async def listen_commands() -> None:
        import json
        try:
            while True:
                msg = await websocket.receive()
                if msg["type"] == "websocket.disconnect":
                    session.stop()
                    if frame_queue is not None:
                        try:
                            frame_queue.put_nowait(None)
                        except Exception:
                            pass
                    return
                if msg.get("bytes") is not None and frame_queue is not None:
                    try:
                        frame_queue.put_nowait(msg["bytes"])
                    except queue.Full:
                        try:
                            frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                        try:
                            frame_queue.put_nowait(msg["bytes"])
                        except Exception:
                            pass
                elif msg.get("text") is not None:
                    try:
                        message = json.loads(msg["text"])
                        if message.get("action") == "stop":
                            session.stop()
                            if frame_queue is not None:
                                try:
                                    frame_queue.put_nowait(None)
                                except Exception:
                                    pass
                    except Exception:
                        pass
        except WebSocketDisconnect:
            session.stop()
            if frame_queue is not None:
                try:
                    frame_queue.put_nowait(None)
                except Exception:
                    pass

    forward = asyncio.create_task(forward_events())
    listen = asyncio.create_task(listen_commands())
    try:
        await asyncio.wait({forward, listen}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        session.stop()
        if frame_queue is not None:
            try:
                frame_queue.put_nowait(None)
            except Exception:
                pass
        forward.cancel()
        listen.cancel()
        _active_sessions.discard(session)
        try:
            await websocket.close()
        except RuntimeError:
            pass  # already closed by the peer
