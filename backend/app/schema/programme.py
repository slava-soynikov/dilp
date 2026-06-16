from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------- Lesson ----------


class LessonCreate(BaseModel):
    title: str
    content_ref: str | None = None
    meeting_url: str | None = None
    order_index: int = 0


class LessonPatch(BaseModel):
    title: str | None = None
    content_ref: str | None = None
    meeting_url: str | None = None
    order_index: int | None = None


class LessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    module_id: str
    title: str
    content_ref: str | None
    meeting_url: str | None = None
    order_index: int


class LessonWithContent(LessonRead):
    content: dict[str, Any] | None = None


# ---------- Module ----------


class ModuleCreate(BaseModel):
    title: str
    order_index: int = 0


class ModulePatch(BaseModel):
    title: str | None = None
    order_index: int | None = None


class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    programme_id: str
    title: str
    order_index: int
    lessons: list[LessonRead] = []


# ---------- Programme ----------


class ProgrammeCreate(BaseModel):
    name: str
    language: str
    tenant_id: str | None = None


class ProgrammePatch(BaseModel):
    name: str | None = None
    language: str | None = None


class ProgrammeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str | None
    name: str
    language: str
    modules: list[ModuleRead] = []


# ---------- Group-programme assignment ----------


class GroupProgrammeAssign(BaseModel):
    programme_id: str


class GroupProgrammeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: str
    programme_id: str


# ---------- Curriculum ----------


class CurriculumRead(BaseModel):
    programmes: list[ProgrammeRead] = []