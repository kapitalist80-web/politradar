import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import alerts, auth, businesses, monitoring, parliament, settings_router
from .routers import parliamentarians, committees_router, votes_router, predictions
from .services.scheduler import fetch_monitoring_candidates, sync_committee_schedules, sync_tracked_businesses
from .services.parliamentarian_sync import sync_parliamentarians
from .services.committee_sync import sync_committees
from .services.voting_sync import sync_voting_data
from .services.parliament_api import sync_cached_businesses

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist yet
    from sqlalchemy import inspect, text
    from .database import Base, engine
    Base.metadata.create_all(bind=engine)

    # Add missing columns for existing tables
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("tracked_businesses")]
        if "author" not in columns:
            conn.execute(text("ALTER TABLE tracked_businesses ADD COLUMN author VARCHAR(500)"))
            conn.commit()
            logger.info("Added author column to tracked_businesses")
        if "submitted_text" not in columns:
            conn.execute(text("ALTER TABLE tracked_businesses ADD COLUMN submitted_text TEXT"))
            conn.commit()
            logger.info("Added submitted_text column to tracked_businesses")
        if "reasoning" not in columns:
            conn.execute(text("ALTER TABLE tracked_businesses ADD COLUMN reasoning TEXT"))
            conn.commit()
            logger.info("Added reasoning column to tracked_businesses")
        if "federal_council_response" not in columns:
            conn.execute(text("ALTER TABLE tracked_businesses ADD COLUMN federal_council_response TEXT"))
            conn.commit()
            logger.info("Added federal_council_response column to tracked_businesses")
        if "federal_council_proposal" not in columns:
            conn.execute(text("ALTER TABLE tracked_businesses ADD COLUMN federal_council_proposal VARCHAR(200)"))
            conn.commit()
            logger.info("Added federal_council_proposal column to tracked_businesses")
        if "first_council" not in columns:
            conn.execute(text("ALTER TABLE tracked_businesses ADD COLUMN first_council VARCHAR(100)"))
            conn.commit()
            logger.info("Added first_council column to tracked_businesses")
        if "author_faction" not in columns:
            conn.execute(text("ALTER TABLE tracked_businesses ADD COLUMN author_faction VARCHAR(255)"))
            conn.commit()
            logger.info("Added author_faction column to tracked_businesses")

        # User table migrations
        user_columns = [c["name"] for c in inspector.get_columns("users")]
        if "email_alerts_enabled" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_alerts_enabled BOOLEAN DEFAULT FALSE"))
            conn.commit()
            logger.info("Added email_alerts_enabled column to users")
        if "email_alert_types" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_alert_types VARCHAR(500) DEFAULT 'status_change,committee_scheduled,debate_scheduled'"))
            conn.commit()
            logger.info("Added email_alert_types column to users")

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
    scheduler.add_job(
        sync_committee_schedules,
        "interval",
        hours=settings.SYNC_INTERVAL_HOURS,
        id="sync_committee_schedules",
    )
    # Monthly sync for parliamentarians and committees (1st of each month at 03:00)
    scheduler.add_job(
        sync_parliamentarians,
        "cron",
        day=1,
        hour=3,
        id="sync_parliamentarians",
    )
    scheduler.add_job(
        sync_committees,
        "cron",
        day=1,
        hour=3,
        minute=30,
        id="sync_committees_data",
    )
    # Weekly voting data sync (Sunday at 04:00)
    scheduler.add_job(
        sync_voting_data,
        "cron",
        day_of_week="sun",
        hour=4,
        id="sync_voting_data",
    )
    # Daily business cache sync (02:00)
    scheduler.add_job(
        sync_cached_businesses,
        "cron",
        hour=2,
        id="sync_cached_businesses",
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
app.include_router(settings_router.router)
app.include_router(parliamentarians.router)
app.include_router(committees_router.router)
app.include_router(committees_router.councils_router)
app.include_router(committees_router.parties_router)
app.include_router(committees_router.parl_groups_router)
app.include_router(votes_router.router)
app.include_router(predictions.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Manual sync endpoints ---

from .auth import get_current_user
from .models import User


@app.post("/api/sync/parliamentarians")
async def trigger_sync_parliamentarians(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Manually trigger parliamentarian + party + canton sync."""
    background_tasks.add_task(sync_parliamentarians)
    return {"status": "started", "job": "sync_parliamentarians"}


@app.post("/api/sync/committees")
async def trigger_sync_committees(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Manually trigger committee + membership sync."""
    background_tasks.add_task(sync_committees)
    return {"status": "started", "job": "sync_committees"}


@app.post("/api/sync/voting-data")
async def trigger_sync_voting_data(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Manually trigger voting data sync (can take several minutes)."""
    background_tasks.add_task(sync_voting_data)
    return {"status": "started", "job": "sync_voting_data"}


@app.post("/api/sync/businesses")
async def trigger_sync_businesses(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Manually trigger business cache sync (years 25/26)."""
    background_tasks.add_task(sync_cached_businesses)
    return {"status": "started", "job": "sync_cached_businesses"}


@app.post("/api/sync/all")
async def trigger_sync_all(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Trigger all parliament data syncs (parliamentarians, committees, voting data, businesses)."""
    background_tasks.add_task(sync_parliamentarians)
    background_tasks.add_task(sync_committees)
    background_tasks.add_task(sync_voting_data)
    background_tasks.add_task(sync_cached_businesses)
    return {"status": "started", "jobs": ["sync_parliamentarians", "sync_committees", "sync_voting_data", "sync_cached_businesses"]}
