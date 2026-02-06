from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
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
    submitted_text = Column(Text)
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
