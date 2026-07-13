import asyncio
from typing import Any

from pymongo import DESCENDING
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    ExecutionTimeout,
    NetworkTimeout,
    ServerSelectionTimeoutError,
)

from core.config import settings
from core.database import mongo_manager
from models.log_model import LogLevel, ProcessedLog


class LogStorageService:
    """
    Wraps persistence behind a service boundary. This keeps routes/workers independent
    from specific database access details and enables future storage fan-out.
    """

    def _build_document(self, log: ProcessedLog) -> dict[str, Any]:
        document = log.model_dump(mode="json")
        # Keep a predictable, query-friendly shape for core log attributes.
        return {
            "timestamp": document["timestamp"],
            "service": document["service"],
            "level": document["level"],
            "message": document["message"],
            "source": document["source"],
            "received_at": document["received_at"],
            "processed_at": document["processed_at"],
            "attributes": document["attributes"],
            "tags": document["tags"],
            "trace_id": document["trace_id"],
            "span_id": document["span_id"],
        }

    async def _with_retry(self, operation):
        max_attempts = max(1, settings.worker_max_retries + 1)
        backoff_seconds = 0.05
        for attempt in range(1, max_attempts + 1):
            try:
                return await asyncio.to_thread(operation)
            except (
                AutoReconnect,
                ConnectionFailure,
                NetworkTimeout,
                ServerSelectionTimeoutError,
                ExecutionTimeout,
            ):
                # Retries with backoff reduce pressure on a degraded DB and increase
                # chances of recovery for transient network/replica-election failures.
                if attempt >= max_attempts:
                    raise
                await asyncio.sleep(backoff_seconds * attempt)

    async def write_log(self, log: ProcessedLog) -> str:
        document = self._build_document(log)
        result = await self._with_retry(
            lambda: mongo_manager.logs_collection.insert_one(document)
        )
        return str(result.inserted_id)

    async def write_logs_batch(self, logs: list[ProcessedLog]) -> int:
        if not logs:
            return 0
        documents = [self._build_document(log) for log in logs]
        # Batch insert amortizes network/driver overhead across many events.
        result = await self._with_retry(
            lambda: mongo_manager.logs_collection.insert_many(documents, ordered=False)
        )
        return len(result.inserted_ids)

    async def read_recent_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = min(max(limit, 1), 200)
        valid_levels = [level.value for level in LogLevel]

        def operation() -> list[dict[str, Any]]:
            cursor = (
                mongo_manager.logs_collection.find(
                    {"level": {"$in": valid_levels}},
                    {"_id": 0},
                )
                .sort("processed_at", DESCENDING)
                .limit(safe_limit)
            )
            return list(cursor)

        return await self._with_retry(operation)


storage_service = LogStorageService()
