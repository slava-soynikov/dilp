from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.tenant import SchoolCreate, SchoolRead
from app.service.tenant import SchoolService

router = APIRouter(prefix="/schools", tags=["schools"])


class SchoolPatch(BaseModel):
    name: str | None = None


@router.get("", response_model=list[SchoolRead])
def list_schools(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return SchoolService(db).list_for_user(user)


@router.post("", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(
    payload: SchoolCreate,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return SchoolService(db).create(payload.tenant_id, payload.name)


@router.patch("/{school_id}", response_model=SchoolRead)
def patch_school(
    school_id: str,
    payload: SchoolPatch,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return SchoolService(db).patch(school_id, payload.model_dump(exclude_unset=True))


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: str,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    SchoolService(db).delete(school_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)