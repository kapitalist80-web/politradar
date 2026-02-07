from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..schemas import EmailSettingsOut, EmailSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])

VALID_ALERT_TYPES = {
    "status_change",
    "committee_scheduled",
    "debate_scheduled",
    "new_document",
    "vote_result",
}


@router.get("/email", response_model=EmailSettingsOut)
def get_email_settings(
    user: User = Depends(get_current_user),
):
    types_str = user.email_alert_types or ""
    types_list = [t.strip() for t in types_str.split(",") if t.strip()] if types_str else []
    return EmailSettingsOut(
        email_alerts_enabled=user.email_alerts_enabled or False,
        email_alert_types=types_list,
    )


@router.put("/email", response_model=EmailSettingsOut)
def update_email_settings(
    data: EmailSettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.email_alerts_enabled = data.email_alerts_enabled
    # Only keep valid alert types
    valid = [t for t in data.email_alert_types if t in VALID_ALERT_TYPES]
    user.email_alert_types = ",".join(valid) if valid else ""
    db.commit()
    db.refresh(user)
    return EmailSettingsOut(
        email_alerts_enabled=user.email_alerts_enabled,
        email_alert_types=valid,
    )
