import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import alerts, auth, businesses, monitoring, parliament
from .services.scheduler import fetch_monitoring_candidates, sync_tracked_businesses

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist yet
    from .database import Base, engine
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")

    # Start scheduler
    scheduler.add_job(
        sync_tracked_businesses,
        "interval",
        hours=settings.SYNC_INTERVAL_HOURS,
        id="sync_businesses",
    )
    scheduler.add_job(
        fetch_monitoring_candidates,
        "cron",
        hour=settings.MONITORING_CRON_HOUR,
        id="monitoring_candidates",
    )
    scheduler.start()
    logger.info("Scheduler started")
    yield
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(businesses.router)
app.include_router(alerts.router)
app.include_router(monitoring.router)
app.include_router(parliament.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
