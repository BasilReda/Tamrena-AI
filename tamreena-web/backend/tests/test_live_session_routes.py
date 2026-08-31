"""
Tests for app/live_session/routes.py's HTTP routes: the video upload
proxy and the result-persistence route. The WebSocket proxy route is
tested separately in test_live_session_ws.py.
"""

import respx
from fastapi.testclient import TestClient
from httpx import Response

from app import tamreena_client
from app.auth import tokens
from app.config import CV_API_URL, LIVE_SESSIONS_TABLE_NAME
from app.live_session.ownership import record_ownership


def _client() -> TestClient:
    import app.main as m
    return TestClient(m.app)


def _auth_header() -> dict:
    token = tokens.create_access_token(user_id="507f1f77bcf86cd799439011")
    return {"Authorization": f"Bearer {token}"}


@respx.mock
def test_upload_forwards_file_and_omits_auth_header():
    route = respx.post(f"{CV_API_URL}/api/uploads").mock(
        return_value=Response(201, json={"id": "abc123__clip.mp4", "name": "clip.mp4", "size": 1024})
    )
    client = _client()
    r = client.post(
        "/api/live-session/upload",
        headers=_auth_header(),
        files={"file": ("clip.mp4", b"fake-video-bytes", "video/mp4")},
    )
    assert r.status_code == 201
    assert r.json()["id"] == "abc123__clip.mp4"
    assert "Authorization" not in route.calls.last.request.headers


@respx.mock
def test_upload_sends_internal_auth_header(monkeypatch):
    monkeypatch.setattr(tamreena_client, "INTERNAL_SERVICE_TOKEN", "test-internal-token")
    route = respx.post(f"{CV_API_URL}/api/uploads").mock(
        return_value=Response(201, json={"id": "abc123__clip.mp4", "name": "clip.mp4", "size": 1024})
    )
    client = _client()
    client.post(
        "/api/live-session/upload",
        headers=_auth_header(),
        files={"file": ("clip.mp4", b"fake-video-bytes", "video/mp4")},
    )
    assert route.calls.last.request.headers["X-Internal-Auth"] == "test-internal-token"


def test_upload_rejects_missing_bff_token():
    client = _client()
    r = client.post("/api/live-session/upload", files={"file": ("clip.mp4", b"x", "video/mp4")})
    assert r.status_code in (401, 403)


def test_save_result_persists_and_returns_item(dynamo_table):
    client = _client()
    body = {"exercise_id": "biceps_curl", "exercise_name": "Biceps Curl", "reps": 8, "good": 6, "bad": 2}
    r = client.post("/api/live-session/result", json=body, headers=_auth_header())
    assert r.status_code == 200
    result = r.json()
    assert result["exercise_id"] == "biceps_curl"
    assert result["reps"] == 8
    assert len(result["session_id"]) == 24

    table = dynamo_table.Table(LIVE_SESSIONS_TABLE_NAME)
    stored = table.get_item(Key={"session_id": result["session_id"]}).get("Item")
    assert stored is not None
    assert stored["good"] == 6


def test_save_result_persists_cv_session_id_when_provided(dynamo_table):
    client = _client()
    body = {
        "exercise_id": "biceps_curl", "exercise_name": "Biceps Curl",
        "reps": 8, "good": 6, "bad": 2, "cv_session_id": "cv-abc123",
    }
    r = client.post("/api/live-session/result", json=body, headers=_auth_header())
    assert r.status_code == 200
    result = r.json()

    table = dynamo_table.Table(LIVE_SESSIONS_TABLE_NAME)
    stored = table.get_item(Key={"session_id": result["session_id"]}).get("Item")
    assert stored["cv_session_id"] == "cv-abc123"


def test_save_result_cv_session_id_defaults_to_none(dynamo_table):
    client = _client()
    body = {"exercise_id": "x", "exercise_name": "X", "reps": 0, "good": 0, "bad": 0}
    r = client.post("/api/live-session/result", json=body, headers=_auth_header())
    result = r.json()

    table = dynamo_table.Table(LIVE_SESSIONS_TABLE_NAME)
    stored = table.get_item(Key={"session_id": result["session_id"]}).get("Item")
    assert stored.get("cv_session_id") is None


def test_save_result_rejects_missing_bff_token():
    client = _client()
    body = {"exercise_id": "x", "exercise_name": "X", "reps": 0, "good": 0, "bad": 0}
    r = client.post("/api/live-session/result", json=body)
    assert r.status_code in (401, 403)


@respx.mock
def test_get_report_forwards_to_cv_sessions_endpoint(dynamo_table):
    record_ownership("abc123", "507f1f77bcf86cd799439011", "session")
    route = respx.get(f"{CV_API_URL}/api/sessions/abc123").mock(
        return_value=Response(200, json={
            "summary": {"total_reps": 8, "good_reps": 6, "bad_reps": 2, "score": 82},
            "history": [{"number": 1, "score": 90, "good": True}],
            "rules": [],
        })
    )
    client = _client()
    r = client.get("/api/live-session/report/abc123", headers=_auth_header())
    assert r.status_code == 200
    assert r.json()["summary"]["total_reps"] == 8
    assert route.called


@respx.mock
def test_get_report_passes_through_404_from_cv(dynamo_table):
    record_ownership("missing", "507f1f77bcf86cd799439011", "session")
    respx.get(f"{CV_API_URL}/api/sessions/missing").mock(
        return_value=Response(404, json={"detail": "Unknown session 'missing'"})
    )
    client = _client()
    r = client.get("/api/live-session/report/missing", headers=_auth_header())
    assert r.status_code == 404


def test_get_report_rejects_missing_bff_token():
    client = _client()
    r = client.get("/api/live-session/report/abc123")
    assert r.status_code in (401, 403)


@respx.mock
def test_get_report_rejects_session_owned_by_another_user(dynamo_table):
    record_ownership("abc123", "someone-elses-user-id", "session")
    route = respx.get(f"{CV_API_URL}/api/sessions/abc123").mock(
        return_value=Response(200, json={"summary": {}, "history": [], "rules": []})
    )
    client = _client()
    r = client.get("/api/live-session/report/abc123", headers=_auth_header())
    assert r.status_code == 404
    assert not route.called


def test_get_report_rejects_session_with_no_ownership_record(dynamo_table):
    client = _client()
    r = client.get("/api/live-session/report/never-recorded", headers=_auth_header())
    assert r.status_code == 404


@respx.mock
def test_upload_translates_upstream_401_to_503():
    respx.post(f"{CV_API_URL}/api/uploads").mock(
        return_value=Response(401, json={"detail": "Invalid or missing internal service credentials"})
    )
    client = _client()
    r = client.post(
        "/api/live-session/upload",
        headers=_auth_header(),
        files={"file": ("clip.mp4", b"fake-video-bytes", "video/mp4")},
    )
    assert r.status_code == 503
    assert "misconfigured" in r.json()["detail"].lower()

