import asyncio
import logging

from core.config import settings
from core.queue import ingestion_queue
from models.log_model import LogIn, ProcessedLog
from services.anomaly_detection import anomaly_detection_service
from services.dedupe_service import dedupe_service
from services.metrics_service import metrics_service
from services.processing_engine import processing_engine
from services.storage_service import storage_service

logger = logging.getLogger(__name__)


class LogWorker:
    """
    Dedicated background worker isolates heavy operations from request handling.
    This keeps ingestion latency stable and makes overload behavior predictable.
    """

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._batch_size = max(1, min(50, settings.worker_batch_size))
        self._poll_timeout = max(0.05, settings.worker_poll_timeout_seconds)
        self._max_retries = max(0, settings.worker_max_retries)
        self._restart_delay = max(0.2, settings.worker_restart_delay_seconds)
        self._dedupe_mode = settings.dedupe_mode.lower().strip()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        await metrics_service.set_worker_running(True)
        logger.info("Log worker started (batch_size=%s)", self._batch_size)
        self._task = asyncio.create_task(self._supervise(), name="log-worker-supervisor")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            # Stop signal is cooperative: worker wakes on timeout and drains remaining logs.
            await self._task
            self._task = None
        await metrics_service.set_worker_running(False)
        logger.info("Log worker stopped")

    async def _supervise(self) -> None:
        while not self._stop_event.is_set() or ingestion_queue.qsize() > 0:
            try:
                await self._run_once()
                break
            except Exception:
                # Failure isolation: API ingestion continues while worker is restarted in background.
                logger.exception("Worker loop crashed; restarting after delay")
                await metrics_service.mark_worker_restarted()
                if self._stop_event.is_set():
                    break
                await asyncio.sleep(self._restart_delay)

    async def _run_once(self) -> None:
        """
        Queue + worker keeps API ingestion non-blocking and resilient under bursts:
        requests enqueue quickly, then background workers handle CPU/IO heavy work.
        Failures are isolated here, away from request handlers, so ingestion remains responsive.
        """
        while not self._stop_event.is_set() or ingestion_queue.qsize() > 0:
            batch = await self._dequeue_batch()
            if not batch:
                continue
            await self._process_batch(batch)

    async def _dequeue_batch(self) -> list[dict]:
        first = await ingestion_queue.get_with_timeout(self._poll_timeout)
        if first is None:
            return []

        batch = [first]
        while len(batch) < self._batch_size:
            item = ingestion_queue.get_nowait()
            if item is None:
                break
            batch.append(item)
        return batch

    async def _process_batch(self, batch: list[dict]) -> None:
        processed_items: list[tuple[ProcessedLog, dict]] = []
        processed_metric_pairs: list[tuple[str, str]] = []
        failed_count = 0
        consumed = 0
        error_services_in_batch: dict[str, int] = {}

        try:
            for payload_dict in batch:
                consumed += 1
                try:
                    if dedupe_service.is_duplicate(payload_dict):
                        await metrics_service.mark_duplicate()
                        if self._dedupe_mode == "skip":
                            continue
                        payload_dict["_is_duplicate"] = True

                    log_payload = LogIn.model_validate(payload_dict)
                    processed = processing_engine.process(log_payload)
                    processed_items.append((processed, payload_dict))
                    processed_metric_pairs.append((processed.level, processed.service))
                    if processed.level == "ERROR":
                        error_services_in_batch[processed.service] = (
                            error_services_in_batch.get(processed.service, 0) + 1
                        )
                except Exception:
                    # Skip malformed payload after optional retries to keep pipeline flowing.
                    requeued = await self._retry_or_skip(payload_dict)
                    if not requeued:
                        failed_count += 1

            if processed_items:
                try:
                    # Batching improves DB write throughput by reducing insert round-trips.
                    await storage_service.write_logs_batch(
                        [item[0] for item in processed_items]
                    )
                    await metrics_service.mark_processed_batch(processed_metric_pairs)
                except Exception:
                    logger.exception("Batch DB write failed; falling back to per-log writes")
                    await metrics_service.mark_db_failure()
                    for log, source_payload in processed_items:
                        try:
                            await storage_service.write_log(log)
                            await metrics_service.mark_processed(log.level, log.service)
                        except Exception:
                            await metrics_service.mark_db_failure()
                            # Requeue original event so retry counters and input fidelity are preserved.
                            requeued = await self._retry_or_skip(source_payload)
                            if not requeued:
                                failed_count += 1
        finally:
            for _ in range(consumed):
                ingestion_queue.task_done()
            if failed_count:
                await metrics_service.mark_failed(failed_count)
            if processed_items:
                affected_service = None
                if error_services_in_batch:
                    affected_service = max(
                        error_services_in_batch,
                        key=error_services_in_batch.get,
                    )
                # Runs in worker path, so ingestion API remains non-blocking.
                anomaly_detection_service.evaluate(affected_service=affected_service)
            logger.info(
                "Worker batch processed: size=%s success=%s failed=%s",
                consumed,
                max(0, consumed - failed_count),
                failed_count,
            )

    async def _retry_or_skip(self, payload: dict) -> bool:
        retries = int(payload.get("_retries", 0))
        if retries >= self._max_retries:
            logger.error("Skipping log after retries exhausted")
            return False
        payload["_retries"] = retries + 1
        try:
            await ingestion_queue.put(payload)
            return True
        except OverflowError:
            logger.error("Retry dropped because ingestion queue is full")
            return False


log_worker = LogWorker()
