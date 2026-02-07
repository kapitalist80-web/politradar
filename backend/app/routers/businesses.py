import logging
import re
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import SessionLocal, get_db
from ..models import BusinessEvent, TrackedBusiness, User
from ..schemas import BusinessAdd, BusinessDetailOut, BusinessEventOut, BusinessScheduleOut, TrackedBusinessOut
from ..services.parliament_api import fetch_business, fetch_business_schedule, fetch_business_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/businesses", tags=["businesses"])

BUSINESS_NUMBER_RE = re.compile(r"^\d{2}\.\d{3,5}$")


@router.get("", response_model=list[TrackedBusinessOut])
def list_businesses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    businesses = (
        db.query(TrackedBusiness)
        .filter(TrackedBusiness.user_id == user.id)
        .order_by(TrackedBusiness.created_at.desc())
        .all()
    )

    if not businesses:
        return businesses

    # Compute next future event date per business_number
    now = datetime.utcnow()
    biz_numbers = list({b.business_number for b in businesses})
    next_dates = (
        db.query(
            BusinessEvent.business_number,
            func.min(BusinessEvent.event_date).label("next_event_date"),
        )
        .filter(
            BusinessEvent.business_number.in_(biz_numbers),
            BusinessEvent.event_date > now,
        )
        .group_by(BusinessEvent.business_number)
        .all()
    )
    date_map = {row.business_number: row.next_event_date for row in next_dates}

    # Attach next_event_date to each business object
    for biz in businesses:
        biz.next_event_date = date_map.get(biz.business_number)

    return businesses


@router.post("", response_model=TrackedBusinessOut, status_code=status.HTTP_201_CREATED)
async def add_business(
    data: BusinessAdd,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not BUSINESS_NUMBER_RE.match(data.business_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungueltiges Geschaeftsnummer-Format (z.B. 24.3927)",
        )

    exists = (
        db.query(TrackedBusiness)
        .filter(
            TrackedBusiness.user_id == user.id,
            TrackedBusiness.business_number == data.business_number,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Geschaeft wird bereits verfolgt",
        )

    info = await fetch_business(data.business_number)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geschaeft nicht auf parlament.ch gefunden",
        )

    business = TrackedBusiness(
        user_id=user.id,
        business_number=data.business_number,
        title=info.get("title"),
        description=info.get("description"),
        status=info.get("status"),
        business_type=info.get("business_type"),
        author=info.get("author"),
        submitted_text=info.get("submitted_text"),
        reasoning=info.get("reasoning"),
        federal_council_response=info.get("federal_council_response"),
        federal_council_proposal=info.get("federal_council_proposal"),
        first_council=info.get("first_council"),
        submission_date=info.get("submission_date"),
    )
    db.add(business)
    db.flush()

    # Fetch and store initial timeline events from parliament API
    existing_events = (
        db.query(BusinessEvent)
        .filter(BusinessEvent.business_number == data.business_number)
        .count()
    )
    if existing_events == 0:
        status_events = await fetch_business_status(data.business_number)
        for evt in status_events:
            db.add(BusinessEvent(
                business_number=data.business_number,
                event_type=evt["event_type"],
                event_date=evt.get("event_date"),
                description=evt.get("description"),
            ))

    db.commit()
    db.refresh(business)
    return business


async def _backfill_business(business_id: int, business_number: str) -> None:
    """Background task: fetch missing data from parliament API and store in DB."""
    db: Session = SessionLocal()
    try:
        # Backfill events if none exist
        event_count = (
            db.query(BusinessEvent)
            .filter(BusinessEvent.business_number == business_number)
            .count()
        )
        if event_count == 0:
            status_events = await fetch_business_status(business_number)
            for evt in status_events:
                db.add(BusinessEvent(
                    business_number=business_number,
                    event_type=evt["event_type"],
                    event_date=evt.get("event_date"),
                    description=evt.get("description"),
                ))
            if status_events:
                db.commit()

        # Backfill business detail fields if any are missing
        business = db.query(TrackedBusiness).filter(TrackedBusiness.id == business_id).first()
        if not business:
            return

        needs_backfill = not business.author or not business.submitted_text or \
            not business.reasoning or not business.federal_council_proposal or \
            not business.first_council
        if needs_backfill:
            info = await fetch_business(business.business_number)
            if info:
                if info.get("author") and not business.author:
                    business.author = info["author"]
                if info.get("submitted_text") and not business.submitted_text:
                    business.submitted_text = info["submitted_text"]
                if info.get("reasoning") and not business.reasoning:
                    business.reasoning = info["reasoning"]
                if info.get("federal_council_response") and not business.federal_council_response:
                    business.federal_council_response = info["federal_council_response"]
                if info.get("federal_council_proposal") and not business.federal_council_proposal:
                    business.federal_council_proposal = info["federal_council_proposal"]
                if info.get("first_council") and not business.first_council:
                    business.first_council = info["first_council"]
                db.commit()
    except Exception:
        db.rollback()
        logger.exception("Backfill failed for business %s", business_number)
    finally:
        db.close()


@router.get("/{business_id}", response_model=BusinessDetailOut)
def get_business(
    business_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = (
        db.query(TrackedBusiness)
        .filter(TrackedBusiness.id == business_id, TrackedBusiness.user_id == user.id)
        .first()
    )
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nicht gefunden")

    events = (
        db.query(BusinessEvent)
        .filter(BusinessEvent.business_number == business.business_number)
        .order_by(BusinessEvent.event_date.desc())
        .all()
    )

    # Schedule background API sync for missing data (non-blocking)
    background_tasks.add_task(_backfill_business, business.id, business.business_number)

    return {"business": business, "events": events}


@router.get("/{business_id}/schedule", response_model=BusinessScheduleOut)
async def get_business_schedule(
    business_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = (
        db.query(TrackedBusiness)
        .filter(TrackedBusiness.id == business_id, TrackedBusiness.user_id == user.id)
        .first()
    )
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nicht gefunden")

    schedule = await fetch_business_schedule(business.business_number)
    return schedule


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(
    business_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = (
        db.query(TrackedBusiness)
        .filter(TrackedBusiness.id == business_id, TrackedBusiness.user_id == user.id)
        .first()
    )
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nicht gefunden")
    db.delete(business)
    db.commit()
