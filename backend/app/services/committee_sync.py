"""Sync service for committees and committee memberships.

Fetches data from ws.parlament.ch via swissparlpy and stores locally.
Runs monthly via scheduler (together with parliamentarian sync).
"""

import asyncio
import logging
from datetime import datetime

import swissparlpy as spp
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Committee, CommitteeMembership

logger = logging.getLogger(__name__)


def _fetch_committees_sync() -> list[dict]:
    """Fetch all committees."""
    try:
        data = spp.get_data("Committee", Language="DE")
        return [dict(row) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch Committee: %s", exc)
        return []


def _fetch_member_committee_sync() -> list[dict]:
    """Fetch all active committee memberships."""
    try:
        data = spp.get_data("MemberCommittee", Language="DE")
        return [dict(row) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch MemberCommittee: %s", exc)
        return []


def _sync_committees(db: Session, committees_data: list[dict]) -> int:
    """Sync committee master data."""
    now = datetime.utcnow()
    count = 0

    for row in committees_data:
        committee_number = row.get("CommitteeNumber")
        if not committee_number:
            continue

        existing = db.query(Committee).filter(
            Committee.committee_number == committee_number
        ).first()

        if existing:
            existing.committee_name = row.get("CommitteeName", existing.committee_name)
            existing.committee_abbreviation = row.get("Abbreviation", existing.committee_abbreviation)
            existing.council_id = row.get("CouncilId") or row.get("CouncilNumber", existing.council_id)
            existing.committee_type = row.get("CommitteeTypeName", existing.committee_type)
            existing.is_active = row.get("IsActive", existing.is_active) if "IsActive" in row else existing.is_active
            existing.last_sync = now
        else:
            db.add(Committee(
                committee_number=committee_number,
                committee_name=row.get("CommitteeName", ""),
                committee_abbreviation=row.get("Abbreviation", ""),
                council_id=row.get("CouncilId") or row.get("CouncilNumber"),
                committee_type=row.get("CommitteeTypeName", ""),
                last_sync=now,
            ))
            count += 1

    return count


def _sync_committee_memberships(db: Session, memberships_data: list[dict]) -> dict:
    """Sync committee membership data."""
    now = datetime.utcnow()
    stats = {"added": 0, "updated": 0}

    for row in memberships_data:
        person_number = row.get("PersonNumber")
        committee_number = row.get("CommitteeNumber")
        if not person_number or not committee_number:
            continue

        # Parse dates
        start_date = None
        if row.get("DateJoining"):
            try:
                val = row["DateJoining"]
                if hasattr(val, "date"):
                    start_date = val.date()
                elif isinstance(val, str):
                    start_date = datetime.fromisoformat(val).date()
            except (ValueError, TypeError):
                pass

        end_date = None
        if row.get("DateLeaving"):
            try:
                val = row["DateLeaving"]
                if hasattr(val, "date"):
                    end_date = val.date()
                elif isinstance(val, str):
                    end_date = datetime.fromisoformat(val).date()
            except (ValueError, TypeError):
                pass

        # Check for existing membership
        query = db.query(CommitteeMembership).filter(
            CommitteeMembership.person_number == person_number,
            CommitteeMembership.committee_id == committee_number,
        )
        if start_date:
            query = query.filter(CommitteeMembership.start_date == start_date)
        else:
            query = query.filter(CommitteeMembership.start_date.is_(None))

        existing = query.first()

        if existing:
            existing.committee_name = row.get("CommitteeName", existing.committee_name)
            existing.committee_abbreviation = row.get("Abbreviation", existing.committee_abbreviation)
            existing.council_id = row.get("CouncilId") or row.get("CouncilNumber", existing.council_id)
            existing.function = row.get("Function", existing.function)
            existing.end_date = end_date
            existing.is_active = not bool(end_date)
            existing.last_sync = now
            stats["updated"] += 1
        else:
            db.add(CommitteeMembership(
                person_number=person_number,
                committee_id=committee_number,
                committee_name=row.get("CommitteeName", ""),
                committee_abbreviation=row.get("Abbreviation", ""),
                council_id=row.get("CouncilId") or row.get("CouncilNumber"),
                function=row.get("Function", ""),
                start_date=start_date,
                end_date=end_date,
                is_active=not bool(end_date),
                last_sync=now,
            ))
            stats["added"] += 1

    return stats


async def sync_committees():
    """Full sync of committees and memberships.

    Called monthly by scheduler.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Starting committee sync...")

        committees_data, memberships_data = await asyncio.gather(
            asyncio.to_thread(_fetch_committees_sync),
            asyncio.to_thread(_fetch_member_committee_sync),
        )

        committees_added = _sync_committees(db, committees_data)
        logger.info("Committees sync: %d added", committees_added)

        membership_stats = _sync_committee_memberships(db, memberships_data)
        logger.info(
            "Committee memberships sync: %d added, %d updated",
            membership_stats["added"], membership_stats["updated"],
        )

        db.commit()
        logger.info("Committee sync complete")
    except Exception:
        db.rollback()
        logger.exception("Committee sync failed")
    finally:
        db.close()
