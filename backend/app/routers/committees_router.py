"""API endpoints for committees."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Committee, CommitteeMembership, Parliamentarian, User
from ..schemas import CommitteeDetailOut, CommitteeMemberOut, CommitteeOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/committees", tags=["committees"])


@router.get("", response_model=list[CommitteeOut])
def list_committees(
    council_id: Optional[int] = Query(None, description="Filter by council"),
    active_only: bool = Query(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Committee)
    if active_only:
        query = query.filter(Committee.is_active == True)
    if council_id:
        query = query.filter(Committee.council_id == council_id)
    return query.order_by(Committee.committee_name).all()


@router.get("/{committee_number}/members", response_model=CommitteeDetailOut)
def get_committee_members(
    committee_number: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get committee details with current members."""
    committee = (
        db.query(Committee)
        .filter(Committee.committee_number == committee_number)
        .first()
    )
    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kommission nicht gefunden",
        )

    # Get active memberships
    memberships = (
        db.query(CommitteeMembership)
        .filter(
            CommitteeMembership.committee_id == committee_number,
            CommitteeMembership.is_active == True,
        )
        .all()
    )

    # Get parliamentarian details for members
    person_numbers = [m.person_number for m in memberships]
    parliamentarians = (
        db.query(Parliamentarian)
        .filter(Parliamentarian.person_number.in_(person_numbers))
        .all()
    ) if person_numbers else []
    parl_map = {p.person_number: p for p in parliamentarians}

    members = []
    for m in memberships:
        parl = parl_map.get(m.person_number)
        members.append(CommitteeMemberOut(
            person_number=m.person_number,
            first_name=parl.first_name if parl else None,
            last_name=parl.last_name if parl else None,
            party_abbreviation=parl.party_abbreviation if parl else None,
            parl_group_abbreviation=parl.parl_group_abbreviation if parl else None,
            canton_abbreviation=parl.canton_abbreviation if parl else None,
            function=m.function,
            photo_url=parl.photo_url if parl else None,
        ))

    return CommitteeDetailOut(
        id=committee.id,
        committee_number=committee.committee_number,
        committee_name=committee.committee_name,
        committee_abbreviation=committee.committee_abbreviation,
        council_id=committee.council_id,
        committee_type=committee.committee_type,
        is_active=committee.is_active,
        members=members,
    )


# Council members endpoint
councils_router = APIRouter(prefix="/api/councils", tags=["councils"])


@councils_router.get("/{council_id}/members")
def get_council_members(
    council_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all active members of a council (1=NR, 2=SR)."""
    members = (
        db.query(Parliamentarian)
        .filter(
            Parliamentarian.council_id == council_id,
            Parliamentarian.active == True,
        )
        .order_by(Parliamentarian.last_name, Parliamentarian.first_name)
        .all()
    )
    return [
        CommitteeMemberOut(
            person_number=m.person_number,
            first_name=m.first_name,
            last_name=m.last_name,
            party_abbreviation=m.party_abbreviation,
            parl_group_abbreviation=m.parl_group_abbreviation,
            canton_abbreviation=m.canton_abbreviation,
            function=None,
            photo_url=m.photo_url,
        )
        for m in members
    ]


# Parties and parliamentary groups endpoints
parties_router = APIRouter(prefix="/api/parties", tags=["parties"])
parl_groups_router = APIRouter(prefix="/api/parl-groups", tags=["parl-groups"])


@parties_router.get("")
def list_parties(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..models import Party
    return db.query(Party).order_by(Party.party_name).all()


@parl_groups_router.get("")
def list_parl_groups(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..models import ParlGroup
    return db.query(ParlGroup).order_by(ParlGroup.parl_group_name).all()
