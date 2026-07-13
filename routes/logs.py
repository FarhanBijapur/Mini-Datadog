from fastapi import APIRouter, Body, HTTPException, Query, status
import logging

from core.queue import ingestion_queue
from models.log_model import ErrorResponse, LogAcceptedResponse, LogIn, RecentLogsResponse, ValidationErrorResponse
from services.metrics_service import metrics_service
from services.storage_service import storage_service
from utils.time_utils import utc_now

router = APIRouter(tags=["logs"])
logger = logging.getLogger(__name__)


@router.get(
    "/logs",
    response_model=RecentLogsResponse,
    summary="Read recent logs",
    description=(
        "Returns the most recently processed logs from MongoDB. The response is "
        "ordered by processing time descending and wrapped in a `logs` array."
    ),
    responses={
        200: {
            "description": "Recent logs returned successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "logs": [
                            {
                                "timestamp": "2026-07-10T12:00:00+00:00",
                                "service": "checkout-api",
                                "level": "ERROR",
                                "message": "payment authorization failed",
                                "source": "demo-generator",
                                "received_at": "2026-07-10T12:00:01+00:00",
                                "processed_at": "2026-07-10T12:00:02+00:00",
                                "attributes": {
                                    "region": "ap-south-1",
                                    "latency_ms": 420,
                                },
                                "tags": ["demo", "local"],
                                "trace_id": "trace-123",
                                "span_id": "span-456",
                            }
                        ]
                    }
                }
            },
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "The `limit` query parameter failed validation.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "greater_than_equal",
                                "loc": ["query", "limit"],
                                "msg": "Input should be greater than or equal to 1",
                                "input": "0",
                                "ctx": {"ge": 1},
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def recent_logs(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    logs = await storage_service.read_recent_logs(limit=limit)
    return {"logs": logs}


@router.post(
    "/logs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=LogAcceptedResponse,
    summary="Ingest a log event",
    description=(
        "Validates a log event and enqueues it for asynchronous processing. "
        "A `202 Accepted` response means the event was accepted into the in-memory "
        "ingestion queue, not necessarily persisted yet."
    ),
    responses={
        202: {
            "description": "Log event accepted into the ingestion queue.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "accepted",
                        "queue_depth": 1,
                    }
                }
            },
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "The request body failed FastAPI/Pydantic validation.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "missing",
                                "loc": ["body", "service"],
                                "msg": "Field required",
                                "input": {
                                    "level": "ERROR",
                                    "message": "payment authorization failed",
                                },
                            }
                        ]
                    }
                }
            },
        },
        429: {
            "model": ErrorResponse,
            "description": "The ingestion queue is full and the client should retry later.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ingestion queue is full. Retry later.",
                    }
                }
            },
        },
    },
)
async def ingest_log(
    payload: LogIn = Body(
        ...,
        examples=[
            {
                "source": "demo-generator",
                "service": "checkout-api",
                "level": "ERROR",
                "message": "payment authorization failed",
                "timestamp": "2026-07-10T12:00:00+00:00",
                "attributes": {"region": "ap-south-1", "latency_ms": 420},
                "tags": ["demo", "local"],
                "trace_id": "trace-123",
                "span_id": "span-456",
            }
        ],
    )
) -> dict:
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
