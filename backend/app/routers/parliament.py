from fastapi import APIRouter, Depends, Query

from ..auth import get_current_user
from ..models import User
from ..schemas import ParliamentPreview
from ..services.parliament_api import fetch_business, search_businesses

router = APIRouter(prefix="/api/parliament", tags=["parliament"])


@router.get("/search", response_model=list[ParliamentPreview])
async def search(
    q: str = Query(..., min_length=2),
    user: User = Depends(get_current_user),
):
    return await search_businesses(q)


@router.get("/preview/{business_number}", response_model=ParliamentPreview)
async def preview(
    business_number: str,
    user: User = Depends(get_current_user),
):
    info = await fetch_business(business_number)
    if not info:
        return ParliamentPreview(business_number=business_number)
    return ParliamentPreview(
        business_number=business_number,
        title=info.get("title"),
        description=info.get("description"),
        business_type=info.get("business_type"),
        status=info.get("status"),
        submission_date=info.get("submission_date"),
    )
