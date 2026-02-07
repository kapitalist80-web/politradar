"""Vote prediction service.

Phase 1: Statistical approach based on faction tendencies.
Phase 2: ML model with Gradient Boosting (when enough data available).
"""

import logging
import os
from collections import defaultdict
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import (
    CommitteeMembership,
    Parliamentarian,
    ParlGroup,
    Vote,
    VotePrediction,
    Voting,
)
from .feature_engineering import (
    compute_faction_tendency,
    compute_party_loyalty,
)

logger = logging.getLogger(__name__)

MODEL_VERSION = "statistical_v1"

# Try to import ML dependencies (optional)
try:
    import joblib
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

ML_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "ml_models",
    "vote_prediction_model.joblib",
)


def predict_for_business(
    business_number: str,
    business_type: str | None,
    author_parl_group_id: int | None,
    member_person_numbers: list[int],
    db: Session,
) -> dict:
    """Generate vote predictions for a list of parliamentarians on a business.

    Uses statistical approach (faction tendency + individual loyalty scores).
    """
    now = datetime.utcnow()

    # Check for cached predictions
    cached = (
        db.query(VotePrediction)
        .filter(
            VotePrediction.business_number == business_number,
            VotePrediction.model_version == MODEL_VERSION,
        )
        .all()
    )

    cached_map = {c.person_number: c for c in cached}
    # Use cache if recent (< 24 hours)
    if cached and cached[0].prediction_date:
        age_hours = (now - cached[0].prediction_date).total_seconds() / 3600
        if age_hours < 24 and len(cached_map) >= len(member_person_numbers):
            return _format_predictions(cached_map, member_person_numbers, business_number, db)

    # Compute fresh predictions
    # Get all parliamentarians
    parliamentarians = (
        db.query(Parliamentarian)
        .filter(Parliamentarian.person_number.in_(member_person_numbers))
        .all()
    )
    parl_map = {p.person_number: p for p in parliamentarians}

    # Get faction tendencies (cached per faction)
    faction_cache: dict[int, dict] = {}

    predictions = {}
    for pn in member_person_numbers:
        parl = parl_map.get(pn)
        if not parl:
            continue

        pg_id = parl.parl_group_id

        # Get faction tendency
        if pg_id and pg_id not in faction_cache:
            faction_cache[pg_id] = compute_faction_tendency(pg_id, business_type, db)

        faction_tend = faction_cache.get(pg_id, {"yes_rate": 0.5, "no_rate": 0.5})

        # Compute individual loyalty score
        loyalty = compute_party_loyalty(pn, db)

        # If author is from same faction, boost yes probability
        same_faction_boost = 0.0
        if author_parl_group_id and pg_id == author_parl_group_id:
            same_faction_boost = 0.15

        # Combine signals
        base_yes = faction_tend["yes_rate"]
        base_no = faction_tend["no_rate"]

        # Adjust with loyalty and same-faction boost
        predicted_yes = min(1.0, base_yes + same_faction_boost)
        predicted_no = max(0.0, base_no - same_faction_boost)

        # Normalize
        total = predicted_yes + predicted_no
        if total > 0:
            predicted_yes = predicted_yes / total
            predicted_no = predicted_no / total
        else:
            predicted_yes = 0.5
            predicted_no = 0.5

        predicted_abstain = 0.02  # Small baseline

        # Confidence based on data availability
        confidence = min(0.9, loyalty * 0.6 + 0.3) if loyalty > 0 else 0.3

        # Store prediction
        pred = VotePrediction(
            business_number=business_number,
            person_number=pn,
            predicted_yes=round(predicted_yes, 3),
            predicted_no=round(predicted_no, 3),
            predicted_abstain=round(predicted_abstain, 3),
            confidence=round(confidence, 3),
            model_version=MODEL_VERSION,
            prediction_date=now,
        )

        # Upsert
        existing = db.query(VotePrediction).filter(
            VotePrediction.business_number == business_number,
            VotePrediction.person_number == pn,
            VotePrediction.model_version == MODEL_VERSION,
        ).first()

        if existing:
            existing.predicted_yes = pred.predicted_yes
            existing.predicted_no = pred.predicted_no
            existing.predicted_abstain = pred.predicted_abstain
            existing.confidence = pred.confidence
            existing.prediction_date = now
        else:
            db.add(pred)

        predictions[pn] = pred

    db.commit()
    return _format_predictions(predictions, member_person_numbers, business_number, db)


def _format_predictions(
    predictions: dict,
    member_person_numbers: list[int],
    business_number: str,
    db: Session,
) -> dict:
    """Format predictions for API response."""
    # Get parliamentarian info
    parliamentarians = (
        db.query(Parliamentarian)
        .filter(Parliamentarian.person_number.in_(member_person_numbers))
        .all()
    )
    parl_map = {p.person_number: p for p in parliamentarians}

    # Build member predictions
    member_predictions = []
    faction_data = defaultdict(lambda: {"members": 0, "yes_sum": 0.0, "no_sum": 0.0, "name": ""})

    for pn in member_person_numbers:
        pred = predictions.get(pn)
        parl = parl_map.get(pn)

        if not pred:
            continue

        pred_yes = pred.predicted_yes if hasattr(pred, "predicted_yes") else pred.predicted_yes
        pred_no = pred.predicted_no if hasattr(pred, "predicted_no") else pred.predicted_no
        pred_abstain = pred.predicted_abstain if hasattr(pred, "predicted_abstain") else 0.0
        confidence = pred.confidence if hasattr(pred, "confidence") else 0.0

        mp = {
            "person_number": pn,
            "first_name": parl.first_name if parl else None,
            "last_name": parl.last_name if parl else None,
            "party_abbreviation": parl.party_abbreviation if parl else None,
            "parl_group_abbreviation": parl.parl_group_abbreviation if parl else None,
            "canton_abbreviation": parl.canton_abbreviation if parl else None,
            "predicted_yes": pred_yes,
            "predicted_no": pred_no,
            "predicted_abstain": pred_abstain,
            "confidence": confidence,
        }
        member_predictions.append(mp)

        # Aggregate by faction
        if parl and parl.parl_group_abbreviation:
            pg_abbr = parl.parl_group_abbreviation
            faction_data[pg_abbr]["members"] += 1
            faction_data[pg_abbr]["yes_sum"] += pred_yes
            faction_data[pg_abbr]["no_sum"] += pred_no
            faction_data[pg_abbr]["name"] = parl.parl_group_name or pg_abbr

    # Build faction breakdown
    faction_breakdown = []
    for pg_abbr, data in sorted(faction_data.items(), key=lambda x: -x[1]["members"]):
        count = data["members"]
        faction_breakdown.append({
            "parl_group_abbreviation": pg_abbr,
            "parl_group_name": data["name"],
            "member_count": count,
            "avg_yes": round(data["yes_sum"] / count, 3) if count > 0 else 0.0,
            "avg_no": round(data["no_sum"] / count, 3) if count > 0 else 0.0,
        })

    # Overall prediction
    total_members = len(member_predictions)
    if total_members > 0:
        overall_yes = sum(mp["predicted_yes"] for mp in member_predictions) / total_members
    else:
        overall_yes = 0.5

    if overall_yes > 0.6:
        expected_result = "Annahme wahrscheinlich"
    elif overall_yes < 0.4:
        expected_result = "Ablehnung wahrscheinlich"
    else:
        expected_result = "Unsicher"

    return {
        "business_number": business_number,
        "overall_yes_probability": round(overall_yes, 3),
        "expected_result": expected_result,
        "model_version": MODEL_VERSION,
        "disclaimer": "Basierend auf historischem Abstimmungsverhalten und Fraktionszugehörigkeit",
        "faction_breakdown": faction_breakdown,
        "member_predictions": member_predictions,
    }
