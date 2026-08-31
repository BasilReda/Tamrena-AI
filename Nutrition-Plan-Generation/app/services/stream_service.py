"""
Streaming service — manages per-run SSE event queues.

Each nutrition generation run gets its own async queue.
The graph nodes publish events; the SSE endpoint consumes them.
"""

import asyncio
import json
import time
from typing import AsyncGenerator
from app.schemas.response import StreamEvent
from app.core.logging import get_logger

logger = get_logger(__name__)

# Node name → progress percentage mapping
NODE_PROGRESS: dict[str, int] = {
    "profile": 10,
    "calories": 22,
    "macros": 34,
    "retrieve_foods": 50,
    "compose_meal": 68,
    "validate": 80,
    "increment_retry": 82,
    "explain": 95,
}


class StreamService:
    """
    Manages per-run async queues for SSE streaming.
    Thread-safe via asyncio.Queue.
    """

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue] = {}
        self._start_times: dict[str, dict[str, float]] = {}

    def create_run(self, run_id: str) -> None:
        self._queues[run_id] = asyncio.Queue()
        self._start_times[run_id] = {}
        logger.debug("Stream queue created for run_id=%s", run_id)

    async def publish(self, run_id: str, event: StreamEvent) -> None:
        q = self._queues.get(run_id)
        if q:
            await q.put(event)

    async def publish_node_start(self, run_id: str, node: str) -> None:
        self._start_times.setdefault(run_id, {})[node] = time.monotonic()
        event = StreamEvent(
            run_id=run_id,
            node=node,
            status="started",
            progress=NODE_PROGRESS.get(node, 50),
            message=f"{node.replace('_', ' ').title()} started",
        )
        await self.publish(run_id, event)

    async def publish_node_complete(self, run_id: str, node: str) -> None:
        start = self._start_times.get(run_id, {}).get(node)
        duration_ms = int((time.monotonic() - start) * 1000) if start else None
        event = StreamEvent(
            run_id=run_id,
            node=node,
            status="completed",
            progress=NODE_PROGRESS.get(node, 50),
            message=f"{node.replace('_', ' ').title()} completed",
            duration_ms=duration_ms,
        )
        await self.publish(run_id, event)

    async def publish_node_error(self, run_id: str, node: str, reason: str) -> None:
        event = StreamEvent(
            run_id=run_id,
            node=node,
            status="failed",
            progress=NODE_PROGRESS.get(node, 50),
            reason=reason,
        )
        await self.publish(run_id, event)

    async def publish_finished(self, run_id: str) -> None:
        event = StreamEvent(
            run_id=run_id,
            node="workflow",
            status="completed",
            progress=100,
            message="Nutrition plan generation complete",
        )
        await self.publish(run_id, event)
        # Sentinel to signal end of stream
        await self._queues[run_id].put(None)

    async def stream_events(self, run_id: str) -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted strings.
        Terminates when it receives the None sentinel.
        """
        q = self._queues.get(run_id)
        if q is None:
            yield f"data: {json.dumps({'error': 'run_id not found'})}\n\n"
            return

        try:
            while True:
                event = await asyncio.wait_for(q.get(), timeout=120.0)
                if event is None:
                    break
                yield f"data: {event.model_dump_json()}\n\n"
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'error': 'stream timeout'})}\n\n"
        finally:
            self._queues.pop(run_id, None)
            self._start_times.pop(run_id, None)

    def cleanup_run(self, run_id: str) -> None:
        self._queues.pop(run_id, None)
        self._start_times.pop(run_id, None)


# Module-level singleton
stream_service = StreamService()
