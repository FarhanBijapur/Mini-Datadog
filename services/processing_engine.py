from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock

from models.log_model import LogIn, ProcessedLog
from utils.time_utils import utc_now


class ProcessingEngine:
    """
    Processing is isolated from transport and storage so the pipeline can evolve:
    enrichment, normalization, sampling, or routing can be added without touching APIs.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        # Hashmap gives O(1) average updates for frequency counting by (service, level).
        self._frequency_by_service_level: dict[tuple[str, str], int] = defaultdict(int)
        self._error_count_per_service: dict[str, int] = defaultdict(int)
        self._total_error_count = 0
        # Two deques track rolling error windows without scanning all historical logs.
        self._current_window: deque[tuple[datetime, str]] = deque()
        self._previous_window: deque[tuple[datetime, str]] = deque()
        self._current_window_error_count = 0
        self._previous_window_error_count = 0

    def process(self, payload: LogIn) -> ProcessedLog:
        level = payload.level.upper()
        event_time = payload.timestamp
        if event_time is None:
            # Preserve event-time if provided; otherwise fallback to ingest-time.
            event_time = utc_now()
        received_at = utc_now()

        processed = ProcessedLog(
            source=payload.source,
            service=payload.service,
            level=level,
            message=payload.message,
            timestamp=event_time,
            attributes=payload.attributes,
            tags=payload.tags,
            trace_id=payload.trace_id,
            span_id=payload.span_id,
            received_at=received_at,
            processed_at=utc_now(),
        )
        self._update_aggregates(processed.service, processed.level, processed.processed_at)
        return processed

    def _update_aggregates(self, service: str, level: str, now: datetime) -> None:
        with self._lock:
            self._frequency_by_service_level[(service, level)] += 1
            if level == "ERROR":
                self._total_error_count += 1
                self._error_count_per_service[service] += 1

            # Sliding windows capture recent anomalies better than cumulative totals.
            # Each append/pop is O(1), and every log is removed once (amortized O(1)).
            self._current_window.append((now, level))
            if level == "ERROR":
                self._current_window_error_count += 1

            current_cutoff = now - timedelta(minutes=5)
            while self._current_window and self._current_window[0][0] < current_cutoff:
                moved_ts, moved_level = self._current_window.popleft()
                if moved_level == "ERROR":
                    self._current_window_error_count -= 1
                self._previous_window.append((moved_ts, moved_level))
                if moved_level == "ERROR":
                    self._previous_window_error_count += 1

            previous_cutoff = now - timedelta(minutes=10)
            while self._previous_window and self._previous_window[0][0] < previous_cutoff:
                _, expired_level = self._previous_window.popleft()
                if expired_level == "ERROR":
                    self._previous_window_error_count -= 1

    def snapshot(self) -> dict:
        with self._lock:
            frequency = {
                f"{service}:{level}": count
                for (service, level), count in self._frequency_by_service_level.items()
            }
            return {
                "total_error_count": self._total_error_count,
                "frequency_by_service_level": frequency,
                "error_count_per_service": dict(self._error_count_per_service),
                "current_window_error_count": self._current_window_error_count,
                "previous_window_error_count": self._previous_window_error_count,
                "current_window_size": len(self._current_window),
                "previous_window_size": len(self._previous_window),
            }


processing_engine = ProcessingEngine()
