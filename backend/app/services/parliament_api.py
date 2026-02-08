import asyncio
import logging
import time
from datetime import datetime, timedelta

import httpx
import swissparlpy as spp

from ..config import settings

logger = logging.getLogger(__name__)

BASE = settings.PARLIAMENT_API_BASE
TIMEOUT = 30.0
MAX_RETRIES = 3

# In-memory cache for recent businesses (title + number)
_recent_businesses_cache: list[dict] = []
_recent_businesses_cache_time: datetime | None = None
_CACHE_TTL_HOURS = 6


async def _get(url: str, params: dict | None = None) -> dict | None:
    """GET request with retry and backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("Parliament API attempt %d failed: %s", attempt + 1, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    return None


async def fetch_business(business_number: str) -> dict | None:
    """Fetch a single business by its number (e.g. '24.3927')."""
    url = f"{BASE}/Business"
    params = {
        "$filter": f"Language eq 'DE'",
        "$format": "json",
    }
    data = await _get(url, params={
        **params,
        "$filter": f"BusinessShortNumber eq '{business_number}' and Language eq 'DE'",
    })
    if not data:
        return None

    results = data.get("d", {}).get("results", []) if isinstance(data.get("d"), dict) else []
    if not results:
        # Try alternative response format
        results = data.get("d", []) if isinstance(data.get("d"), list) else []
    if not results:
        return None

    item = results[0] if isinstance(results, list) else results
    parsed = _parse_business(item, business_number)

    # Fetch author faction in parallel
    try:
        faction = await fetch_author_faction(business_number)
        if faction:
            parsed["author_faction"] = faction
    except Exception:
        logger.debug("Could not fetch faction for %s", business_number)

    return parsed


def _parse_business(item: dict, business_number: str) -> dict:
    submission_raw = item.get("SubmissionDate")
    submission_date = None
    if submission_raw:
        try:
            # OData date format: /Date(timestamp)/
            if "/Date(" in str(submission_raw):
                ts = int(str(submission_raw).split("(")[1].split(")")[0].split("+")[0].split("-")[0])
                submission_date = datetime.utcfromtimestamp(ts / 1000).isoformat()
            else:
                submission_date = submission_raw
        except (ValueError, IndexError):
            submission_date = str(submission_raw)

    return {
        "title": item.get("Title", ""),
        "description": item.get("Description", ""),
        "status": item.get("BusinessStatusText", ""),
        "business_type": item.get("BusinessTypeName", ""),
        "author": item.get("SubmittedBy", ""),
        "submitted_text": item.get("SubmittedText", ""),
        "reasoning": item.get("ReasonText", ""),
        "federal_council_response": item.get("FederalCouncilResponseText", ""),
        "federal_council_proposal": item.get("FederalCouncilProposalText", ""),
        "first_council": item.get("FirstCouncil1Name", ""),
        "submission_date": submission_date,
    }


async def fetch_author_faction(business_number: str) -> str | None:
    """Fetch the parliamentary faction (Fraktion) of the business author via BusinessRole."""
    url = f"{BASE}/BusinessRole"
    params = {
        "$filter": f"BusinessShortNumber eq '{business_number}' and Language eq 'DE'",
        "$format": "json",
    }
    data = await _get(url, params)
    if not data:
        return None

    results = data.get("d", {}).get("results", []) if isinstance(data.get("d"), dict) else []
    if not results:
        results = data.get("d", []) if isinstance(data.get("d"), list) else []

    # Find a role that has a MemberCouncilNumber (the author)
    member_council_number = None
    for role in results:
        mcn = role.get("MemberCouncilNumber")
        if mcn:
            member_council_number = mcn
            break

    if not member_council_number:
        return None

    # Fetch the MemberCouncil to get ParlGroupName
    mc_url = f"{BASE}/MemberCouncil"
    mc_params = {
        "$filter": f"ID eq {member_council_number} and Language eq 'DE'",
        "$format": "json",
        "$select": "ParlGroupName,ParlGroupAbbreviation,PartyName",
    }
    mc_data = await _get(mc_url, mc_params)
    if not mc_data:
        return None

    mc_results = mc_data.get("d", {}).get("results", []) if isinstance(mc_data.get("d"), dict) else []
    if not mc_results:
        mc_results = mc_data.get("d", []) if isinstance(mc_data.get("d"), list) else []
    if not mc_results:
        return None

    member = mc_results[0] if isinstance(mc_results, list) else mc_results
    faction = member.get("ParlGroupName") or member.get("PartyName") or ""
    return faction if faction else None


async def fetch_recent_businesses_cached() -> list[dict]:
    """Return cached list of business_number + title from the database.

    Falls back to API if the DB cache is empty.
    """
    from ..database import SessionLocal
    from ..models import CachedBusiness

    db = SessionLocal()
    try:
        count = db.query(CachedBusiness).count()
        if count > 0:
            rows = db.query(CachedBusiness).order_by(CachedBusiness.business_number.desc()).all()
            return [{"business_number": r.business_number, "title": r.title or ""} for r in rows]
    finally:
        db.close()

    # Fallback: fetch from API and return (without persisting)
    return await _fetch_businesses_from_api()


async def _fetch_businesses_from_api() -> list[dict]:
    """Fetch businesses for years 25/26 from parliament API."""
    url = f"{BASE}/Business"
    all_results: list[dict] = []

    for year_prefix in ["25.", "26."]:
        skip = 0
        batch_size = 500
        while True:
            params = {
                "$filter": f"startswith(BusinessShortNumber, '{year_prefix}') and Language eq 'DE'",
                "$format": "json",
                "$select": "BusinessShortNumber,Title",
                "$orderby": "BusinessShortNumber desc",
                "$top": str(batch_size),
                "$skip": str(skip),
            }
            data = await _get(url, params)
            if not data:
                break

            results = data.get("d", {}).get("results", []) if isinstance(data.get("d"), dict) else []
            if not results:
                results = data.get("d", []) if isinstance(data.get("d"), list) else []
            if not results:
                break

            for item in results:
                nr = item.get("BusinessShortNumber", "")
                if nr:
                    all_results.append({
                        "business_number": nr,
                        "title": item.get("Title", ""),
                    })
            if len(results) < batch_size:
                break
            skip += batch_size

    logger.info("Fetched %d businesses from API for years 25/26", len(all_results))
    return all_results


async def sync_cached_businesses():
    """Fetch businesses for years 25/26 from API and store in DB."""
    from ..database import SessionLocal
    from ..models import CachedBusiness

    businesses = await _fetch_businesses_from_api()
    if not businesses:
        logger.warning("No businesses fetched from API for sync")
        return

    db = SessionLocal()
    try:
        existing = {r.business_number for r in db.query(CachedBusiness.business_number).all()}
        seen = set(existing)
        new_count = 0
        for b in businesses:
            nr = b["business_number"]
            if nr not in seen:
                seen.add(nr)
                db.add(CachedBusiness(
                    business_number=nr,
                    title=b.get("title", ""),
                ))
                new_count += 1
        db.commit()
        logger.info("Business cache sync complete: %d new, %d total", new_count, len(existing) + new_count)
    except Exception:
        db.rollback()
        logger.exception("Error syncing business cache")
        raise
    finally:
        db.close()


async def search_businesses(query: str) -> list[dict]:
    """Search businesses by text query."""
    url = f"{BASE}/Business"
    params = {
        "$filter": f"substringof('{query}', Title) and Language eq 'DE'",
        "$format": "json",
        "$top": "20",
        "$orderby": "SubmissionDate desc",
    }
    data = await _get(url, params)
    if not data:
        return []

    results = data.get("d", {}).get("results", []) if isinstance(data.get("d"), dict) else []
    if not results:
        results = data.get("d", []) if isinstance(data.get("d"), list) else []

    out = []
    for item in results:
        nr = item.get("BusinessShortNumber", "")
        parsed = _parse_business(item, nr)
        out.append({
            "business_number": nr,
            **parsed,
        })
    return out


def _short_number_to_id(business_number: str) -> int:
    """Convert short number '24.3961' to OData integer ID 20243961."""
    return int("20" + business_number.replace(".", ""))


async def fetch_business_status(business_number: str) -> list[dict]:
    """Fetch the status history for a business and return parsed events."""
    business_id = _short_number_to_id(business_number)
    url = f"{BASE}/BusinessStatus"
    params = {
        "$filter": f"BusinessNumber eq {business_id} and Language eq 'DE'",
        "$format": "json",
        "$orderby": "Modified desc",
    }
    data = await _get(url, params)
    if not data:
        return []

    results = data.get("d", {}).get("results", []) if isinstance(data.get("d"), dict) else []
    if not results:
        results = data.get("d", []) if isinstance(data.get("d"), list) else []

    events = []
    for item in results:
        status_text = item.get("BusinessStatusName", "")
        modified_raw = item.get("BusinessStatusDate") or item.get("Modified")
        event_date = None
        if modified_raw:
            try:
                if "/Date(" in str(modified_raw):
                    ts = int(str(modified_raw).split("(")[1].split(")")[0].split("+")[0].split("-")[0])
                    event_date = datetime.utcfromtimestamp(ts / 1000)
                else:
                    event_date = datetime.fromisoformat(str(modified_raw).replace("Z", "+00:00"))
            except (ValueError, IndexError):
                pass

        if status_text:
            events.append({
                "event_type": "status_change",
                "event_date": event_date,
                "description": status_text,
            })
    return events


async def fetch_new_businesses(since_date: str) -> list[dict]:
    """Fetch new businesses submitted since a given date (YYYY-MM-DD)."""
    url = f"{BASE}/Business"
    params = {
        "$filter": f"SubmissionDate ge datetime'{since_date}T00:00:00' and Language eq 'DE'",
        "$format": "json",
        "$orderby": "SubmissionDate desc",
        "$top": "100",
    }
    data = await _get(url, params)
    if not data:
        return []

    results = data.get("d", {}).get("results", []) if isinstance(data.get("d"), dict) else []
    out = []
    for item in results:
        nr = item.get("BusinessShortNumber", "")
        parsed = _parse_business(item, nr)
        out.append({"business_number": nr, **parsed})
    return out


# ---------------------------------------------------------------------------
# swissparlpy-based functions for committee & session schedule data
# ---------------------------------------------------------------------------

def _fetch_preconsultations_sync(business_number: str) -> list[dict]:
    """Fetch committee pre-consultations (Vorberatungen) for a business."""
    try:
        data = spp.get_data("Preconsultation", Language="DE", BusinessShortNumber=business_number)
    except Exception as exc:
        logger.warning("swissparlpy Preconsultation query failed: %s", exc)
        return []

    results = []
    for row in data:
        if not row.get("CommitteeName"):
            continue
        results.append({
            "committee_name": row.get("CommitteeName", ""),
            "committee_abbrev": row.get("Abbreviation1") or row.get("Abbreviation", ""),
            "date": row["PreconsultationDate"].isoformat() if row.get("PreconsultationDate") else None,
            "treatment_category": row.get("TreatmentCategory", ""),
            "business_type": row.get("BusinessTypeName", ""),
        })
    return results


def _fetch_session_schedule_sync(business_number: str) -> list[dict]:
    """Fetch plenary session schedule for a business via SubjectBusiness → Subject → Meeting."""
    try:
        sb_data = spp.get_data("SubjectBusiness", Language="DE", BusinessShortNumber=business_number)
    except Exception as exc:
        logger.warning("swissparlpy SubjectBusiness query failed: %s", exc)
        return []

    subject_ids = []
    for row in sb_data:
        subject_ids.append(row["IdSubject"])

    if not subject_ids:
        return []

    results = []
    for sid in subject_ids:
        try:
            subj_data = spp.get_data("Subject", Language="DE", ID=sid)
        except Exception:
            continue
        for subj in subj_data:
            meeting_id = subj.get("IdMeeting")
            if not meeting_id:
                continue
            try:
                mtg_data = spp.get_data("Meeting", Language="DE", ID=meeting_id)
            except Exception:
                continue
            for mtg in mtg_data:
                results.append({
                    "meeting_date": mtg["Date"].isoformat() if mtg.get("Date") else None,
                    "begin": mtg.get("Begin", ""),
                    "council": mtg.get("CouncilName", ""),
                    "council_abbrev": mtg.get("CouncilAbbreviation", ""),
                    "session_name": mtg.get("SessionName", ""),
                    "meeting_order": mtg.get("MeetingOrderText", ""),
                    "location": mtg.get("Location", ""),
                })
    return results


async def fetch_preconsultations(business_number: str) -> list[dict]:
    """Async wrapper: fetch committee pre-consultations for a business."""
    return await asyncio.to_thread(_fetch_preconsultations_sync, business_number)


async def fetch_session_schedule(business_number: str) -> list[dict]:
    """Async wrapper: fetch plenary session schedule for a business."""
    return await asyncio.to_thread(_fetch_session_schedule_sync, business_number)


async def fetch_business_schedule(business_number: str) -> dict:
    """Fetch full schedule info for a business (committees + plenary sessions)."""
    preconsultations, sessions = await asyncio.gather(
        fetch_preconsultations(business_number),
        fetch_session_schedule(business_number),
    )
    return {
        "business_number": business_number,
        "preconsultations": preconsultations,
        "sessions": sessions,
    }
