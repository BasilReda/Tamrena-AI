"""
Shared HTTP-proxy helpers for forwarding requests to Tamreena_AI's API
(WORKOUT_API_URL), the Computer-Vision service's API (CV_API_URL), and the
AWS Nutrition Agent (NUTRITION_API_URL).
"""

from typing import Optional
import httpx
from fastapi.responses import JSONResponse

from app.config import CV_API_URL, INTERNAL_SERVICE_TOKEN, NUTRITION_API_URL, WORKOUT_API_URL

LLM_TIMEOUT = 3600.0

# Computer-Vision and Nutrition-Plan-Generation have no user-level auth of
# their own — every call to either one carries the shared internal-service
# secret instead (see app/config.py's INTERNAL_SERVICE_TOKEN). Tamreena_AI
# (WORKOUT_API_URL) is not in this set: it authenticates via the caller's
# own forwarded Bearer token.
_INTERNAL_AUTH_BASE_URLS = {CV_API_URL, NUTRITION_API_URL}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def call_upstream(
    method: str,
    path: str,
    *,
    token: Optional[str] = None,
    base_url: str = WORKOUT_API_URL,
    timeout: float = 3600.0,
    **kwargs,
) -> Optional[httpx.Response]:
    """Make a request to an upstream service. Returns None if host is unreachable (dev/offline fallback)."""
    headers = auth_header(token) if token is not None else {}
    if base_url in _INTERNAL_AUTH_BASE_URLS:
        headers["X-Internal-Auth"] = INTERNAL_SERVICE_TOKEN
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            return await client.request(method, path, headers=headers, **kwargs)
    except httpx.HTTPError:
        return None


def proxy_json(response: Optional[httpx.Response], *, internal_auth: bool = False) -> JSONResponse:
    if response is None:
        return JSONResponse(status_code=502, content={"detail": "Upstream service unavailable"})
    if internal_auth and response.status_code == 401:
        # This upstream has no user-level auth of its own (see module
        # docstring) — a 401 here can only mean our own X-Internal-Auth
        # secret is missing/wrong, never that the caller's session is
        # invalid. Forwarding it as a bare 401 gets misread by the
        # frontend's global authFetch as "log this user out."
        return JSONResponse(
            status_code=503,
            content={"detail": "Upstream service is misconfigured (internal auth rejected). Not a session issue."},
        )
    try:
        content = response.json()
    except ValueError:
        content = {"detail": response.text}
    return JSONResponse(status_code=response.status_code, content=content)

