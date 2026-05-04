import hashlib
from collections import OrderedDict
from datetime import datetime
from threading import Lock

from core.config import settings
from utils.time_utils import utc_now


class DedupeService:
    """
    Best-effort duplicate suppression in memory:
    - Fast: O(1) average hash lookup/update.
    - Imperfect: process restarts lose cache state and cross-instance dedupe is not guaranteed.
    """

    def __init__(self) -> None:
        self._max_size = max(1000, min(5000, settings.dedupe_cache_size))
        self._ttl_seconds = max(60, min(120, settings.dedupe_ttl_seconds))
        self._cache: OrderedDict[str, datetime] = OrderedDict()
        self._lock = Lock()

    def _fingerprint(self, payload: dict) -> str:
        # Rounded timestamp reduces tiny timestamp jitter while keeping duplicates close together.
        timestamp_raw = payload.get("timestamp")
        rounded_ts = "none"
        if timestamp_raw:
            try:
                parsed_ts = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
                rounded_ts = parsed_ts.replace(second=0, microsecond=0).isoformat()
            except ValueError:
                rounded_ts = str(timestamp_raw)
        raw = (
            f"{payload.get('service','')}|{payload.get('level','')}|"
            f"{payload.get('message','')}|{rounded_ts}"
        )
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def is_duplicate(self, payload: dict) -> bool:
        now = utc_now()
        key = self._fingerprint(payload)
        with self._lock:
            self._purge_expired(now)
            if key in self._cache:
                self._cache.move_to_end(key)
                return True
            self._cache[key] = now
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)
            return False

    def _purge_expired(self, now: datetime) -> None:
        # OrderedDict preserves age ordering; popping from the head is O(1) amortized.
        while self._cache:
            first_key = next(iter(self._cache))
            age = (now - self._cache[first_key]).total_seconds()
            if age <= self._ttl_seconds:
                break
            self._cache.popitem(last=False)


dedupe_service = DedupeService()
