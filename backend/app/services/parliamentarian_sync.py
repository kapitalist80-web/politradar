"""Sync service for parliamentarians, parties, parliamentary groups, and cantons.

Fetches data from ws.parlament.ch via swissparlpy and stores locally.
Runs monthly via scheduler.
"""

import asyncio
import logging
from datetime import datetime

import swissparlpy as spp
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Canton, Parliamentarian, ParlGroup, Party

logger = logging.getLogger(__name__)


def _fetch_member_council_sync() -> list[dict]:
    """Fetch all active council members via swissparlpy."""
    try:
        data = spp.get_data("MemberCouncil", Language="DE")
        return [dict(row) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch MemberCouncil: %s", exc)
        return []


def _fetch_parties_sync() -> list[dict]:
    """Fetch all parties."""
    try:
        data = spp.get_data("Party", Language="DE")
        return [dict(row) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch Party: %s", exc)
        return []


def _fetch_parl_groups_sync() -> list[dict]:
    """Fetch all parliamentary groups (Fraktionen)."""
    try:
        data = spp.get_data("ParlGroup", Language="DE")
        return [dict(row) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch ParlGroup: %s", exc)
        return []


def _fetch_cantons_sync() -> list[dict]:
    """Fetch all cantons."""
    try:
        data = spp.get_data("Canton", Language="DE")
        return [dict(row) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch Canton: %s", exc)
        return []


def _sync_cantons(db: Session, cantons_data: list[dict]) -> int:
    """Sync canton lookup data."""
    count = 0
    for row in cantons_data:
        canton_number = row.get("CantonNumber")
        if not canton_number:
            continue

        existing = db.query(Canton).filter(Canton.canton_number == canton_number).first()
        if existing:
            existing.canton_name = row.get("CantonName", existing.canton_name)
            existing.canton_abbreviation = row.get("CantonAbbreviation", existing.canton_abbreviation)
        else:
            db.add(Canton(
                canton_number=canton_number,
                canton_name=row.get("CantonName", ""),
                canton_abbreviation=row.get("CantonAbbreviation", ""),
            ))
            count += 1
    return count


def _sync_parties(db: Session, parties_data: list[dict]) -> int:
    """Sync party master data."""
    now = datetime.utcnow()
    count = 0
    for row in parties_data:
        party_number = row.get("PartyNumber")
        if not party_number:
            continue

        existing = db.query(Party).filter(Party.party_number == party_number).first()
        if existing:
            existing.party_name = row.get("PartyName", existing.party_name)
            existing.party_abbreviation = row.get("PartyAbbreviation", existing.party_abbreviation)
            existing.last_sync = now
        else:
            db.add(Party(
                party_number=party_number,
                party_name=row.get("PartyName", ""),
                party_abbreviation=row.get("PartyAbbreviation", ""),
                last_sync=now,
            ))
            count += 1
    return count


def _sync_parl_groups(db: Session, groups_data: list[dict]) -> int:
    """Sync parliamentary group data."""
    now = datetime.utcnow()
    count = 0
    for row in groups_data:
        pg_number = row.get("ParlGroupNumber")
        if not pg_number:
            continue

        existing = db.query(ParlGroup).filter(ParlGroup.parl_group_number == pg_number).first()
        if existing:
            existing.parl_group_name = row.get("ParlGroupName", existing.parl_group_name)
            existing.parl_group_abbreviation = row.get("ParlGroupAbbreviation", existing.parl_group_abbreviation)
            existing.last_sync = now
        else:
            db.add(ParlGroup(
                parl_group_number=pg_number,
                parl_group_name=row.get("ParlGroupName", ""),
                parl_group_abbreviation=row.get("ParlGroupAbbreviation", ""),
                last_sync=now,
            ))
            count += 1
    return count


def _sync_parliamentarians(db: Session, members_data: list[dict]) -> dict:
    """Sync parliamentarian data from MemberCouncil records."""
    now = datetime.utcnow()
    stats = {"added": 0, "updated": 0, "deactivated": 0}

    # Track person numbers we see in this sync
    seen_person_numbers = set()

    for row in members_data:
        person_number = row.get("PersonNumber")
        if not person_number:
            continue

        seen_person_numbers.add(person_number)

        # Parse date of birth
        dob = None
        dob_raw = row.get("DateOfBirth") or row.get("GenderAsString")
        if row.get("DateOfBirth"):
            try:
                dob_val = row["DateOfBirth"]
                if hasattr(dob_val, "date"):
                    dob = dob_val.date() if hasattr(dob_val, "date") else dob_val
                elif isinstance(dob_val, str):
                    dob = datetime.fromisoformat(dob_val).date()
            except (ValueError, TypeError):
                pass

        # Parse membership dates
        membership_start = None
        if row.get("DateJoining"):
            try:
                val = row["DateJoining"]
                if hasattr(val, "date"):
                    membership_start = val.date()
                elif isinstance(val, str):
                    membership_start = datetime.fromisoformat(val).date()
            except (ValueError, TypeError):
                pass

        membership_end = None
        if row.get("DateLeaving"):
            try:
                val = row["DateLeaving"]
                if hasattr(val, "date"):
                    membership_end = val.date()
                elif isinstance(val, str):
                    membership_end = datetime.fromisoformat(val).date()
            except (ValueError, TypeError):
                pass

        # Build photo URL
        photo_url = None
        if person_number:
            photo_url = f"https://www.parlament.ch/sitecollectionimages/profil/portrait-260/{person_number}.jpg"

        biografie_url = None
        if person_number:
            biografie_url = f"https://www.parlament.ch/de/biografie/x/{person_number}"

        existing = db.query(Parliamentarian).filter(
            Parliamentarian.person_number == person_number
        ).first()

        if existing:
            existing.first_name = row.get("FirstName", existing.first_name)
            existing.last_name = row.get("LastName", existing.last_name)
            existing.gender = row.get("GenderAsString", existing.gender)
            existing.date_of_birth = dob or existing.date_of_birth
            existing.canton_id = row.get("CantonNumber", existing.canton_id)
            existing.canton_name = row.get("CantonName", existing.canton_name)
            existing.canton_abbreviation = row.get("CantonAbbreviation", existing.canton_abbreviation)
            existing.council_id = row.get("CouncilId") or row.get("CouncilNumber", existing.council_id)
            existing.council_name = row.get("CouncilName", existing.council_name)
            existing.party_id = row.get("PartyNumber", existing.party_id)
            existing.party_name = row.get("PartyName", existing.party_name)
            existing.party_abbreviation = row.get("PartyAbbreviation", existing.party_abbreviation)
            existing.parl_group_id = row.get("ParlGroupNumber", existing.parl_group_id)
            existing.parl_group_name = row.get("ParlGroupName", existing.parl_group_name)
            existing.parl_group_abbreviation = row.get("ParlGroupAbbreviation", existing.parl_group_abbreviation)
            existing.active = not bool(membership_end)
            existing.membership_start = membership_start or existing.membership_start
            existing.membership_end = membership_end or existing.membership_end
            existing.biografie_url = biografie_url
            existing.photo_url = photo_url
            existing.last_sync = now
            existing.updated_at = now
            stats["updated"] += 1
        else:
            db.add(Parliamentarian(
                person_number=person_number,
                first_name=row.get("FirstName", ""),
                last_name=row.get("LastName", ""),
                gender=row.get("GenderAsString", ""),
                date_of_birth=dob,
                canton_id=row.get("CantonNumber"),
                canton_name=row.get("CantonName", ""),
                canton_abbreviation=row.get("CantonAbbreviation", ""),
                council_id=row.get("CouncilId") or row.get("CouncilNumber"),
                council_name=row.get("CouncilName", ""),
                party_id=row.get("PartyNumber"),
                party_name=row.get("PartyName", ""),
                party_abbreviation=row.get("PartyAbbreviation", ""),
                parl_group_id=row.get("ParlGroupNumber"),
                parl_group_name=row.get("ParlGroupName", ""),
                parl_group_abbreviation=row.get("ParlGroupAbbreviation", ""),
                active=not bool(membership_end),
                membership_start=membership_start,
                membership_end=membership_end,
                biografie_url=biografie_url,
                photo_url=photo_url,
                last_sync=now,
            ))
            stats["added"] += 1

    # Mark parliamentarians not in current data as inactive
    if seen_person_numbers:
        inactive = (
            db.query(Parliamentarian)
            .filter(
                Parliamentarian.active == True,
                ~Parliamentarian.person_number.in_(seen_person_numbers),
            )
            .all()
        )
        for p in inactive:
            p.active = False
            p.updated_at = now
            stats["deactivated"] += 1

    return stats


async def sync_parliamentarians():
    """Full sync of parliamentarians, parties, groups, and cantons.

    Called monthly by scheduler.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Starting parliamentarian sync...")

        # Fetch all data in parallel via threads
        members_data, parties_data, groups_data, cantons_data = await asyncio.gather(
            asyncio.to_thread(_fetch_member_council_sync),
            asyncio.to_thread(_fetch_parties_sync),
            asyncio.to_thread(_fetch_parl_groups_sync),
            asyncio.to_thread(_fetch_cantons_sync),
        )

        # Sync cantons first (lookup data)
        cantons_added = _sync_cantons(db, cantons_data)
        logger.info("Cantons sync: %d added", cantons_added)

        # Sync parties
        parties_added = _sync_parties(db, parties_data)
        logger.info("Parties sync: %d added", parties_added)

        # Sync parliamentary groups
        groups_added = _sync_parl_groups(db, groups_data)
        logger.info("Parl groups sync: %d added", groups_added)

        # Sync parliamentarians
        parl_stats = _sync_parliamentarians(db, members_data)
        logger.info(
            "Parliamentarians sync: %d added, %d updated, %d deactivated",
            parl_stats["added"], parl_stats["updated"], parl_stats["deactivated"],
        )

        db.commit()
        logger.info("Parliamentarian sync complete")
    except Exception:
        db.rollback()
        logger.exception("Parliamentarian sync failed")
    finally:
        db.close()
