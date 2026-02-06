import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import BusinessEvent, TrackedBusiness, User
from ..schemas import BusinessAdd, BusinessDetailOut, BusinessEventOut, TrackedBusinessOut
from ..services.parliament_api import fetch_business, fetch_business_status

router = APIRouter(prefix="/api/businesses", tags=["businesses"])

BUSINESS_NUMBER_RE = re.compile(r"^\d{2}\.\d{3,5}$")


@router.get("", response_model=list[TrackedBusinessOut])
def list_businesses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(TrackedBusiness)
        .filter(TrackedBusiness.user_id == user.id)
        .order_by(TrackedBusiness.created_at.desc())
        .all()
    )


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


@router.get("/{business_id}", response_model=BusinessDetailOut)
async def get_business(
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

    events = (
        db.query(BusinessEvent)
        .filter(BusinessEvent.business_number == business.business_number)
        .order_by(BusinessEvent.event_date.desc())
        .all()
    )

    # If no events in DB, try to fetch from parliament API
    if not events:
        status_events = await fetch_business_status(business.business_number)
        for evt in status_events:
            db.add(BusinessEvent(
                business_number=business.business_number,
                event_type=evt["event_type"],
                event_date=evt.get("event_date"),
                description=evt.get("description"),
            ))
        if status_events:
            db.commit()
            events = (
                db.query(BusinessEvent)
                .filter(BusinessEvent.business_number == business.business_number)
                .order_by(BusinessEvent.event_date.desc())
                .all()
            )

    # Backfill author if missing
    if not getattr(business, "author", None):
        info = await fetch_business(business.business_number)
        if info and info.get("author"):
            try:
                business.author = info["author"]
                db.commit()
                db.refresh(business)
            except Exception:
                db.rollback()

    return {"business": business, "events": events}


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
