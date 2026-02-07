"""API endpoints for parliamentarians."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Parliamentarian, User, Voting, Vote
from ..schemas import (
    ParliamentarianDetailOut,
    ParliamentarianOut,
    ParliamentarianStatsOut,
    VoteOut,
)
from ..services.feature_engineering import (
    compute_parliamentarian_stats,
    compute_party_loyalty,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parliamentarians", tags=["parliamentarians"])


@router.get("", response_model=list[ParliamentarianOut])
def list_parliamentarians(
    council_id: Optional[int] = Query(None, description="Filter by council (1=NR, 2=SR)"),
    party: Optional[str] = Query(None, description="Filter by party abbreviation"),
    parl_group: Optional[str] = Query(None, description="Filter by parliamentary group abbreviation"),
    canton: Optional[str] = Query(None, description="Filter by canton abbreviation"),
    search: Optional[str] = Query(None, description="Search by name"),
    active_only: bool = Query(True, description="Only active members"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Parliamentarian)

    if active_only:
        query = query.filter(Parliamentarian.active == True)
    if council_id:
        query = query.filter(Parliamentarian.council_id == council_id)
    if party:
        query = query.filter(Parliamentarian.party_abbreviation == party)
    if parl_group:
        query = query.filter(Parliamentarian.parl_group_abbreviation == parl_group)
    if canton:
        query = query.filter(Parliamentarian.canton_abbreviation == canton)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Parliamentarian.first_name.ilike(search_term))
            | (Parliamentarian.last_name.ilike(search_term))
        )

    return (
        query.order_by(Parliamentarian.last_name, Parliamentarian.first_name)
        .all()
    )


@router.get("/{person_number}", response_model=ParliamentarianDetailOut)
def get_parliamentarian(
    person_number: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parl = (
        db.query(Parliamentarian)
        .filter(Parliamentarian.person_number == person_number)
        .first()
    )
    if not parl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parlamentarier nicht gefunden",
        )
    return parl


@router.get("/{person_number}/votes")
def get_parliamentarian_votes(
    person_number: int,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get voting history for a parliamentarian."""
    # Verify parliamentarian exists
    parl = (
        db.query(Parliamentarian)
        .filter(Parliamentarian.person_number == person_number)
        .first()
    )
    if not parl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parlamentarier nicht gefunden",
        )

    # Get votings with vote details
    votings = (
        db.query(Voting, Vote)
        .join(Vote, Vote.vote_id == Voting.vote_id)
        .filter(Voting.person_number == person_number)
        .order_by(Vote.vote_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for voting, vote in votings:
        results.append({
            "vote_id": vote.vote_id,
            "business_number": vote.business_number,
            "business_title": vote.business_title,
            "subject": vote.subject,
            "vote_date": vote.vote_date.isoformat() if vote.vote_date else None,
            "decision": voting.decision,
            "result": vote.result,
            "council_id": vote.council_id,
        })

    return results


@router.get("/{person_number}/stats", response_model=ParliamentarianStatsOut)
def get_parliamentarian_stats(
    person_number: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get voting statistics for a parliamentarian."""
    parl = (
        db.query(Parliamentarian)
        .filter(Parliamentarian.person_number == person_number)
        .first()
    )
    if not parl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parlamentarier nicht gefunden",
        )

    stats = compute_parliamentarian_stats(person_number, db)
    loyalty = compute_party_loyalty(person_number, db)

    return ParliamentarianStatsOut(
        person_number=person_number,
        total_votes=stats["total_votes"],
        yes_rate=stats["yes_rate"],
        no_rate=stats["no_rate"],
        abstention_rate=stats["abstention_rate"],
        absence_rate=stats["absence_rate"],
        party_loyalty_score=round(loyalty, 3),
        parl_group_loyalty_score=round(loyalty, 3),
    )
