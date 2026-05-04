from datetime import datetime, timedelta
from threading import Lock

from services.processing_engine import processing_engine
from utils.time_utils import utc_now


class AnomalyDetectionService:
    """
    Dynamic (relative) thresholding adapts to baseline traffic changes better than
    a static threshold, which can under-alert on busy systems and over-alert on quiet ones.

    Limitations:
    - Can raise false positives during short-lived traffic spikes.
    - Not seasonality-aware (e.g., known hourly/daily peaks).

    Future improvements:
    - Statistical methods: moving average, EWMA, z-score based detection.
    - ML methods: supervised/unsupervised anomaly models over richer features.
    """

    def __init__(self, cooldown_seconds: int = 120) -> None:
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._last_alert_at: datetime | None = None
        self._last_signature: tuple[int, int] | None = None
        self._last_anomaly: dict | None = None
        self._anomaly_active = False
        self._lock = Lock()

    def evaluate(self, affected_service: str | None = None) -> None:
        stats = processing_engine.snapshot()
        current_count = int(stats["current_window_error_count"])
        previous_count = int(stats["previous_window_error_count"])

        now = utc_now()
        signature = (current_count, previous_count)
        with self._lock:
            # Relative threshold highlights abrupt recent changes over prior behavior.
            self._anomaly_active = previous_count > 0 and current_count > 2 * previous_count
            if not self._anomaly_active:
                return
            if self._last_alert_at is not None:
                if now - self._last_alert_at < self._cooldown and self._last_signature == signature:
                    return

            self._last_alert_at = now
            self._last_signature = signature
            self._last_anomaly = {
                "timestamp": now.isoformat(),
                "current_count": current_count,
                "previous_count": previous_count,
                "affected_service": affected_service or "unknown",
                "message": f"ANOMALY DETECTED: errors spiked from {previous_count} to {current_count}",
            }
            print(self._last_anomaly["message"])

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "cooldown_seconds": int(self._cooldown.total_seconds()),
                "anomaly_active": self._anomaly_active,
                "last_detected_anomaly": self._last_anomaly,
            }


anomaly_detection_service = AnomalyDetectionService()
