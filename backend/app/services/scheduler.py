import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Alert, BusinessEvent, MonitoringCandidate, TrackedBusiness
from .parliament_api import fetch_business, fetch_new_businesses

logger = logging.getLogger(__name__)


async def sync_tracked_businesses():
    """Sync all tracked businesses with parlament.ch API (runs every 6 hours)."""
    db: Session = SessionLocal()
    try:
        businesses = db.query(TrackedBusiness).all()
        seen: set[str] = set()

        for biz in businesses:
            if biz.business_number in seen:
                continue
            seen.add(biz.business_number)

            logger.info("Syncing %s", biz.business_number)
            info = await fetch_business(biz.business_number)
            if not info:
                logger.warning("Could not fetch %s", biz.business_number)
                continue

            new_status = info.get("status", "")
            old_status = biz.status or ""

            # Check for status change
            if new_status and new_status != old_status:
                event = BusinessEvent(
                    business_number=biz.business_number,
                    event_type="status_change",
                    event_date=datetime.utcnow(),
                    description=f"Status: {old_status} → {new_status}",
                )
                db.add(event)

                # Create alerts for all users tracking this business
                trackers = (
                    db.query(TrackedBusiness)
                    .filter(TrackedBusiness.business_number == biz.business_number)
                    .all()
                )
                for t in trackers:
                    alert = Alert(
                        user_id=t.user_id,
                        business_number=biz.business_number,
                        alert_type="status_change",
                        message=f"Geschaeft {biz.business_number}: Status geaendert von '{old_status}' zu '{new_status}'",
                    )
                    db.add(alert)

            # Update all tracked instances
            all_instances = (
                db.query(TrackedBusiness)
                .filter(TrackedBusiness.business_number == biz.business_number)
                .all()
            )
            for inst in all_instances:
                inst.title = info.get("title") or inst.title
                inst.description = info.get("description") or inst.description
                inst.status = new_status or inst.status
                inst.business_type = info.get("business_type") or inst.business_type
                inst.author = info.get("author") or inst.author
                inst.submitted_text = info.get("submitted_text") or inst.submitted_text
                inst.reasoning = info.get("reasoning") or inst.reasoning
                inst.federal_council_response = info.get("federal_council_response") or inst.federal_council_response
                inst.federal_council_proposal = info.get("federal_council_proposal") or inst.federal_council_proposal
                inst.first_council = info.get("first_council") or inst.first_council
                inst.last_api_sync = datetime.utcnow()

        db.commit()
        logger.info("Sync complete: %d businesses processed", len(seen))
    except Exception:
        db.rollback()
        logger.exception("Sync failed")
    finally:
        db.close()


async def fetch_monitoring_candidates():
    """Fetch new businesses for monitoring (runs daily at 07:00)."""
    db: Session = SessionLocal()
    try:
        since = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
        new_businesses = await fetch_new_businesses(since)
        added = 0

        for biz in new_businesses:
            nr = biz.get("business_number", "")
            if not nr:
                continue

            exists = (
                db.query(MonitoringCandidate)
                .filter(MonitoringCandidate.business_number == nr)
                .first()
            )
            if exists:
                continue

            candidate = MonitoringCandidate(
                business_number=nr,
                title=biz.get("title"),
                description=biz.get("description"),
                business_type=biz.get("business_type"),
                submission_date=biz.get("submission_date"),
            )
            db.add(candidate)
            added += 1

        db.commit()
        logger.info("Monitoring: %d new candidates added", added)
    except Exception:
        db.rollback()
        logger.exception("Monitoring fetch failed")
    finally:
        db.close()
