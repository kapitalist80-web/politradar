"""Feature engineering for vote prediction ML model.

Computes features for each parliamentarian x business combination.
"""

import logging
from collections import Counter

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Parliamentarian, Vote, Voting

logger = logging.getLogger(__name__)


def compute_party_loyalty(person_number: int, db: Session) -> float:
    """Compute how often a parliamentarian votes with their parliamentary group majority."""
    # Get the parliamentarian's current parl group
    parl = db.query(Parliamentarian).filter(
        Parliamentarian.person_number == person_number
    ).first()
    if not parl or not parl.parl_group_id:
        return 0.0

    parl_group_number = parl.parl_group_id

    # Get all votes where this person participated
    person_votings = (
        db.query(Voting.vote_id, Voting.decision)
        .filter(
            Voting.person_number == person_number,
            Voting.decision.in_(["Yes", "No"]),
        )
        .all()
    )

    if not person_votings:
        return 0.0

    agreements = 0
    total = 0

    for vote_id, person_decision in person_votings:
        # Get the majority decision of the parliamentary group for this vote
        group_decisions = (
            db.query(Voting.decision, func.count(Voting.id))
            .filter(
                Voting.vote_id == vote_id,
                Voting.parl_group_number == parl_group_number,
                Voting.decision.in_(["Yes", "No"]),
            )
            .group_by(Voting.decision)
            .all()
        )

        if not group_decisions:
            continue

        # Find majority decision
        majority_decision = max(group_decisions, key=lambda x: x[1])[0]
        total += 1
        if person_decision == majority_decision:
            agreements += 1

    return agreements / total if total > 0 else 0.0


def compute_parliamentarian_stats(person_number: int, db: Session) -> dict:
    """Compute voting statistics for a parliamentarian."""
    votings = (
        db.query(Voting.decision)
        .filter(Voting.person_number == person_number)
        .all()
    )

    total = len(votings)
    if total == 0:
        return {
            "total_votes": 0,
            "yes_rate": 0.0,
            "no_rate": 0.0,
            "abstention_rate": 0.0,
            "absence_rate": 0.0,
        }

    counts = Counter(v.decision for v in votings)

    yes_count = counts.get("Yes", 0)
    no_count = counts.get("No", 0)
    abstention_count = counts.get("Abstention", 0)
    absent_count = counts.get("Absent", 0)
    president_count = counts.get("President", 0)

    # Exclude president votes from the total for rates
    effective_total = total - president_count
    if effective_total == 0:
        return {
            "total_votes": total,
            "yes_rate": 0.0,
            "no_rate": 0.0,
            "abstention_rate": 0.0,
            "absence_rate": 0.0,
        }

    return {
        "total_votes": total,
        "yes_rate": round(yes_count / effective_total, 3),
        "no_rate": round(no_count / effective_total, 3),
        "abstention_rate": round(abstention_count / effective_total, 3),
        "absence_rate": round(absent_count / effective_total, 3),
    }


def compute_agreement_with_party(
    person_number: int, target_parl_group_number: int, db: Session
) -> float:
    """Compute historical agreement rate between a parliamentarian and a specific parliamentary group."""
    person_votings = (
        db.query(Voting.vote_id, Voting.decision)
        .filter(
            Voting.person_number == person_number,
            Voting.decision.in_(["Yes", "No"]),
        )
        .all()
    )

    if not person_votings:
        return 0.0

    agreements = 0
    total = 0

    for vote_id, person_decision in person_votings:
        # Get majority decision of target group
        group_decisions = (
            db.query(Voting.decision, func.count(Voting.id))
            .filter(
                Voting.vote_id == vote_id,
                Voting.parl_group_number == target_parl_group_number,
                Voting.decision.in_(["Yes", "No"]),
            )
            .group_by(Voting.decision)
            .all()
        )

        if not group_decisions:
            continue

        majority_decision = max(group_decisions, key=lambda x: x[1])[0]
        total += 1
        if person_decision == majority_decision:
            agreements += 1

    return agreements / total if total > 0 else 0.0


def compute_faction_tendency(
    parl_group_number: int,
    business_type: str | None,
    db: Session,
) -> dict:
    """Statistical approach: compute how a faction typically votes on a given business type.

    Returns dict with yes_rate, no_rate for the faction.
    """
    # Get votes related to this business type if available
    query = (
        db.query(Voting.decision, func.count(Voting.id))
        .filter(
            Voting.parl_group_number == parl_group_number,
            Voting.decision.in_(["Yes", "No"]),
        )
    )

    # If business type is provided, filter by votes on businesses of that type
    if business_type:
        vote_ids_subq = (
            db.query(Vote.vote_id)
            .filter(Vote.business_number.isnot(None))
            .subquery()
        )
        query = query.filter(Voting.vote_id.in_(
            db.query(vote_ids_subq.c.vote_id)
        ))

    results = query.group_by(Voting.decision).all()

    if not results:
        return {"yes_rate": 0.5, "no_rate": 0.5}

    total = sum(r[1] for r in results)
    rates = {}
    for decision, count in results:
        rates[decision] = count / total if total > 0 else 0.0

    return {
        "yes_rate": round(rates.get("Yes", 0.0), 3),
        "no_rate": round(rates.get("No", 0.0), 3),
    }
