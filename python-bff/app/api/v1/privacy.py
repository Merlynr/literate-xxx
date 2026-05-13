from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.privacy import PrivacyAcceptRequest, PrivacyAcceptResponse, PrivacyAgreementStatus
from app.services.privacy_service import accept_generation_privacy, get_generation_privacy_status

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.get("/agreement-status", response_model=PrivacyAgreementStatus)
async def agreement_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    consent = await get_generation_privacy_status(db, tenant_id=current_user.tenant_id, user_id=current_user.id)
    return PrivacyAgreementStatus(
        has_privacy_agreement=consent is not None,
        privacy_accepted_at=consent.consented_at if consent else None,
    )


@router.post("/accept", response_model=PrivacyAcceptResponse)
async def accept_privacy(
    body: PrivacyAcceptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    consent = await accept_generation_privacy(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        source=body.source,
        metadata={"consent_type": body.consent_type},
    )
    return PrivacyAcceptResponse(
        has_privacy_agreement=True,
        privacy_accepted_at=consent.consented_at,
    )
