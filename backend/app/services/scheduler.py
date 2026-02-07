import logging
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Alert, BusinessEvent, MonitoringCandidate, TrackedBusiness, User
from .email_service import send_alert_email
from .parliament_api import fetch_business, fetch_new_businesses, fetch_preconsultations, fetch_session_schedule

logger = logging.getLogger(__name__)


def _send_email_notifications(db: Session, new_alerts: list[Alert]) -> None:
    """Send email notifications to users who have email alerts enabled.

    Groups alerts by user and sends a single summary email per user.
    """
    if not new_alerts:
        return

    # Group alerts by user_id
    alerts_by_user: dict[int, list[Alert]] = defaultdict(list)
    for alert in new_alerts:
        alerts_by_user[alert.user_id].append(alert)

    # Get users with email alerts enabled
    user_ids = list(alerts_by_user.keys())
    users = (
        db.query(User)
        .filter(User.id.in_(user_ids), User.email_alerts_enabled == True)
        .all()
    )

    # Build title lookup for business numbers
    all_biz_numbers = list({a.business_number for a in new_alerts})
    title_map: dict[str, str] = {}
    if all_biz_numbers:
        rows = (
            db.query(TrackedBusiness.business_number, TrackedBusiness.title)
            .filter(TrackedBusiness.business_number.in_(all_biz_numbers))
            .all()
        )
        for row in rows:
            if row.title:
                title_map[row.business_number] = row.title

    for user in users:
        # Filter alerts by user's configured alert types
        enabled_types_str = user.email_alert_types or ""
        enabled_types = {t.strip() for t in enabled_types_str.split(",") if t.strip()}
        if not enabled_types:
            continue

        user_alerts = [
            a for a in alerts_by_user[user.id]
            if a.alert_type in enabled_types
        ]
        if not user_alerts:
            continue

        # Prepare alert dicts for the email template
        alert_dicts = []
        for a in user_alerts:
            alert_dicts.append({
                "business_number": a.business_number,
                "business_title": title_map.get(a.business_number, ""),
                "alert_type": a.alert_type,
                "message": a.message,
                "event_date": a.event_date,
            })

        send_alert_email(user.email, user.name, alert_dicts)


async def sync_tracked_businesses():
    """Sync all tracked businesses with parlament.ch API (runs every 6 hours)."""
    db: Session = SessionLocal()
    new_alerts: list[Alert] = []
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
                    description=f"Status: {old_status} \u2192 {new_status}",
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
                    new_alerts.append(alert)

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
                inst.author_faction = info.get("author_faction") or inst.author_faction
                inst.submitted_text = info.get("submitted_text") or inst.submitted_text
                inst.reasoning = info.get("reasoning") or inst.reasoning
                inst.federal_council_response = info.get("federal_council_response") or inst.federal_council_response
                inst.federal_council_proposal = info.get("federal_council_proposal") or inst.federal_council_proposal
                inst.first_council = info.get("first_council") or inst.first_council
                inst.last_api_sync = datetime.utcnow()

        db.commit()
        logger.info("Sync complete: %d businesses processed", len(seen))

        # Send email notifications for new alerts
        _send_email_notifications(db, new_alerts)
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


async def sync_committee_schedules():
    """Check for new committee/session scheduling of tracked businesses (runs every 6 hours)."""
    db: Session = SessionLocal()
    new_alerts: list[Alert] = []
    try:
        businesses = db.query(TrackedBusiness).all()
        seen: set[str] = set()
        new_events = 0

        for biz in businesses:
            if biz.business_number in seen:
                continue
            seen.add(biz.business_number)

            # Fetch committee pre-consultations
            preconsultations = await fetch_preconsultations(biz.business_number)
            for precon in preconsultations:
                committee = precon.get("committee_name", "")
                precon_date = precon.get("date")
                # Build a dedup key from business_number + committee + date
                description = f"Vorberatung: {committee}"
                if precon.get("committee_abbrev"):
                    description += f" ({precon['committee_abbrev']})"
                if precon.get("treatment_category"):
                    description += f" \u2013 Kategorie: {precon['treatment_category']}"

                existing = (
                    db.query(BusinessEvent)
                    .filter(
                        BusinessEvent.business_number == biz.business_number,
                        BusinessEvent.event_type == "committee_scheduled",
                        BusinessEvent.committee_name == committee,
                        BusinessEvent.description == description,
                    )
                    .first()
                )
                if existing:
                    continue

                event_date = None
                if precon_date:
                    try:
                        event_date = datetime.fromisoformat(precon_date)
                    except (ValueError, TypeError):
                        pass

                event = BusinessEvent(
                    business_number=biz.business_number,
                    event_type="committee_scheduled",
                    event_date=event_date,
                    description=description,
                    committee_name=committee,
                )
                db.add(event)
                new_events += 1

                # Alert all users tracking this business
                trackers = (
                    db.query(TrackedBusiness)
                    .filter(TrackedBusiness.business_number == biz.business_number)
                    .all()
                )
                for t in trackers:
                    date_str = event_date.strftime("%d.%m.%Y") if event_date else "unbekannt"
                    alert = Alert(
                        user_id=t.user_id,
                        business_number=biz.business_number,
                        alert_type="committee_scheduled",
                        event_date=event_date,
                        message=f"Geschaeft {biz.business_number}: {description} (Datum: {date_str})",
                    )
                    db.add(alert)
                    new_alerts.append(alert)

            # Fetch plenary session schedule
            sessions = await fetch_session_schedule(biz.business_number)
            for sess in sessions:
                council = sess.get("council", "")
                session_name = sess.get("session_name", "")
                meeting_date = sess.get("meeting_date")
                description = f"Traktandiert: {council}"
                if session_name:
                    description += f", {session_name}"
                if sess.get("meeting_order"):
                    description += f" \u2013 {sess['meeting_order']}"

                existing = (
                    db.query(BusinessEvent)
                    .filter(
                        BusinessEvent.business_number == biz.business_number,
                        BusinessEvent.event_type == "debate_scheduled",
                        BusinessEvent.description == description,
                    )
                    .first()
                )
                if existing:
                    continue

                event_date = None
                if meeting_date:
                    try:
                        event_date = datetime.fromisoformat(meeting_date)
                    except (ValueError, TypeError):
                        pass

                event = BusinessEvent(
                    business_number=biz.business_number,
                    event_type="debate_scheduled",
                    event_date=event_date,
                    description=description,
                    committee_name=council,
                )
                db.add(event)
                new_events += 1

                trackers = (
                    db.query(TrackedBusiness)
                    .filter(TrackedBusiness.business_number == biz.business_number)
                    .all()
                )
                for t in trackers:
                    date_str = event_date.strftime("%d.%m.%Y") if event_date else "unbekannt"
                    alert = Alert(
                        user_id=t.user_id,
                        business_number=biz.business_number,
                        alert_type="debate_scheduled",
                        event_date=event_date,
                        message=f"Geschaeft {biz.business_number}: {description} (Datum: {date_str})",
                    )
                    db.add(alert)
                    new_alerts.append(alert)

        db.commit()
        logger.info("Committee schedule sync: %d new events for %d businesses", new_events, len(seen))

        # Send email notifications for new alerts
        _send_email_notifications(db, new_alerts)
    except Exception:
        db.rollback()
        logger.exception("Committee schedule sync failed")
    finally:
        db.close()
