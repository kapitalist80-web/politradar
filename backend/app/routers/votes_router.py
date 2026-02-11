"""API endpoints for votes and voting records."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Parliamentarian, User, Vote, Voting
from ..schemas import VoteDetailOut, VoteOut, VotingOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/votes", tags=["votes"])


@router.get("/sessions")
def get_vote_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get distinct sessions that have votes, ordered by most recent."""
    from sqlalchemy import func
    rows = (
        db.query(
            Vote.session_id,
            func.max(Vote.session_name).label("session_name"),
            func.max(Vote.vote_date).label("latest_date"),
        )
        .filter(Vote.session_id.isnot(None), Vote.session_id != "")
        .group_by(Vote.session_id)
        .order_by(func.max(Vote.vote_date).desc())
        .all()
    )
    return [{"session_id": r.session_id, "session_name": r.session_name, "latest_date": r.latest_date} for r in rows]


@router.get("/recent", response_model=list[VoteOut])
def get_recent_votes(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    council_id: int = Query(None),
    session_id: str = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent votes with optional council or session filter."""
    query = db.query(Vote)
    if council_id:
        query = query.filter(Vote.council_id == council_id)
    if session_id:
        query = query.filter(Vote.session_id == session_id)
    return (
        query.order_by(Vote.vote_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{vote_id}", response_model=VoteDetailOut)
def get_vote_detail(
    vote_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get vote details with all individual voting records."""
    vote = db.query(Vote).filter(Vote.vote_id == vote_id).first()
    if not vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abstimmung nicht gefunden",
        )

    # Get individual votings
    votings = (
        db.query(Voting)
        .filter(Voting.vote_id == vote_id)
        .all()
    )

    # Get parliamentarian details
    person_numbers = [v.person_number for v in votings]
    parliamentarians = (
        db.query(Parliamentarian)
        .filter(Parliamentarian.person_number.in_(person_numbers))
        .all()
    ) if person_numbers else []
    parl_map = {p.person_number: p for p in parliamentarians}

    voting_list = []
    for v in votings:
        parl = parl_map.get(v.person_number)
        voting_list.append(VotingOut(
            person_number=v.person_number,
            first_name=parl.first_name if parl else None,
            last_name=parl.last_name if parl else None,
            decision=v.decision,
            party_abbreviation=parl.party_abbreviation if parl else None,
            parl_group_abbreviation=parl.parl_group_abbreviation if parl else None,
            canton_abbreviation=parl.canton_abbreviation if parl else None,
        ))

    return VoteDetailOut(
        id=vote.id,
        vote_id=vote.vote_id,
        business_number=vote.business_number,
        business_title=vote.business_title,
        subject=vote.subject,
        meaning_yes=vote.meaning_yes,
        meaning_no=vote.meaning_no,
        vote_date=vote.vote_date,
        council_id=vote.council_id,
        total_yes=vote.total_yes,
        total_no=vote.total_no,
        total_abstain=vote.total_abstain,
        total_not_voted=vote.total_not_voted,
        result=vote.result,
        votings=voting_list,
    )
