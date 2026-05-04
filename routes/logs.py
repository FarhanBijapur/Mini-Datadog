from fastapi import APIRouter, HTTPException, Query, status
import logging

from core.queue import ingestion_queue
from models.log_model import LogIn
from services.metrics_service import metrics_service
from services.storage_service import storage_service
from utils.time_utils import utc_now

router = APIRouter(tags=["logs"])
logger = logging.getLogger(__name__)


@router.get("/logs")
async def recent_logs(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    logs = await storage_service.read_recent_logs(limit=limit)
    return {"logs": logs}


@router.post("/logs", status_code=status.HTTP_202_ACCEPTED)
async def ingest_log(payload: LogIn) -> dict:
    if ingestion_queue.is_full():
        # Explicit overload signal lets clients apply retries/backoff upstream.
        await metrics_service.mark_queue_rejected()
        logger.warning(
            "queue_overflow",
            extra={"event": "queue_overflow", "endpoint": "/logs", "action": "reject_429"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Ingestion queue is full. Retry later.",
        )

    # Add ingest timestamp at the API boundary so queue items are self-contained.
    event = payload.model_dump(mode="json")
    if event.get("timestamp") is None:
        event["timestamp"] = utc_now().isoformat()

    try:
        await ingestion_queue.put(event)
    except OverflowError:
        await metrics_service.mark_queue_rejected()
        logger.warning(
            "queue_overflow",
            extra={"event": "queue_overflow", "endpoint": "/logs", "action": "reject_429"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Ingestion queue is full. Retry later.",
        ) from None

    await metrics_service.mark_received()

    return {
        "status": "accepted",
        "queue_depth": ingestion_queue.qsize(),
    }
