"""Sync service for voting data (Vote + individual Voting records).

Fetches data from ws.parlament.ch via swissparlpy session-wise.
Runs weekly via scheduler.
"""

import asyncio
import logging
import time
from datetime import datetime

import swissparlpy as spp
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Vote, Voting

logger = logging.getLogger(__name__)

# Legislative period 51 (since 2023) session IDs
# These are fetched dynamically, but we start from session 5100 onwards
MIN_SESSION_ID = 5100


def _fetch_sessions_sync() -> list[dict]:
    """Fetch all available sessions."""
    try:
        data = spp.get_data("Session", Language="DE")
        return [dict(row) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch Session: %s", exc)
        return []


def _fetch_votes_of_session_sync(session_id: int) -> list[dict]:
    """Fetch all votes of a session."""
    try:
        data = spp.get_data("Vote", Language="DE", IdSession=session_id)
        return [dict(v) for v in data]
    except Exception as exc:
        logger.warning("Failed to fetch Vote for session %s: %s", session_id, exc)
        return []


def _fetch_votings_of_vote_sync(vote_id: int) -> list[dict]:
    """Fetch individual voting records for a specific vote."""
    try:
        data = spp.get_data("Voting", Language="DE", IdVote=vote_id)
        return [dict(v) for v in data]
    except Exception as exc:
        logger.warning("Failed to fetch Voting for vote %s: %s", vote_id, exc)
        return []


def _parse_odata_date(raw) -> datetime | None:
    """Parse OData date formats."""
    if not raw:
        return None
    try:
        if hasattr(raw, "isoformat"):
            return raw if isinstance(raw, datetime) else datetime.combine(raw, datetime.min.time())
        raw_str = str(raw)
        if "/Date(" in raw_str:
            ts = int(raw_str.split("(")[1].split(")")[0].split("+")[0].split("-")[0])
            return datetime.utcfromtimestamp(ts / 1000)
        return datetime.fromisoformat(raw_str.replace("Z", "+00:00"))
    except (ValueError, IndexError, TypeError):
        return None


def _sync_vote_record(db: Session, vote_data: dict, session_name: str = "") -> bool:
    """Sync a single vote record. Returns True if new."""
    vote_id = vote_data.get("ID") or vote_data.get("IdVote")
    if not vote_id:
        return False

    existing = db.query(Vote).filter(Vote.vote_id == vote_id).first()
    if existing:
        return False

    vote_date = _parse_odata_date(vote_data.get("VoteDate") or vote_data.get("Date"))

    db.add(Vote(
        vote_id=vote_id,
        business_number=vote_data.get("BusinessShortNumber", ""),
        business_title=vote_data.get("BusinessTitle", ""),
        subject=vote_data.get("Subject", ""),
        meaning_yes=vote_data.get("MeaningYes", ""),
        meaning_no=vote_data.get("MeaningNo", ""),
        vote_date=vote_date,
        council_id=vote_data.get("CouncilId") or vote_data.get("IdCouncil"),
        session_id=str(vote_data.get("IdSession", "")),
        session_name=session_name,
        total_yes=vote_data.get("TotalYes"),
        total_no=vote_data.get("TotalNo"),
        total_abstain=vote_data.get("TotalAbstain"),
        total_not_voted=vote_data.get("TotalNotVoted"),
        result=vote_data.get("ResultText", ""),
    ))
    return True


def _sync_voting_records(db: Session, vote_id: int, votings_data: list[dict]) -> int:
    """Sync individual voting records for a vote. Returns count of new records."""
    count = 0
    for row in votings_data:
        person_number = row.get("PersonNumber")
        if not person_number:
            continue

        existing = db.query(Voting).filter(
            Voting.vote_id == vote_id,
            Voting.person_number == person_number,
        ).first()
        if existing:
            continue

        decision = row.get("DecisionText") or row.get("Decision", "")
        # Normalize decision values
        decision_map = {
            "Ja": "Yes",
            "Nein": "No",
            "Enthaltung": "Abstention",
            "Entschuldigt": "Absent",
            "Hat nicht teilgenommen": "Absent",
            "Die Präsidentin/Der Präsident": "President",
        }
        decision = decision_map.get(decision, decision)

        db.add(Voting(
            vote_id=vote_id,
            person_number=person_number,
            decision=decision,
            parl_group_number=row.get("ParlGroupNumber"),
            canton_id=row.get("CantonNumber"),
        ))
        count += 1

    return count


async def sync_voting_data():
    """Sync voting data: fetch new votes and individual voting records.

    Called weekly by scheduler. Processes session-wise with rate limiting.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Starting voting data sync...")

        # Get all sessions
        sessions_data = await asyncio.to_thread(_fetch_sessions_sync)
        if not sessions_data:
            logger.warning("No sessions fetched")
            return

        # Build session name lookup
        session_name_map = {}
        for s in sessions_data:
            sid = s.get("ID")
            name = s.get("SessionName") or s.get("Abbreviation") or ""
            if sid:
                session_name_map[sid] = name

        # Filter to recent sessions (legislative period 51+)
        recent_sessions = [
            s for s in sessions_data
            if (s.get("ID") or 0) >= MIN_SESSION_ID
        ]
        recent_sessions.sort(key=lambda s: s.get("ID", 0))

        total_new_votes = 0
        total_new_votings = 0

        for session in recent_sessions:
            session_id = session.get("ID")
            if not session_id:
                continue

            # Check if we already have votes from this session
            existing_count = db.query(Vote).filter(Vote.session_id == str(session_id)).count()

            # Fetch votes for this session
            votes_data = await asyncio.to_thread(_fetch_votes_of_session_sync, session_id)

            if not votes_data:
                continue

            # Skip if we already have all votes from this session
            if existing_count >= len(votes_data):
                continue

            logger.info("Processing session %s: %d votes found", session_id, len(votes_data))

            for vote_data in votes_data:
                vote_id = vote_data.get("ID") or vote_data.get("IdVote")
                if not vote_id:
                    continue

                is_new = _sync_vote_record(db, vote_data, session_name=session_name_map.get(session_id, ""))
                if is_new:
                    total_new_votes += 1

                    # Fetch individual voting records
                    votings_data = await asyncio.to_thread(
                        _fetch_votings_of_vote_sync, vote_id
                    )
                    new_votings = _sync_voting_records(db, vote_id, votings_data)
                    total_new_votings += new_votings

                    # Rate limiting between voting fetches
                    await asyncio.sleep(0.5)

            # Commit per session and rate limit between sessions
            db.commit()
            await asyncio.sleep(1.0)

        # Backfill session names for existing votes that are missing them
        for sid, sname in session_name_map.items():
            if sname:
                db.query(Vote).filter(
                    Vote.session_id == str(sid),
                    Vote.session_name.is_(None),
                ).update({"session_name": sname}, synchronize_session=False)
        db.commit()

        logger.info(
            "Voting sync complete: %d new votes, %d new voting records",
            total_new_votes, total_new_votings,
        )
    except Exception:
        db.rollback()
        logger.exception("Voting sync failed")
    finally:
        db.close()
