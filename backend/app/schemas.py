from datetime import date, datetime
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


class BusinessPriorityUpdate(BaseModel):
    priority: Optional[int] = None  # 1, 2, 3, or null


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
    priority: Optional[int] = None
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


# --- Business Notes ---
class BusinessNoteCreate(BaseModel):
    content: str


class BusinessNoteOut(BaseModel):
    id: int
    content: str
    user_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


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


# --- Parliamentarians ---
class ParliamentarianOut(BaseModel):
    id: int
    person_number: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    canton_name: Optional[str] = None
    canton_abbreviation: Optional[str] = None
    council_id: Optional[int] = None
    council_name: Optional[str] = None
    party_name: Optional[str] = None
    party_abbreviation: Optional[str] = None
    parl_group_name: Optional[str] = None
    parl_group_abbreviation: Optional[str] = None
    active: bool = True
    photo_url: Optional[str] = None
    biografie_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ParliamentarianDetailOut(ParliamentarianOut):
    date_of_birth: Optional[date] = None
    canton_id: Optional[int] = None
    party_id: Optional[int] = None
    parl_group_id: Optional[int] = None
    membership_start: Optional[date] = None
    membership_end: Optional[date] = None
    last_sync: Optional[datetime] = None


class ParliamentarianStatsOut(BaseModel):
    person_number: int
    total_votes: int = 0
    yes_rate: float = 0.0
    no_rate: float = 0.0
    abstention_rate: float = 0.0
    absence_rate: float = 0.0
    party_loyalty_score: float = 0.0
    parl_group_loyalty_score: float = 0.0


# --- Parties ---
class PartyOut(BaseModel):
    id: int
    party_number: int
    party_name: Optional[str] = None
    party_abbreviation: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Parliamentary Groups ---
class ParlGroupOut(BaseModel):
    id: int
    parl_group_number: int
    parl_group_name: Optional[str] = None
    parl_group_abbreviation: Optional[str] = None
    associated_parties: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Committees ---
class CommitteeOut(BaseModel):
    id: int
    committee_number: int
    committee_name: Optional[str] = None
    committee_abbreviation: Optional[str] = None
    council_id: Optional[int] = None
    committee_type: Optional[str] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class CommitteeMemberOut(BaseModel):
    person_number: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    party_abbreviation: Optional[str] = None
    parl_group_abbreviation: Optional[str] = None
    canton_abbreviation: Optional[str] = None
    function: Optional[str] = None
    photo_url: Optional[str] = None


class CommitteeDetailOut(CommitteeOut):
    members: list[CommitteeMemberOut] = []


# --- Votes ---
class VoteOut(BaseModel):
    id: int
    vote_id: int
    business_number: Optional[str] = None
    business_title: Optional[str] = None
    subject: Optional[str] = None
    meaning_yes: Optional[str] = None
    meaning_no: Optional[str] = None
    vote_date: Optional[datetime] = None
    council_id: Optional[int] = None
    total_yes: Optional[int] = None
    total_no: Optional[int] = None
    total_abstain: Optional[int] = None
    total_not_voted: Optional[int] = None
    result: Optional[str] = None

    model_config = {"from_attributes": True}


class VotingOut(BaseModel):
    person_number: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    decision: str
    party_abbreviation: Optional[str] = None
    parl_group_abbreviation: Optional[str] = None
    canton_abbreviation: Optional[str] = None


class VoteDetailOut(VoteOut):
    votings: list[VotingOut] = []


# --- Vote Predictions ---
class PredictionMemberOut(BaseModel):
    person_number: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    party_abbreviation: Optional[str] = None
    parl_group_abbreviation: Optional[str] = None
    canton_abbreviation: Optional[str] = None
    predicted_yes: float = 0.0
    predicted_no: float = 0.0
    predicted_abstain: float = 0.0
    confidence: float = 0.0


class FactionPredictionOut(BaseModel):
    parl_group_abbreviation: str
    parl_group_name: str
    member_count: int
    avg_yes: float = 0.0
    avg_no: float = 0.0


class VotePredictionOut(BaseModel):
    business_number: str
    committee_name: Optional[str] = None
    committee_abbreviation: Optional[str] = None
    overall_yes_probability: float = 0.0
    expected_result: str = "Unsicher"
    model_version: Optional[str] = None
    disclaimer: str = "Basierend auf historischem Abstimmungsverhalten und Fraktionszugehörigkeit"
    faction_breakdown: list[FactionPredictionOut] = []
    member_predictions: list[PredictionMemberOut] = []


# --- Treating Body ---
class TreatingBodyOut(BaseModel):
    business_number: str
    next_body_name: Optional[str] = None
    next_body_abbreviation: Optional[str] = None
    next_body_type: Optional[str] = None  # "committee" or "council"
    next_date: Optional[str] = None
    members: list[CommitteeMemberOut] = []
