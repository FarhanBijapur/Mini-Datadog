from fastapi import APIRouter

from services.anomaly_detection import anomaly_detection_service
from services.metrics_service import metrics_service
from services.processing_engine import processing_engine

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
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
