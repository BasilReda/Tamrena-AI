"""
Regression test: GET /api/v1/nutrition/history used to be shadowed by the
GET /{run_id} alias (registered before it, in app/api/routes/nutrition.py)
— FastAPI matches routes in registration order, and {run_id} matches any
single path segment including the literal "history". Every call to
/history 404'd as an unknown run_id instead of ever running
list_results().
"""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import nutrition_service

_TEST_TOKEN = "test-internal-service-token"


def _client() -> TestClient:
    return TestClient(app)


def _auth_headers() -> dict:
    return {"X-Internal-Auth": _TEST_TOKEN}


def test_history_route_lists_results_instead_of_404ing_as_unknown_run_id(monkeypatch):
    monkeypatch.setattr(settings, "internal_service_token", _TEST_TOKEN)
    monkeypatch.setattr(nutrition_service, "list_results", lambda: [])

    r = _client().get("/api/v1/nutrition/history", headers=_auth_headers())

    assert r.status_code == 200
    assert r.json()["data"] == []


def test_result_alias_still_resolves_a_real_run_id(monkeypatch):
    """The generic /{run_id} alias must still work for an actual run_id —
    this fix only reorders it after /history, it doesn't remove it."""
    monkeypatch.setattr(settings, "internal_service_token", _TEST_TOKEN)
    monkeypatch.setattr(nutrition_service, "get_result", lambda run_id: None)

    r = _client().get("/api/v1/nutrition/some-real-run-id", headers=_auth_headers())

    assert r.status_code == 404
    assert "some-real-run-id" in r.json()["detail"]
