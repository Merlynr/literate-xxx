from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PrivacyAgreementStatus(BaseModel):
    has_privacy_agreement: bool
    privacy_accepted_at: datetime | None = None


class PrivacyAcceptRequest(BaseModel):
    consent_type: str = Field(default="generation")
    source: str = Field(default="generation")


class PrivacyAcceptResponse(BaseModel):
    has_privacy_agreement: bool
    privacy_accepted_at: datetime
