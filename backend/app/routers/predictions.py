"""API endpoints for vote predictions and treating body."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import (
    Committee,
    CommitteeMembership,
    Parliamentarian,
    TrackedBusiness,
    User,
)
from ..schemas import (
    CommitteeMemberOut,
    TreatingBodyOut,
    VotePredictionOut,
)
from ..services.parliament_api import fetch_preconsultations
from ..services.prediction_service import predict_for_business

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/businesses", tags=["predictions"])


@router.get("/{business_id}/treating-body", response_model=TreatingBodyOut)
async def get_treating_body(
    business_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the next treating body (committee/council) for a business with members."""
    business = (
        db.query(TrackedBusiness)
        .filter(TrackedBusiness.id == business_id, TrackedBusiness.user_id == user.id)
        .first()
    )
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geschaeft nicht gefunden",
        )

    # Fetch preconsultations from parliament API
    preconsultations = await fetch_preconsultations(business.business_number)

    # Find the next treating body
    next_body_name = None
    next_body_abbr = None
    next_date = None
    next_body_type = None
    committee_number = None

    if preconsultations:
        # Sort by date, find the most relevant (upcoming or most recent)
        for pc in sorted(preconsultations, key=lambda x: x.get("date") or "", reverse=True):
            next_body_name = pc.get("committee_name")
            next_body_abbr = pc.get("committee_abbrev")
            next_date = pc.get("date")
            next_body_type = "committee"
            break

    # Find committee number from our DB
    members = []
    if next_body_name:
        committee = (
            db.query(Committee)
            .filter(Committee.committee_name == next_body_name)
            .first()
        )
        if not committee and next_body_abbr:
            committee = (
                db.query(Committee)
                .filter(Committee.committee_abbreviation == next_body_abbr)
                .first()
            )

        if committee:
            committee_number = committee.committee_number
            # Get members
            memberships = (
                db.query(CommitteeMembership)
                .filter(
                    CommitteeMembership.committee_id == committee_number,
                    CommitteeMembership.is_active == True,
                )
                .all()
            )
            person_numbers = [m.person_number for m in memberships]
            if person_numbers:
                parliamentarians = (
                    db.query(Parliamentarian)
                    .filter(Parliamentarian.person_number.in_(person_numbers))
                    .all()
                )
                parl_map = {p.person_number: p for p in parliamentarians}

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

    return TreatingBodyOut(
        business_number=business.business_number,
        next_body_name=next_body_name,
        next_body_abbreviation=next_body_abbr,
        next_body_type=next_body_type,
        next_date=next_date,
        members=members,
    )


@router.get("/{business_id}/vote-prediction", response_model=VotePredictionOut)
async def get_vote_prediction(
    business_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get vote prediction for a business based on treating body members."""
    business = (
        db.query(TrackedBusiness)
        .filter(TrackedBusiness.id == business_id, TrackedBusiness.user_id == user.id)
        .first()
    )
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geschaeft nicht gefunden",
        )

    # First determine the treating body
    preconsultations = await fetch_preconsultations(business.business_number)

    committee_name = None
    committee_abbr = None
    member_person_numbers = []

    if preconsultations:
        for pc in sorted(preconsultations, key=lambda x: x.get("date") or "", reverse=True):
            committee_name = pc.get("committee_name")
            committee_abbr = pc.get("committee_abbrev")
            break

    if committee_name:
        # Find committee and its members
        committee = (
            db.query(Committee)
            .filter(Committee.committee_name == committee_name)
            .first()
        )
        if not committee and committee_abbr:
            committee = (
                db.query(Committee)
                .filter(Committee.committee_abbreviation == committee_abbr)
                .first()
            )

        if committee:
            memberships = (
                db.query(CommitteeMembership)
                .filter(
                    CommitteeMembership.committee_id == committee.committee_number,
                    CommitteeMembership.is_active == True,
                )
                .all()
            )
            member_person_numbers = [m.person_number for m in memberships]

    if not member_person_numbers:
        # Fallback: use all active parliamentarians in the relevant council
        council_id = None
        if business.first_council:
            if "national" in business.first_council.lower():
                council_id = 1
            elif "staende" in business.first_council.lower() or "ständ" in business.first_council.lower():
                council_id = 2

        if council_id:
            members = (
                db.query(Parliamentarian)
                .filter(
                    Parliamentarian.council_id == council_id,
                    Parliamentarian.active == True,
                )
                .all()
            )
            member_person_numbers = [m.person_number for m in members]

    if not member_person_numbers:
        return VotePredictionOut(
            business_number=business.business_number,
            committee_name=committee_name,
            committee_abbreviation=committee_abbr,
            disclaimer="Keine Mitglieder gefunden. Bitte Parlamentarier-Daten synchronisieren.",
        )

    # Determine author's parliamentary group
    author_parl_group_id = None
    if business.author_faction:
        from ..models import ParlGroup
        pg = (
            db.query(ParlGroup)
            .filter(ParlGroup.parl_group_name == business.author_faction)
            .first()
        )
        if pg:
            author_parl_group_id = pg.parl_group_number

    # Generate predictions
    prediction = predict_for_business(
        business_number=business.business_number,
        business_type=business.business_type,
        author_parl_group_id=author_parl_group_id,
        member_person_numbers=member_person_numbers,
        db=db,
    )

    prediction["committee_name"] = committee_name
    prediction["committee_abbreviation"] = committee_abbr

    return prediction
