"""
Tests for app/nutrition/routes.py's HTTP routes: generate and result. The
SSE stream proxy route is tested separately in test_nutrition_stream.py.
"""

import respx
from fastapi.testclient import TestClient
from httpx import Response

from app import tamreena_client
from app.auth import tokens
from app.config import NUTRITION_API_URL


def _client() -> TestClient:
    import app.main as m
    return TestClient(m.app)


def _auth_header() -> dict:
    token = tokens.create_access_token(user_id="507f1f77bcf86cd799439011")
    return {"Authorization": f"Bearer {token}"}


_VALID_BODY = {
    "age": 28,
    "gender": "male",
    "height_cm": 178.0,
    "weight_kg": 80.0,
    "goal": "maintenance",
    "activity_level": "moderate",
    "diet_type": "normal",
    "preferences": ["chicken", "rice"],
    "allergies": ["peanuts"],
    "additional_notes": None,
}


@respx.mock
def test_generate_forwards_body_and_omits_auth_header():
    from app.rate_limit import nutrition_generate_limiter
    nutrition_generate_limiter.reset()
    respx.post(f"{NUTRITION_API_URL}/generate-plan").mock(return_value=Response(404))
    route = respx.post(f"{NUTRITION_API_URL}/api/v1/nutrition/generate").mock(
        return_value=Response(202, json={"run_id": "abc123", "status": "started", "message": "Started."})
    )
    client = _client()
    r = client.post("/api/nutrition/generate", json=_VALID_BODY, headers=_auth_header())
    assert r.status_code == 202
    assert r.json()["run_id"] == "abc123"
    assert "Authorization" not in route.calls.last.request.headers
    assert route.calls.last.request.read().decode().count('"meal_generation_mode":"dataset"') == 1


@respx.mock
def test_generate_sends_internal_auth_header(monkeypatch):
    from app.rate_limit import nutrition_generate_limiter
    nutrition_generate_limiter.reset()
    monkeypatch.setattr(tamreena_client, "INTERNAL_SERVICE_TOKEN", "test-internal-token")
    respx.post(f"{NUTRITION_API_URL}/generate-plan").mock(return_value=Response(404))
    route = respx.post(f"{NUTRITION_API_URL}/api/v1/nutrition/generate").mock(
        return_value=Response(202, json={"run_id": "abc123", "status": "started", "message": "Started."})
    )
    client = _client()
    client.post("/api/nutrition/generate", json=_VALID_BODY, headers=_auth_header())
    assert route.calls.last.request.headers["X-Internal-Auth"] == "test-internal-token"


def test_generate_rejects_missing_bff_token():
    client = _client()
    r = client.post("/api/nutrition/generate", json=_VALID_BODY)
    assert r.status_code in (401, 403)


def test_generate_rejects_out_of_range_age():
    client = _client()
    body = {**_VALID_BODY, "age": 5}
    r = client.post("/api/nutrition/generate", json=body, headers=_auth_header())
    assert r.status_code == 422


@respx.mock
def test_get_result_forwards_and_omits_auth_header():
    from app.auth import models
    models.set_last_nutrition_run_id("507f1f77bcf86cd799439011", "abc123")

    route = respx.get(f"{NUTRITION_API_URL}/api/v1/nutrition/result/abc123").mock(
        return_value=Response(200, json={"run_id": "abc123", "success": True, "error": None})
    )
    client = _client()
    r = client.get("/api/nutrition/result/abc123", headers=_auth_header())
    assert r.status_code == 200
    assert r.json()["run_id"] == "abc123"
    assert "Authorization" not in route.calls.last.request.headers


@respx.mock
def test_get_result_rejects_run_id_belonging_to_another_user():
    from app.auth import models
    models.set_last_nutrition_run_id("someone-elses-user-id", "abc123")

    route = respx.get(f"{NUTRITION_API_URL}/api/v1/nutrition/result/abc123").mock(
        return_value=Response(200, json={"run_id": "abc123", "success": True, "error": None})
    )
    client = _client()
    r = client.get("/api/nutrition/result/abc123", headers=_auth_header())
    assert r.status_code == 404
    assert not route.called


@respx.mock
def test_get_result_returns_404_when_upstream_404s():
    respx.get(f"{NUTRITION_API_URL}/api/v1/nutrition/result/unknown").mock(
        return_value=Response(404, json={"detail": "No result found for run_id=unknown."})
    )
    client = _client()
    r = client.get("/api/nutrition/result/unknown", headers=_auth_header())
    assert r.status_code == 404


def test_get_result_rejects_missing_bff_token():
    client = _client()
    r = client.get("/api/nutrition/result/abc123")
    assert r.status_code in (401, 403)


@respx.mock
def test_generate_persists_last_nutrition_run_id_on_success():
    from app.rate_limit import nutrition_generate_limiter
    nutrition_generate_limiter.reset()
    respx.post(f"{NUTRITION_API_URL}/generate-plan").mock(return_value=Response(404))
    respx.post(f"{NUTRITION_API_URL}/api/v1/nutrition/generate").mock(
        return_value=Response(202, json={"run_id": "abc123", "status": "started", "message": "Started."})
    )
    client = _client()
    r = client.post("/api/nutrition/generate", json=_VALID_BODY, headers=_auth_header())
    assert r.status_code == 202

    from app.auth import models
    assert models.get_last_nutrition_run_id("507f1f77bcf86cd799439011") == "abc123"


@respx.mock
def test_generate_does_not_persist_run_id_on_upstream_failure():
    from app.rate_limit import nutrition_generate_limiter
    nutrition_generate_limiter.reset()
    respx.post(f"{NUTRITION_API_URL}/generate-plan").mock(return_value=Response(500))
    respx.post(f"{NUTRITION_API_URL}/api/v1/nutrition/generate").mock(return_value=Response(500))
    client = _client()
    r = client.post("/api/nutrition/generate", json=_VALID_BODY, headers=_auth_header())
    assert r.status_code == 500

    from app.auth import models
    assert models.get_last_nutrition_run_id("507f1f77bcf86cd799439011") is None


def test_get_last_returns_run_id_when_present():
    from app.auth import models
    models.set_last_nutrition_run_id("507f1f77bcf86cd799439011", "abc123")

    client = _client()
    r = client.get("/api/nutrition/last", headers=_auth_header())
    assert r.status_code == 200
    assert r.json() == {"run_id": "abc123"}


def test_get_last_returns_null_when_absent():
    client = _client()
    r = client.get("/api/nutrition/last", headers=_auth_header())
    assert r.status_code == 200
    assert r.json() == {"run_id": None}


def test_get_last_rejects_missing_bff_token():
    client = _client()
    r = client.get("/api/nutrition/last")
    assert r.status_code in (401, 403)


def test_generate_rejects_after_rate_limit_exceeded():
    from app.rate_limit import nutrition_generate_limiter
    nutrition_generate_limiter.reset()
    for _ in range(3):
        nutrition_generate_limiter.check("507f1f77bcf86cd799439011")

    client = _client()
    r = client.post("/api/nutrition/generate", json=_VALID_BODY, headers=_auth_header())
    assert r.status_code == 429


@respx.mock
def test_generate_translates_upstream_401_to_503():
    from app.rate_limit import nutrition_generate_limiter
    nutrition_generate_limiter.reset()
    respx.post(f"{NUTRITION_API_URL}/generate-plan").mock(return_value=Response(404))
    respx.post(f"{NUTRITION_API_URL}/api/v1/nutrition/generate").mock(
        return_value=Response(401, json={"detail": "Invalid or missing internal service credentials"})
    )
    client = _client()
    r = client.post("/api/nutrition/generate", json=_VALID_BODY, headers=_auth_header())
    assert r.status_code == 503
    assert "misconfigured" in r.json()["detail"].lower()

