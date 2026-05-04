from pydantic import BaseModel


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
