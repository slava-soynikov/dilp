from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    created_at: datetime


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    action: str
    entity_type: str
    entity_id: str
    diff: str | None
    timestamp: datetime