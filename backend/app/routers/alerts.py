from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Alert, TrackedBusiness, User
from ..schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Alert types where only future events are relevant
_SCHEDULED_TYPES = {"committee_scheduled", "debate_scheduled"}


def _attach_business_titles(alerts: list[Alert], user_id: int, db: Session) -> list[dict]:
    """Look up business titles for a list of alerts and return dicts with business_title."""
    biz_numbers = list({a.business_number for a in alerts})
    title_map: dict[str, str] = {}
    if biz_numbers:
        rows = (
            db.query(TrackedBusiness.business_number, TrackedBusiness.title)
            .filter(
                TrackedBusiness.user_id == user_id,
                TrackedBusiness.business_number.in_(biz_numbers),
            )
            .all()
        )
        for row in rows:
            title_map[row.business_number] = row.title or ""

    result = []
    for a in alerts:
        d = {
            "id": a.id,
            "business_number": a.business_number,
            "business_title": title_map.get(a.business_number, ""),
            "alert_type": a.alert_type,
            "message": a.message,
            "event_date": a.event_date,
            "is_read": a.is_read,
            "created_at": a.created_at,
        }
        result.append(d)
    return result


@router.get("", response_model=list[AlertOut])
def list_alerts(
    alert_type: str | None = Query(None),
    is_read: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Alert).filter(Alert.user_id == user.id)
    if alert_type:
        q = q.filter(Alert.alert_type == alert_type)
    if is_read is not None:
        q = q.filter(Alert.is_read == is_read)

    # Only show scheduled alerts (committee/debate) whose event is in the future.
    # Non-scheduled types (status_change, new_document, vote_result) are always shown.
    today = datetime.combine(date.today(), datetime.min.time())
    q = q.filter(
        or_(
            Alert.alert_type.notin_(_SCHEDULED_TYPES),
            Alert.event_date >= today,
            Alert.event_date.is_(None),
        )
    )

    alerts = q.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return _attach_business_titles(alerts, user.id, db)


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_read(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.user_id == user.id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nicht gefunden")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    result = _attach_business_titles([alert], user.id, db)
    return result[0]


@router.post("/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Alert).filter(Alert.user_id == user.id, Alert.is_read == False).update(
        {"is_read": True}
    )
    db.commit()
    return {"detail": "Alle Alerts als gelesen markiert"}
