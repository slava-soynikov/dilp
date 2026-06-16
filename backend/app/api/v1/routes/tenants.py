from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.tenant import TenantCreate, TenantRead
from app.service.tenant import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantPatch(BaseModel):
    name: str | None = None


@router.get("", response_model=list[TenantRead])
def list_tenants(
    _: User = Depends(require_role("admin")), db: Session = Depends(get_db)
):
    return TenantService(db).list_all()


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return TenantService(db).create(payload.name)


@router.patch("/{tenant_id}", response_model=TenantRead)
def patch_tenant(
    tenant_id: str,
    payload: TenantPatch,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return TenantService(db).patch(tenant_id, payload.model_dump(exclude_unset=True))


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: str,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    TenantService(db).delete(tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)