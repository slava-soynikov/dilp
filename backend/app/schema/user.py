from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None = None
    username: str | None = None
    status: str
    created_at: datetime


class UserMeRead(BaseModel):
    id: str
    email: str | None = None
    username: str | None = None
    status: str
    roles: list[str]
    created_at: datetime


class UserMePatch(BaseModel):
    # Reserved for future fields editable on the user itself.
    # Profile-specific fields (first_name on child, etc.) live under /children, /teachers.
    pass


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str