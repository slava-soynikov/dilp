from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ProgressStatus = Literal["not_started", "in_progress", "completed"]


class ModuleProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    child_id: str
    module_id: str
    status: ProgressStatus
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime


class ModuleProgressUpdate(BaseModel):
    status: ProgressStatus


class LessonProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    child_id: str
    lesson_id: str
    status: ProgressStatus
    started_at: datetime | None
    completed_at: datetime | None
    last_accessed_at: datetime


class LessonProgressUpdate(BaseModel):
    status: ProgressStatus