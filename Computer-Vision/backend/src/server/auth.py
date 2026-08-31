"""Shared-secret gate for this service's HTTP API.

Computer-Vision has no user-level auth of its own — it's only meant to be
called by the tamreena-web BFF, which authenticates real end users. This
is the only thing stopping anyone who can reach this service's port from
listing/reading/deleting every user's sessions and uploads directly (see
routes/sessions.py, routes/uploads.py).

The WebSocket route (/ws/live) checks the same header itself rather than
using this as a FastAPI dependency — HTTPException handling for a
dependency that runs before websocket.accept() isn't guaranteed to reach
the client cleanly across ASGI servers, whereas the explicit
accept-then-send-error-then-close pattern already used throughout
routes/live.py for its other validation failures is unambiguous.
"""

import hmac

from fastapi import Header, HTTPException

from ..config import settings


def require_internal_auth(x_internal_auth: str = Header(default="")) -> None:
    """hmac.compare_digest avoids leaking the token's length/prefix via
    timing. An unset configured token rejects everything (fail closed)
    rather than letting every request through."""
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        x_internal_auth, settings.INTERNAL_SERVICE_TOKEN
    ):
        raise HTTPException(status_code=401, detail="Missing or invalid internal service credentials.")


def internal_auth_ok(token: str) -> bool:
    """Same check, usable from contexts (like the WebSocket handler) that
    handle their own failure response instead of raising HTTPException."""
    return bool(settings.INTERNAL_SERVICE_TOKEN) and hmac.compare_digest(token, settings.INTERNAL_SERVICE_TOKEN)
