from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


ALLOWED_CONSENT_TYPES = {"data_processing"}  # MVP. content_access in Sprint 4.


class ConsentCreate(BaseModel):
    child_id: str
    consent_type: str
    consent_version: str = "1.0"
    consent_text_ref: str | None = None

    @field_validator("consent_type")
    @classmethod
    def _allowed_type(cls, v: str) -> str:
        if v not in ALLOWED_CONSENT_TYPES:
            raise ValueError(f"consent_type must be one of {sorted(ALLOWED_CONSENT_TYPES)}")
        return v


class ConsentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_id: str
    child_id: str
    consent_type: str
    consent_version: str
    consent_text_ref: str | None
    granted_at: datetime
    revoked_at: datetime | None