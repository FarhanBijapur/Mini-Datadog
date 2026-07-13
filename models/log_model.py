from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


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
    level: LogLevel = Field(
        ...,
        examples=["INFO", "ERROR", "WARN"],
    )
    message: str
    timestamp: datetime | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def _reject_numeric_timestamp(cls, v: Any) -> Any:
        if isinstance(v, (int, float)):
            raise ValueError("numeric timestamps are not accepted; use ISO-8601 strings")
        return v

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


class ValidationErrorItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = Field(examples=["missing"])
    loc: list[str | int] = Field(examples=[["body", "tags", 0]])
    msg: str = Field(examples=["Field required"])
    input: Any = Field(default=None)


class ValidationErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
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
            ]
        }
    )

    detail: list[ValidationErrorItem]


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
