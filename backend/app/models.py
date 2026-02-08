from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    email_alerts_enabled = Column(Boolean, default=False)
    email_alert_types = Column(String(500), default="status_change,committee_scheduled,debate_scheduled")
    created_at = Column(DateTime, default=datetime.utcnow)

    tracked_businesses = relationship("TrackedBusiness", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class TrackedBusiness(Base):
    __tablename__ = "tracked_businesses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_number = Column(String(20), nullable=False, index=True)
    title = Column(String(500))
    description = Column(Text)
    status = Column(String(100))
    business_type = Column(String(100))
    author = Column(String(500))
    author_faction = Column(String(255))
    submitted_text = Column(Text)
    reasoning = Column(Text)
    federal_council_response = Column(Text)
    federal_council_proposal = Column(String(200))
    first_council = Column(String(100))
    submission_date = Column(DateTime)
    last_api_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tracked_businesses")


class BusinessEvent(Base):
    __tablename__ = "business_events"

    id = Column(Integer, primary_key=True, index=True)
    business_number = Column(String(20), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    event_date = Column(DateTime)
    description = Column(Text)
    committee_name = Column(String(255))
    raw_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_number = Column(String(20), nullable=False)
    alert_type = Column(
        Enum(
            "status_change",
            "committee_scheduled",
            "debate_scheduled",
            "new_document",
            "vote_result",
            name="alert_type_enum",
        ),
        nullable=False,
    )
    message = Column(Text, nullable=False)
    event_date = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class MonitoringCandidate(Base):
    __tablename__ = "monitoring_candidates"

    id = Column(Integer, primary_key=True, index=True)
    business_number = Column(String(20), nullable=False, unique=True)
    title = Column(String(500))
    description = Column(Text)
    business_type = Column(String(100))
    submission_date = Column(DateTime)
    decision = Column(
        Enum("pending", "accepted", "rejected", name="decision_enum"),
        default="pending",
    )
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Parlamentarier-Profile & Abstimmungsprognose ---


class Canton(Base):
    __tablename__ = "cantons"

    id = Column(Integer, primary_key=True, index=True)
    canton_number = Column(Integer, unique=True, nullable=False)
    canton_name = Column(String(100))
    canton_abbreviation = Column(String(5))


class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, index=True)
    party_number = Column(Integer, unique=True, nullable=False)
    party_name = Column(String(255))
    party_abbreviation = Column(String(50))
    program_summary = Column(Text)
    political_position = Column(JSONB)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ParlGroup(Base):
    __tablename__ = "parl_groups"

    id = Column(Integer, primary_key=True, index=True)
    parl_group_number = Column(Integer, unique=True, nullable=False)
    parl_group_name = Column(String(255))
    parl_group_abbreviation = Column(String(50))
    associated_parties = Column(Text)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Parliamentarian(Base):
    __tablename__ = "parliamentarians"

    id = Column(Integer, primary_key=True, index=True)
    person_number = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    gender = Column(String(10))
    date_of_birth = Column(Date)
    canton_id = Column(Integer)
    canton_name = Column(String(100))
    canton_abbreviation = Column(String(5))
    council_id = Column(Integer)
    council_name = Column(String(100))
    party_id = Column(Integer)
    party_name = Column(String(255))
    party_abbreviation = Column(String(50))
    parl_group_id = Column(Integer)
    parl_group_name = Column(String(255))
    parl_group_abbreviation = Column(String(50))
    active = Column(Boolean, default=True)
    membership_start = Column(Date)
    membership_end = Column(Date)
    biografie_url = Column(String(500))
    photo_url = Column(String(500))
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Committee(Base):
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True, index=True)
    committee_number = Column(Integer, unique=True, nullable=False)
    committee_name = Column(String(500))
    committee_abbreviation = Column(String(50))
    council_id = Column(Integer)
    committee_type = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommitteeMembership(Base):
    __tablename__ = "committee_memberships"

    id = Column(Integer, primary_key=True, index=True)
    person_number = Column(Integer, nullable=False)
    committee_id = Column(Integer, nullable=False)
    committee_name = Column(String(500))
    committee_abbreviation = Column(String(50))
    council_id = Column(Integer)
    function = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("person_number", "committee_id", "start_date", name="uq_committee_membership"),
    )


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    vote_id = Column(Integer, unique=True, nullable=False)
    business_number = Column(String(20))
    business_title = Column(String(500))
    subject = Column(Text)
    meaning_yes = Column(Text)
    meaning_no = Column(Text)
    vote_date = Column(DateTime)
    council_id = Column(Integer)
    session_id = Column(String(50))
    total_yes = Column(Integer)
    total_no = Column(Integer)
    total_abstain = Column(Integer)
    total_not_voted = Column(Integer)
    result = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Voting(Base):
    __tablename__ = "votings"

    id = Column(Integer, primary_key=True, index=True)
    vote_id = Column(Integer, nullable=False)
    person_number = Column(Integer, nullable=False)
    decision = Column(String(20), nullable=False)
    parl_group_number = Column(Integer)
    canton_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("vote_id", "person_number", name="uq_voting"),
        Index("idx_votings_person", "person_number"),
        Index("idx_votings_vote", "vote_id"),
        Index("idx_votings_decision", "decision"),
    )


class CachedBusiness(Base):
    __tablename__ = "cached_businesses"

    id = Column(Integer, primary_key=True, index=True)
    business_number = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class VotePrediction(Base):
    __tablename__ = "vote_predictions"

    id = Column(Integer, primary_key=True, index=True)
    business_number = Column(String(20), nullable=False)
    person_number = Column(Integer, nullable=False)
    predicted_yes = Column(Float)
    predicted_no = Column(Float)
    predicted_abstain = Column(Float)
    confidence = Column(Float)
    model_version = Column(String(50))
    prediction_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("business_number", "person_number", "model_version", name="uq_vote_prediction"),
    )
