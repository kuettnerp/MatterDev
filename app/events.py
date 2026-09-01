"""In-memory pub/sub for pushing camera events (e.g. motion) to connected browsers via SSE.

Single-process only - matches this app's deployment (one uvicorn worker on the Pi).
"""

import asyncio


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    async def publish(self, event: dict) -> None:
        for queue in list(self._subscribers):
            await queue.put(event)


broker = EventBroker()
