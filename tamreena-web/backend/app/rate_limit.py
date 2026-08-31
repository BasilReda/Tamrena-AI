"""
Minimal in-memory sliding-window rate limiter — this process is the only
place with real per-user identity for calls to Tamrena-Workout's coach
chat and Nutrition-Plan-Generation's plan generation, both of which have
no rate limiting of their own (see Full-Project/OWASP-Security-Review.md
§6). In-memory and per-process by design, matching this codebase's
existing state-management style elsewhere (e.g. Computer-Vision's
in-memory session lock) — if this service ever runs multiple replicas,
this needs to move to a shared store (Redis) instead.
"""

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        """Records this attempt and returns whether it's within the limit."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self._window_seconds:
                hits.popleft()
            if len(hits) >= self._max_requests:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


coach_chat_limiter = RateLimiter(max_requests=10, window_seconds=60)
nutrition_generate_limiter = RateLimiter(max_requests=3, window_seconds=300)
