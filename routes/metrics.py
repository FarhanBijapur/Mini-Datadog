from fastapi import APIRouter

from models.metric_model import MetricsResponse
from services.anomaly_detection import anomaly_detection_service
from services.metrics_service import metrics_service
from services.processing_engine import processing_engine

router = APIRouter(tags=["metrics"])


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Read observability metrics",
    description=(
        "Returns a real-time observability snapshot assembled from in-memory "
        "counters, rolling error windows, service-level frequency tracking, and "
        "the current anomaly detection state."
    ),
    responses={
        200: {
            "description": "Metrics snapshot returned successfully.",
            "content": {
                "application/json": {
                    "example": {
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
                }
            },
        }
    },
)
async def get_metrics() -> dict:
    # Real-time observability endpoints should serve pre-aggregated in-memory values.
    # Querying MongoDB per request adds latency and contention under load.
    metrics_snapshot = await metrics_service.snapshot()
    processing_snapshot = processing_engine.snapshot()
    anomaly_snapshot = anomaly_detection_service.snapshot()
    worker_status = "running" if metrics_snapshot.worker_running else "stopped"
    last_anomaly = anomaly_snapshot.get("last_detected_anomaly")

    return {
        "system_throughput": {
            "total_logs_received": metrics_snapshot.logs_received_total,
            "total_logs_processed": metrics_snapshot.logs_processed_total,
            "total_logs_failed": metrics_snapshot.logs_failed_total,
            "queue_rejections_total": metrics_snapshot.queue_rejections_total,
            "duplicate_logs_total": metrics_snapshot.duplicate_logs_total,
            "db_failures_total": metrics_snapshot.db_failures_total,
            "worker_restarts_total": metrics_snapshot.worker_restarts_total,
            "queue_depth": metrics_snapshot.queue_depth,
            "worker_status": worker_status,
        },
        "error_analytics": {
            "total_error_count": processing_snapshot["total_error_count"],
            "current_window_error_count": processing_snapshot["current_window_error_count"],
            "previous_window_error_count": processing_snapshot["previous_window_error_count"],
        },
        "service_level_insights": {
            "logs_per_service": metrics_snapshot.by_service,
            "error_count_per_service": processing_snapshot["error_count_per_service"],
        },
        "frequency_tracking": {
            "frequency_by_service_level": processing_snapshot["frequency_by_service_level"],
        },
        "anomaly_detection": {
            "last_anomaly": {
                "timestamp": last_anomaly["timestamp"] if last_anomaly else None,
                "current_count": last_anomaly["current_count"] if last_anomaly else 0,
                "previous_count": last_anomaly["previous_count"] if last_anomaly else 0,
                "affected_service": last_anomaly["affected_service"] if last_anomaly else None,
            },
            "anomaly_active": anomaly_snapshot["anomaly_active"],
        },
    }
