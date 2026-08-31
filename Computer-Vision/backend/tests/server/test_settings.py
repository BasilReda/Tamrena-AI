from pathlib import Path

from fastapi.testclient import TestClient
from src.server.app import app
from src.config.app_settings import settings, ASSETS_DIR, UPLOADS_DIR

_HEADERS = {"X-Internal-Auth": "test-internal-service-token"}


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", "test-internal-service-token")
    return TestClient(app)


def test_video_path_outside_allowed_dirs_is_rejected(monkeypatch):
    client = _client(monkeypatch)
    r = client.put("/api/settings", json={"VIDEO_PATH": "/etc/passwd"}, headers=_HEADERS)
    assert r.status_code == 422


def test_video_path_inside_assets_is_accepted(monkeypatch):
    client = _client(monkeypatch)
    sample = ASSETS_DIR / "videos"
    sample.mkdir(parents=True, exist_ok=True)
    r = client.put("/api/settings", json={"VIDEO_PATH": "assets/videos"}, headers=_HEADERS)
    assert r.status_code == 200


def test_video_path_inside_uploads_is_accepted(monkeypatch):
    client = _client(monkeypatch)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    r = client.put("/api/settings", json={"VIDEO_PATH": "uploads/videos"}, headers=_HEADERS)
    assert r.status_code == 200


def test_model_path_outside_models_dir_is_rejected(monkeypatch):
    client = _client(monkeypatch)
    r = client.put("/api/settings", json={"MODEL_PATH": "/tmp/evil.task"}, headers=_HEADERS)
    assert r.status_code == 422


def test_video_path_traversal_is_rejected(monkeypatch):
    """Verify path-traversal attacks (../ segments) are blocked.

    This test specifically checks that payloads like "assets/../../../etc/hosts"
    are rejected even though they start with an allowed prefix. The fix requires
    resolving paths before containment checks.
    """
    client = _client(monkeypatch)
    r = client.put(
        "/api/settings",
        json={"VIDEO_PATH": "assets/../../../Windows/System32/drivers/etc/hosts"},
        headers=_HEADERS,
    )
    assert r.status_code == 422
