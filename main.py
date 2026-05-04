from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import mongo_manager
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
    version="1.0.0",
    lifespan=lifespan,
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


@app.get("/healthz")
async def health_check() -> dict:
    return {"status": "ok"}
