import re
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,32}$")


class ChildCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date | None = None
    native_language: str | None = None
    school_id: str | None = None

    @field_validator("username")
    @classmethod
    def _username_format(cls, v: str) -> str:
        v = v.strip()
        if not USERNAME_RE.match(v):
            raise ValueError(
                "username must be 3-32 chars of lowercase letters, digits, dot, dash, underscore"
            )
        return v


class ChildPatch(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    native_language: str | None = None


class ChildProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    username: str | None = None
    status: str | None = None
    school_id: str | None
    first_name: str
    last_name: str
    date_of_birth: date | None
    native_language: str | None


class ChildCreateResponse(ChildProfileRead):
    pin: str  # 8-digit, returned ONCE on creation


class ParentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class TeacherProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    first_name: str
    last_name: str


class TeacherListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str  # teacher_profile.id — used as group.teacher_id
    user_id: str
    email: str | None
    first_name: str
    last_name: str