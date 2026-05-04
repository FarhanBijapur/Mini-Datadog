from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class LogIn(BaseModel):
    source: str = Field(default="unknown", examples=["checkout-service"])
    service: str = Field(..., examples=["payments"])
    level: str = Field(..., examples=["INFO", "ERROR", "WARN"])
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
