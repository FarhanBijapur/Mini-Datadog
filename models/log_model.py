from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class LogIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
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
            ]
        }
    )

    source: str = Field(default="unknown", examples=["checkout-service"])
    service: str = Field(..., examples=["payments"])
    level: str = Field(
        ...,
        examples=["INFO", "ERROR", "WARN"],
        json_schema_extra={"enum": ["DEBUG", "INFO", "WARN", "ERROR"]},
    )
    message: str
    timestamp: datetime | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    trace_id: str | None = None
    span_id: str | None = None


class ProcessedLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    service: str
    level: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    trace_id: str | None = None
    span_id: str | None = None
    received_at: datetime
    processed_at: datetime


class WorkerStatus(str, Enum):
    running = "running"
    stopped = "stopped"


class LogAcceptedResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "accepted",
                    "queue_depth": 1,
                }
            ]
        }
    )

    status: str = Field(examples=["accepted"])
    queue_depth: int = Field(ge=0, examples=[1])


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "Ingestion queue is full. Retry later.",
                }
            ]
        }
    )

    detail: str


class StoredLog(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "timestamp": "2026-07-10T12:00:00+00:00",
                    "service": "checkout-api",
                    "level": "ERROR",
                    "message": "payment authorization failed",
                    "source": "demo-generator",
                    "received_at": "2026-07-10T12:00:01+00:00",
                    "processed_at": "2026-07-10T12:00:02+00:00",
                    "attributes": {"region": "ap-south-1", "latency_ms": 420},
                    "tags": ["demo", "local"],
                    "trace_id": "trace-123",
                    "span_id": "span-456",
                }
            ]
        },
    )

    timestamp: str = Field(json_schema_extra={"format": "date-time"})
    service: str
    level: str = Field(json_schema_extra={"enum": ["DEBUG", "INFO", "WARN", "ERROR"]})
    message: str
    source: str
    received_at: str = Field(json_schema_extra={"format": "date-time"})
    processed_at: str = Field(json_schema_extra={"format": "date-time"})
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    trace_id: str | None = None
    span_id: str | None = None


class RecentLogsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "logs": [
                        {
                            "timestamp": "2026-07-10T12:00:00+00:00",
                            "service": "checkout-api",
                            "level": "ERROR",
                            "message": "payment authorization failed",
                            "source": "demo-generator",
                            "received_at": "2026-07-10T12:00:01+00:00",
                            "processed_at": "2026-07-10T12:00:02+00:00",
                            "attributes": {"region": "ap-south-1", "latency_ms": 420},
                            "tags": ["demo", "local"],
                            "trace_id": "trace-123",
                            "span_id": "span-456",
                        }
                    ]
                }
            ]
        }
    )

    logs: list[StoredLog]
