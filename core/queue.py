import asyncio
from queue import Empty, Full, Queue

from core.config import settings


class IngestionQueue:
    """
    Bounded queue to absorb short traffic spikes and protect the worker.
    Backpressure (full queue) is preferred over memory growth under load.
    We use `queue.Queue` because it is globally shareable and thread-safe by design.
    """

    def __init__(self) -> None:
        self._queue: Queue[dict] = Queue(maxsize=settings.ingestion_queue_max_size)

    async def put(self, item: dict) -> None:
        try:
            self._queue.put_nowait(item)
        except Full as exc:
            raise OverflowError("Ingestion queue is full") from exc

    async def get(self) -> dict:
        # queue.get() is blocking, so run it in a worker thread to keep event loop free.
        return await asyncio.to_thread(self._queue.get)

    async def get_with_timeout(self, timeout_seconds: float) -> dict | None:
        """
        Timed poll avoids busy-looping while still waking up quickly for shutdown.
        """
        try:
            return await asyncio.to_thread(self._queue.get, True, timeout_seconds)
        except Empty:
            return None

    def get_nowait(self) -> dict | None:
        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()

    def is_full(self) -> bool:
        return self._queue.full()


ingestion_queue = IngestionQueue()
