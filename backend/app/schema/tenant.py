from pydantic import BaseModel, ConfigDict


class TenantCreate(BaseModel):
    name: str


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class SchoolCreate(BaseModel):
    tenant_id: str
    name: str


class SchoolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str