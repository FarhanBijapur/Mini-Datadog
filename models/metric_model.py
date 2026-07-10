from pydantic import BaseModel, ConfigDict, Field

from models.log_model import WorkerStatus


class MetricsSnapshot(BaseModel):
    logs_received_total: int
    logs_processed_total: int
    logs_failed_total: int
    queue_rejections_total: int
    duplicate_logs_total: int
    db_failures_total: int
    worker_restarts_total: int
    queue_depth: int
    worker_running: bool
    by_level: dict[str, int]
    by_service: dict[str, int]


class SystemThroughputResponse(BaseModel):
    total_logs_received: int = Field(ge=0, examples=[120])
    total_logs_processed: int = Field(ge=0, examples=[118])
    total_logs_failed: int = Field(ge=0, examples=[1])
    queue_rejections_total: int = Field(ge=0, examples=[0])
    duplicate_logs_total: int = Field(ge=0, examples=[2])
    db_failures_total: int = Field(ge=0, examples=[0])
    worker_restarts_total: int = Field(ge=0, examples=[0])
    queue_depth: int = Field(ge=0, examples=[3])
    worker_status: WorkerStatus = Field(examples=["running"])


class ErrorAnalyticsResponse(BaseModel):
    total_error_count: int = Field(ge=0, examples=[14])
    current_window_error_count: int = Field(ge=0, examples=[8])
    previous_window_error_count: int = Field(ge=0, examples=[3])


class ServiceLevelInsightsResponse(BaseModel):
    logs_per_service: dict[str, int] = Field(
        examples=[{"checkout-api": 48, "payment-worker": 31}]
    )
    error_count_per_service: dict[str, int] = Field(
        examples=[{"checkout-api": 9, "payment-worker": 5}]
    )


class FrequencyTrackingResponse(BaseModel):
    frequency_by_service_level: dict[str, int] = Field(
        examples=[{"checkout-api:ERROR": 9, "checkout-api:INFO": 39}]
    )


class LastAnomalyResponse(BaseModel):
    timestamp: str | None = Field(
        default=None,
        examples=["2026-07-10T12:00:30+00:00"],
        json_schema_extra={"format": "date-time"},
    )
    current_count: int = Field(ge=0, examples=[8])
    previous_count: int = Field(ge=0, examples=[3])
    affected_service: str | None = Field(default=None, examples=["checkout-api"])


class AnomalyDetectionResponse(BaseModel):
    last_anomaly: LastAnomalyResponse
    anomaly_active: bool = Field(examples=[True])


class MetricsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "system_throughput": {
                        "total_logs_received": 120,
                        "total_logs_processed": 118,
                        "total_logs_failed": 1,
                        "queue_rejections_total": 0,
                        "duplicate_logs_total": 2,
                        "db_failures_total": 0,
                        "worker_restarts_total": 0,
                        "queue_depth": 3,
                        "worker_status": "running",
                    },
                    "error_analytics": {
                        "total_error_count": 14,
                        "current_window_error_count": 8,
                        "previous_window_error_count": 3,
                    },
                    "service_level_insights": {
                        "logs_per_service": {
                            "checkout-api": 48,
                            "payment-worker": 31,
                        },
                        "error_count_per_service": {
                            "checkout-api": 9,
                            "payment-worker": 5,
                        },
                    },
                    "frequency_tracking": {
                        "frequency_by_service_level": {
                            "checkout-api:ERROR": 9,
                            "checkout-api:INFO": 39,
                        }
                    },
                    "anomaly_detection": {
                        "last_anomaly": {
                            "timestamp": "2026-07-10T12:00:30+00:00",
                            "current_count": 8,
                            "previous_count": 3,
                            "affected_service": "checkout-api",
                        },
                        "anomaly_active": True,
                    },
                }
            ]
        }
    )

    system_throughput: SystemThroughputResponse
    error_analytics: ErrorAnalyticsResponse
    service_level_insights: ServiceLevelInsightsResponse
    frequency_tracking: FrequencyTrackingResponse
    anomaly_detection: AnomalyDetectionResponse
