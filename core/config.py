import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Mini Datadog"
    environment: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "mini_datadog"
    mongodb_logs_collection: str = "logs"
    ingestion_queue_max_size: int = int(os.getenv("INGESTION_QUEUE_MAX_SIZE", "10000"))
    worker_batch_size: int = 20
    worker_poll_timeout_seconds: float = 0.2
    worker_max_retries: int = 2
    worker_restart_delay_seconds: float = 1.0
    dedupe_cache_size: int = 2000
    dedupe_ttl_seconds: int = 90
    dedupe_mode: str = "skip"


settings = Settings()
