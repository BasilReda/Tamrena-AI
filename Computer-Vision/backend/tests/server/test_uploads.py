import cv2
import numpy as np
from fastapi.testclient import TestClient
from src.server.app import app
from src.config.app_settings import settings

_HEADERS = {"X-Internal-Auth": "test-internal-service-token"}


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", "test-internal-service-token")
    return TestClient(app)


def _real_mp4_bytes(tmp_path) -> bytes:
    path = tmp_path / "real.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 32))
    for _ in range(5):
        writer.write(np.zeros((32, 32, 3), dtype=np.uint8))
    writer.release()
    return path.read_bytes()


def test_upload_rejects_undecodable_content_despite_allowed_extension(monkeypatch):
    client = _client(monkeypatch)
    r = client.post(
        "/api/uploads",
        headers=_HEADERS,
        files={"file": ("clip.mp4", b"this is not a video, just text bytes padded out", "video/mp4")},
    )
    assert r.status_code == 422


def test_upload_accepts_real_video_content(monkeypatch, tmp_path):
    client = _client(monkeypatch)
    r = client.post(
        "/api/uploads",
        headers=_HEADERS,
        files={"file": ("clip.mp4", _real_mp4_bytes(tmp_path), "video/mp4")},
    )
    assert r.status_code == 201
