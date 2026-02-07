from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import MonitoringCandidate, User
from ..schemas import MonitoringCandidateOut, MonitoringDecision

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/business-types")
def list_business_types(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all distinct business_type values present in monitoring candidates."""
    rows = (
        db.query(distinct(MonitoringCandidate.business_type))
        .filter(MonitoringCandidate.business_type.isnot(None))
        .order_by(MonitoringCandidate.business_type)
        .all()
    )
    return [r[0] for r in rows if r[0]]


@router.get("", response_model=list[MonitoringCandidateOut])
def list_candidates(
    decision: str = Query("pending"),
    business_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(MonitoringCandidate)
    if decision:
        q = q.filter(MonitoringCandidate.decision == decision)
    if business_type:
        q = q.filter(MonitoringCandidate.business_type == business_type)
    return (
        q.order_by(MonitoringCandidate.submission_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.patch("/{candidate_id}", response_model=MonitoringCandidateOut)
def decide(
    candidate_id: int,
    body: MonitoringDecision,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.decision not in ("accepted", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Entscheidung muss 'accepted' oder 'rejected' sein",
        )

    candidate = db.query(MonitoringCandidate).filter(MonitoringCandidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nicht gefunden")

    candidate.decision = body.decision
    candidate.decided_by = user.id
    candidate.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(candidate)
    return candidate
