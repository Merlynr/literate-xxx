from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_consent import UserConsent


GENERATION_CONSENT = "generation"


async def get_generation_privacy_status(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> UserConsent | None:
    return await db.scalar(
        select(UserConsent).where(
            UserConsent.tenant_id == tenant_id,
            UserConsent.user_id == user_id,
            UserConsent.consent_type == GENERATION_CONSENT,
        )
    )


async def accept_generation_privacy(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    source: str = GENERATION_CONSENT,
    metadata: dict[str, Any] | None = None,
) -> UserConsent:
    consent = await get_generation_privacy_status(db, tenant_id=tenant_id, user_id=user_id)
    if consent:
        consent.consented_at = datetime.now(timezone.utc)
        consent.source = source
        consent.metadata_json = metadata
        await db.flush()
        await db.refresh(consent)
        return consent

    consent = UserConsent(
        tenant_id=tenant_id,
        user_id=user_id,
        consent_type=GENERATION_CONSENT,
        consented_at=datetime.now(timezone.utc),
        source=source,
        metadata_json=metadata,
    )
    db.add(consent)
    await db.flush()
    await db.refresh(consent)
    return consent


async def has_generation_privacy_agreement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    consent = await get_generation_privacy_status(db, tenant_id=tenant_id, user_id=user_id)
    return consent is not None
