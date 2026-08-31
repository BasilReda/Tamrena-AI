"""Covers the /ws/live concurrency gate in src/server/routes/live.py.

Reproduces a bug found in review of the original single-`_active_session`
slot: once source="video" sessions could run concurrently (webcam-only
gate), a single slot got silently overwritten by whichever session
connected most recently, and cleared by whichever session's connection
tore down first — even if an *earlier* session was still alive. That let a
webcam connection through while a video session was still running.

These tests drive the async websocket handler directly (bypassing the real
ASGI/TestClient websocket transport, which isn't a good fit for holding two
concurrent long-lived connections open) with a lightweight fake WebSocket
and a fake LiveSession that mimics the is_alive()/stop() contract the route
depends on, without any real camera/model/thread.
"""

import asyncio
import queue

import src.server.routes.live as live_mod
from src.config.app_settings import settings


class FakeWebSocket:
    """Minimal stand-in for fastapi.WebSocket — just enough surface for
    live_session() to run: accept/send_json/send_bytes/close, and a
    receive_json() that blocks (as a real still-connected client would)
    until the test's cleanup cancels it."""

    def __init__(self):
        self.headers = {"x-internal-auth": "test-token"}
        self.sent = []
        self.closed = False

    async def accept(self):
        pass

    async def send_json(self, data):
        self.sent.append(data)

    async def send_bytes(self, data):
        pass

    async def close(self):
        self.closed = True

    async def receive_json(self):
        await asyncio.Event().wait()  # never resolves; cancelled by cleanup


class FakeLiveSession:
    """Stand-in for LiveSession. No real thread, camera, or model — just
    the is_alive()/stop() contract routes/live.py relies on, plus a test
    hook (`finish`) to simulate the underlying thread completing its run()
    and publishing its terminal event, the way the real LiveSession does."""

    instances = []

    def __init__(self, exercise, source, events, video_path=None, use_3d=None, frame_queue=None, **kwargs):
        self.exercise = exercise
        self.source = source
        self.events: "queue.Queue" = events
        self.video_path = video_path
        self.frame_queue = frame_queue
        self._alive = True
        FakeLiveSession.instances.append(self)

    def start(self):
        pass  # the test drives lifecycle manually via finish()

    def stop(self):
        pass  # a client-initiated stop request; doesn't by itself end is_alive()

    def is_alive(self):
        return self._alive

    def finish(self):
        self._alive = False
        self.events.put_nowait({"type": "end", "reps": 0})


def test_webcam_gate_blocks_while_any_video_session_is_alive(monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", "test-token")
    monkeypatch.setattr(live_mod, "LiveSession", FakeLiveSession)
    live_mod._active_sessions.clear()
    FakeLiveSession.instances.clear()

    async def scenario():
        ws_a, ws_b = FakeWebSocket(), FakeWebSocket()

        task_a = asyncio.create_task(
            live_mod.live_session(ws_a, exercise="squat", source="video", video=None)
        )
        task_b = asyncio.create_task(
            live_mod.live_session(ws_b, exercise="squat", source="video", video=None)
        )

        # Let both connections clear the gate, register themselves, and
        # reach their blocking `await asyncio.wait(...)`.
        await asyncio.sleep(0.1)
        assert len(FakeLiveSession.instances) == 2
        session_a, session_b = FakeLiveSession.instances

        # Session B (connected second) finishes first — the exact ordering
        # that broke the old single-slot `_active_session`.
        session_b.finish()
        await asyncio.wait_for(task_b, timeout=2)

        assert session_a.is_alive()

        # A webcam connection must still be rejected: session A is alive.
        ws_c = FakeWebSocket()
        await asyncio.wait_for(
            live_mod.live_session(ws_c, exercise="squat", source="webcam", video=None),
            timeout=2,
        )
        assert ws_c.sent == [
            {"type": "error", "message": "Another live session is already running"}
        ]
        assert ws_c.closed is True

        # cleanup: end session A so no task is left dangling
        session_a.finish()
        await asyncio.wait_for(task_a, timeout=2)

    asyncio.run(scenario())


def test_webcam_gate_allows_connection_once_all_sessions_have_finished(monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", "test-token")
    monkeypatch.setattr(live_mod, "LiveSession", FakeLiveSession)
    live_mod._active_sessions.clear()
    FakeLiveSession.instances.clear()

    async def scenario():
        ws_a = FakeWebSocket()
        task_a = asyncio.create_task(
            live_mod.live_session(ws_a, exercise="squat", source="video", video=None)
        )
        await asyncio.sleep(0.1)
        assert len(FakeLiveSession.instances) == 1
        session_a = FakeLiveSession.instances[0]

        session_a.finish()
        await asyncio.wait_for(task_a, timeout=2)

        ws_b = FakeWebSocket()
        task_b = asyncio.create_task(
            live_mod.live_session(ws_b, exercise="squat", source="webcam", video=None)
        )
        await asyncio.sleep(0.1)

        # Not rejected by the gate: no "Another live session" error sent,
        # and a real session got registered (the connection was accepted).
        assert not any(
            e.get("message") == "Another live session is already running"
            for e in ws_b.sent
        )
        assert len(FakeLiveSession.instances) == 2

        FakeLiveSession.instances[-1].finish()
        await asyncio.wait_for(task_b, timeout=2)

    asyncio.run(scenario())


def test_browser_source_initializes_frame_queue(monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", "test-token")
    monkeypatch.setattr(live_mod, "LiveSession", FakeLiveSession)
    live_mod._active_sessions.clear()
    FakeLiveSession.instances.clear()

    async def scenario():
        ws = FakeWebSocket()
        task = asyncio.create_task(
            live_mod.live_session(ws, exercise="squat", source="browser", video=None)
        )
        await asyncio.sleep(0.1)
        assert len(FakeLiveSession.instances) == 1
        session = FakeLiveSession.instances[0]
        assert session.source == "browser"
        assert session.frame_queue is not None

        session.finish()
        await asyncio.wait_for(task, timeout=2)

    asyncio.run(scenario())
