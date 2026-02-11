import logging
import re
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import SessionLocal, get_db
from ..models import BusinessEvent, BusinessNote, CachedBusiness, TrackedBusiness, User
from ..schemas import BusinessAdd, BusinessDetailOut, BusinessEventOut, BusinessNoteCreate, BusinessNoteOut, BusinessPriorityUpdate, BusinessScheduleOut, TrackedBusinessOut
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
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not BUSINESS_NUMBER_RE.match(data.business_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiges Geschäftsnummer-Format (z.B. 24.3927)",
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
            detail="Geschäft wird bereits verfolgt",
        )

    # Use cached title if available for instant response
    cached = (
        db.query(CachedBusiness)
        .filter(CachedBusiness.business_number == data.business_number)
        .first()
    )

    business = TrackedBusiness(
        user_id=user.id,
        business_number=data.business_number,
        title=cached.title if cached else data.business_number,
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    # Fetch full details and events from API in background
    background_tasks.add_task(_backfill_business, business.id, data.business_number)

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

        info = await fetch_business(business.business_number)
        if info:
            for field in ("title", "author", "author_faction", "submitted_text",
                          "reasoning", "federal_council_response",
                          "federal_council_proposal", "first_council",
                          "description", "status", "business_type"):
                val = info.get(field)
                if val and not getattr(business, field, None):
                    setattr(business, field, val)
            business.last_api_sync = datetime.utcnow()
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

    # Only backfill if data is missing and not recently synced (< 24h)
    needs_backfill = not business.title or not business.author or not business.status
    recently_synced = (
        business.last_api_sync
        and (datetime.utcnow() - business.last_api_sync).total_seconds() < 86400
    )
    if needs_backfill and not recently_synced:
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


@router.patch("/{business_id}/priority")
def update_priority(
    business_id: int,
    data: BusinessPriorityUpdate,
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
    if data.priority is not None and data.priority not in (1, 2, 3):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priorität muss 1, 2 oder 3 sein",
        )
    business.priority = data.priority
    db.commit()
    db.refresh(business)
    return {"id": business.id, "priority": business.priority}


@router.get("/{business_id}/notes", response_model=list[BusinessNoteOut])
def get_business_notes(
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
    notes = (
        db.query(BusinessNote)
        .filter(BusinessNote.business_id == business_id)
        .order_by(BusinessNote.created_at.desc())
        .all()
    )
    result = []
    for note in notes:
        note_user = db.query(User).filter(User.id == note.user_id).first()
        result.append(BusinessNoteOut(
            id=note.id,
            content=note.content,
            user_name=note_user.name if note_user else None,
            created_at=note.created_at,
        ))
    return result


@router.post("/{business_id}/notes", response_model=BusinessNoteOut, status_code=status.HTTP_201_CREATED)
def add_business_note(
    business_id: int,
    data: BusinessNoteCreate,
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
    note = BusinessNote(
        business_id=business_id,
        user_id=user.id,
        content=data.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return BusinessNoteOut(
        id=note.id,
        content=note.content,
        user_name=user.name,
        created_at=note.created_at,
    )
