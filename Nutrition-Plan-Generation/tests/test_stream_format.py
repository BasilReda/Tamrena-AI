"""
Regression test for the nutrition SSE stream's wire format.

GET /api/v1/nutrition/stream/{run_id} used to wrap stream_service's
already-SSE-formatted output ("data: {...}\n\n" per event, see
StreamService.stream_events) in sse_starlette's EventSourceResponse, which
ALSO prefixes each yielded chunk with its own "data: " -- doubling the
prefix into "data: data: {...}". No SSE client can parse that: confirmed
live in the browser as a JSON.parse SyntaxError
("Unexpected token 'd', "data: {"ru"... is not valid JSON") on every single
event, which the frontend's EventSource.onerror handler then reported as
"Lost connection while generating your nutrition plan." even though the
backend pipeline had completed successfully.
"""

import asyncio
import json

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.stream_service import stream_service

_TEST_TOKEN = "test-internal-service-token"


def test_stream_endpoint_yields_singly_prefixed_valid_json_events(monkeypatch):
    monkeypatch.setattr(settings, "internal_service_token", _TEST_TOKEN)

    run_id = "test-stream-format-run"
    stream_service.create_run(run_id)

    # Publish before opening the stream so both events are already queued —
    # no dependency on a real graph run or background-task timing.
    asyncio.run(stream_service.publish_node_start(run_id, "profile"))
    asyncio.run(stream_service.publish_finished(run_id))

    with TestClient(app) as client:
        with client.stream(
            "GET", f"/api/v1/nutrition/stream/{run_id}", headers={"X-Internal-Auth": _TEST_TOKEN}
        ) as response:
            assert response.status_code == 200
            body = b"".join(response.iter_bytes()).decode()

    events = [chunk for chunk in body.split("\n\n") if chunk.strip()]
    assert len(events) == 2

    for raw_event in events:
        assert raw_event.startswith("data: ")
        assert not raw_event.startswith("data: data:")
        payload = raw_event[len("data: "):]
        parsed = json.loads(payload)  # must not raise SyntaxError/JSONDecodeError
        assert parsed["run_id"] == run_id

    assert json.loads(events[0][len("data: "):])["node"] == "profile"
    assert json.loads(events[1][len("data: "):])["node"] == "workflow"
    assert json.loads(events[1][len("data: "):])["status"] == "completed"
