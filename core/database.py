import threading

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from core.config import settings


class MongoManager:
    """
    Single MongoDB manager to avoid creating many clients per request.
    One process-wide client is the common production pattern for PyMongo.

    MongoDB fits log ingestion well because log payloads evolve quickly and document
    schema flexibility avoids expensive migrations for every new attribute.
    It also offers strong write scalability for append-heavy workloads.

    Trade-off vs PostgreSQL: PostgreSQL provides stronger relational guarantees and
    richer joins/constraints, but that schema rigidity is usually a poor fit for
    high-cardinality, semi-structured telemetry events.
    """

    _instance: "MongoManager | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "MongoManager":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._client: MongoClient | None = None
        self._db: Database | None = None
        self._lock = threading.Lock()
        self._initialized = True

    def connect(self) -> None:
        with self._lock:
            if self._client is not None:
                return
            self._client = MongoClient(settings.mongodb_uri)
            self._db = self._client[settings.mongodb_db_name]
            self._ensure_indexes()

    def close(self) -> None:
        with self._lock:
            if self._client is not None:
                self._client.close()
            self._client = None
            self._db = None

    @property
    def logs_collection(self) -> Collection:
        if self._db is None:
            raise RuntimeError("MongoDB is not connected")
        return self._db[settings.mongodb_logs_collection]

    def _ensure_indexes(self) -> None:
        """
        create_index is idempotent when the same key pattern exists.
        Running this at startup guarantees query-ready collections after deploy.
        """
        self.logs_collection.create_index([("timestamp", ASCENDING)], name="idx_logs_timestamp")
        self.logs_collection.create_index([("service", ASCENDING)], name="idx_logs_service")
        self.logs_collection.create_index([("level", ASCENDING)], name="idx_logs_level")


mongo_manager = MongoManager()
