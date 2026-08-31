import httpx
import pytest

from app.tamreena_client import proxy_json


def _resp(status_code: int, json_body: dict) -> httpx.Response:
    return httpx.Response(status_code, json=json_body, request=httpx.Request("GET", "http://upstream/x"))


def test_internal_auth_401_is_translated_to_503():
    resp = proxy_json(_resp(401, {"detail": "Invalid or missing internal service credentials"}), internal_auth=True)
    assert resp.status_code == 503


def test_non_internal_auth_401_passes_through_unchanged():
    # Workout proxy calls forward the user's own token; a 401 there is real
    # and must reach the client as-is.
    resp = proxy_json(_resp(401, {"detail": "token expired"}), internal_auth=False)
    assert resp.status_code == 401


def test_non_401_status_codes_pass_through_unchanged_regardless_of_internal_auth():
    resp = proxy_json(_resp(404, {"detail": "not found"}), internal_auth=True)
    assert resp.status_code == 404
