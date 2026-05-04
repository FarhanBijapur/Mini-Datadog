import asyncio
from collections import Counter

from core.queue import ingestion_queue
from models.metric_model import MetricsSnapshot


class MetricsService:
    """
    In-memory counters are cheap and fast for high-ingestion control-plane metrics.
    They are intentionally decoupled from storage to avoid read/write amplification.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._logs_received_total = 0
        self._logs_processed_total = 0
        self._logs_failed_total = 0
        self._queue_rejections_total = 0
        self._duplicate_logs_total = 0
        self._db_failures_total = 0
        self._worker_restarts_total = 0
        self._by_level = Counter()
        self._by_service = Counter()
        self._worker_running = False

    async def mark_received(self) -> None:
        async with self._lock:
            self._logs_received_total += 1

    async def mark_processed(self, level: str, service: str) -> None:
        async with self._lock:
            self._logs_processed_total += 1
            self._by_level[level] += 1
            self._by_service[service] += 1

    async def mark_processed_batch(self, logs: list[tuple[str, str]]) -> None:
        if not logs:
            return
        async with self._lock:
            self._logs_processed_total += len(logs)
            for level, service in logs:
                self._by_level[level] += 1
                self._by_service[service] += 1

    async def mark_failed(self, count: int = 1) -> None:
        async with self._lock:
            self._logs_failed_total += count

    async def mark_queue_rejected(self, count: int = 1) -> None:
        async with self._lock:
            self._queue_rejections_total += count

    async def mark_duplicate(self, count: int = 1) -> None:
        async with self._lock:
            self._duplicate_logs_total += count

    async def mark_db_failure(self, count: int = 1) -> None:
        async with self._lock:
            self._db_failures_total += count

    async def mark_worker_restarted(self, count: int = 1) -> None:
        async with self._lock:
            self._worker_restarts_total += count

    async def set_worker_running(self, running: bool) -> None:
        async with self._lock:
            self._worker_running = running

    async def snapshot(self) -> MetricsSnapshot:
        async with self._lock:
            return MetricsSnapshot(
                logs_received_total=self._logs_received_total,
                logs_processed_total=self._logs_processed_total,
                logs_failed_total=self._logs_failed_total,
                queue_rejections_total=self._queue_rejections_total,
                duplicate_logs_total=self._duplicate_logs_total,
                db_failures_total=self._db_failures_total,
                worker_restarts_total=self._worker_restarts_total,
                queue_depth=ingestion_queue.qsize(),
                worker_running=self._worker_running,
                by_level=dict(self._by_level),
                by_service=dict(self._by_service),
            )


metrics_service = MetricsService()
