from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import mongo_manager
from models.health_model import HealthResponse
from routes.logs import router as logs_router
from routes.metrics import router as metrics_router
from services.worker import log_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Keep external resources in lifespan so boot/shutdown are deterministic.
    mongo_manager.connect()
    await log_worker.start()
    try:
        yield
    finally:
        await log_worker.stop()
        mongo_manager.close()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Local observability demo API for ingesting logs, reading recent persisted "
        "events, and exposing real-time metrics for the React dashboard."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "health",
            "description": "Readiness and liveness endpoints.",
        },
        {
            "name": "logs",
            "description": "Log ingestion and recent-log retrieval endpoints.",
        },
        {
            "name": "metrics",
            "description": "Real-time metrics and anomaly detection endpoints.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs_router)
app.include_router(metrics_router)


@app.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["health"],
    summary="Check API health",
    description="Returns a lightweight health signal for local readiness checks.",
    responses={
        200: {
            "description": "API is healthy.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                    }
                }
            },
        }
    },
)
async def health_check() -> dict:
    return {"status": "ok"}
