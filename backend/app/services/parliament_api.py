import logging
import time
from datetime import datetime

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

BASE = settings.PARLIAMENT_API_BASE
TIMEOUT = 30.0
MAX_RETRIES = 3


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
    return _parse_business(item, business_number)


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
