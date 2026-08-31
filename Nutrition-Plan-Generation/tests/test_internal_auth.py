"""
This API has no user-level auth of its own — it's only meant to be called
by the tamreena-web BFF, which authenticates real end users. These tests
cover the shared-secret gate in app/api/dependencies.py that enforces that
boundary at this service's own edge, independent of network placement.
"""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

_TEST_TOKEN = "test-internal-service-token"


def _client() -> TestClient:
    return TestClient(app)


def test_nutrition_route_rejects_missing_auth_header(monkeypatch):
    monkeypatch.setattr(settings, "internal_service_token", _TEST_TOKEN)
    r = _client().get("/api/v1/nutrition/result/some-run-id")
    assert r.status_code == 401


def test_nutrition_route_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(settings, "internal_service_token", _TEST_TOKEN)
    r = _client().get("/api/v1/nutrition/result/some-run-id", headers={"X-Internal-Auth": "wrong-token"})
    assert r.status_code == 401


def test_nutrition_route_accepts_correct_token(monkeypatch):
    monkeypatch.setattr(settings, "internal_service_token", _TEST_TOKEN)
    r = _client().get("/api/v1/nutrition/result/some-run-id", headers={"X-Internal-Auth": _TEST_TOKEN})
    # 404 (unknown run_id) proves the auth gate let it through to the real
    # handler — a 401 here would mean the auth check itself is broken.
    assert r.status_code == 404


def test_nutrition_route_rejects_everything_when_token_unset(monkeypatch):
    """An unset internal_service_token must fail closed, not open — a
    missing .env value should surface as every call 401ing, never as an
    unauthenticated API."""
    monkeypatch.setattr(settings, "internal_service_token", "")
    r = _client().get("/api/v1/nutrition/result/some-run-id", headers={"X-Internal-Auth": ""})
    assert r.status_code == 401


def test_health_check_does_not_require_internal_auth():
    r = _client().get("/health")
    assert r.status_code == 200
