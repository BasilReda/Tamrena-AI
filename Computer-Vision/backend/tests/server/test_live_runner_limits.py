import queue

import cv2
import numpy as np

import src.server.live_runner as live_runner_mod
from src.config.app_settings import settings
from src.server.live_runner import LiveSession


def test_max_session_seconds_setting_exists_and_defaults_reasonably():
    assert settings.MAX_SESSION_SECONDS > 0
    assert settings.MAX_SESSION_SECONDS <= 3600  # sanity: not accidentally unlimited


class _FakePoseService:
    """No-op stand-in for PoseService (needs real mediapipe, stubbed out in
    conftest.py). The duration cap fires before the loop ever calls
    detect(), so this never actually needs to do anything."""

    def __init__(self, *_a, **_k):
        pass

    def detect(self, *_a, **_k):
        return None


def _write_clip(path, frames=3):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 32))
    for _ in range(frames):
        writer.write(np.zeros((32, 32, 3), dtype=np.uint8))
    writer.release()
    return path


def test_duration_cap_breaks_loop_with_stopped_reason_and_no_error_event(monkeypatch, tmp_path):
    """Covers the reviewer-found bug: the duration cap must not publish a
    terminal "error" event. forward_events() in routes/live.py treats
    "error" as connection-ending and returns immediately after forwarding
    one, which would silently drop the "end" event (and its session_id)
    that follows right after in the normal cleanup path. The cap should
    break the loop silently and let "end" carry
    stopped_reason="max_duration_exceeded" instead.
    """
    clip = _write_clip(tmp_path / "clip.mp4")

    monkeypatch.setattr(live_runner_mod, "PoseService", _FakePoseService)
    monkeypatch.setattr(settings, "MAX_SESSION_SECONDS", -1.0)  # fires on the first check
    monkeypatch.setattr(settings, "EXPORT_DIR", tmp_path / "sessions")
    monkeypatch.setattr(settings, "SAVE_OUTPUT", False)

    events: "queue.Queue" = queue.Queue(maxsize=50)
    session = LiveSession("squat", "video", events, video_path=str(clip))
    session.run()  # synchronous call — no need for a real thread here

    collected = []
    while not events.empty():
        collected.append(events.get_nowait())

    assert not any(isinstance(e, dict) and e.get("type") == "error" for e in collected)
    ended = [e for e in collected if isinstance(e, dict) and e.get("type") == "end"]
    assert len(ended) == 1
    assert ended[0]["stopped_reason"] == "max_duration_exceeded"
