from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Business ---
class BusinessAdd(BaseModel):
    business_number: str


class TrackedBusinessOut(BaseModel):
    id: int
    business_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    business_type: Optional[str] = None
    author: Optional[str] = None
    author_faction: Optional[str] = None
    submitted_text: Optional[str] = None
    reasoning: Optional[str] = None
    federal_council_response: Optional[str] = None
    federal_council_proposal: Optional[str] = None
    first_council: Optional[str] = None
    submission_date: Optional[datetime] = None
    next_event_date: Optional[datetime] = None
    last_api_sync: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BusinessEventOut(BaseModel):
    id: int
    business_number: str
    event_type: str
    event_date: Optional[datetime] = None
    description: Optional[str] = None
    committee_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BusinessDetailOut(BaseModel):
    business: TrackedBusinessOut
    events: list[BusinessEventOut]


# --- Alerts ---
class AlertOut(BaseModel):
    id: int
    business_number: str
    business_title: Optional[str] = None
    alert_type: str
    message: str
    event_date: Optional[datetime] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Monitoring ---
class MonitoringCandidateOut(BaseModel):
    id: int
    business_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    business_type: Optional[str] = None
    submission_date: Optional[datetime] = None
    decision: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MonitoringDecision(BaseModel):
    decision: str  # "accepted" or "rejected"


# --- Business Cache ---
class BusinessCacheItem(BaseModel):
    business_number: str
    title: str = ""


# --- Parliament Preview ---
class ParliamentPreview(BaseModel):
    business_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    business_type: Optional[str] = None
    status: Optional[str] = None
    submission_date: Optional[str] = None


# --- Schedule ---
class PreconsultationOut(BaseModel):
    committee_name: str
    committee_abbrev: Optional[str] = None
    date: Optional[str] = None
    treatment_category: Optional[str] = None
    business_type: Optional[str] = None


class SessionScheduleOut(BaseModel):
    meeting_date: Optional[str] = None
    begin: Optional[str] = None
    council: Optional[str] = None
    council_abbrev: Optional[str] = None
    session_name: Optional[str] = None
    meeting_order: Optional[str] = None
    location: Optional[str] = None


class BusinessScheduleOut(BaseModel):
    business_number: str
    preconsultations: list[PreconsultationOut] = []
    sessions: list[SessionScheduleOut] = []


# --- Email Settings ---
class EmailSettingsOut(BaseModel):
    email_alerts_enabled: bool = False
    email_alert_types: list[str] = []

    model_config = {"from_attributes": True}


class EmailSettingsUpdate(BaseModel):
    email_alerts_enabled: bool
    email_alert_types: list[str]
