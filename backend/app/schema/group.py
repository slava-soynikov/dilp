from pydantic import BaseModel, ConfigDict


class GroupCreate(BaseModel):
    name: str
    school_id: str
    teacher_id: str


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    school_id: str
    teacher_id: str


class GroupMemberCreate(BaseModel):
    child_id: str


class GroupMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: str
    child_id: str