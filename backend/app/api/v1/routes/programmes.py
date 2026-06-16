from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.programme import (
    ModuleCreate,
    ModuleRead,
    ProgrammeCreate,
    ProgrammePatch,
    ProgrammeRead,
)
from app.service.programme import ModuleService, ProgrammeService

router = APIRouter(prefix="/programmes", tags=["programmes"])


@router.get("", response_model=list[ProgrammeRead])
def list_programmes(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return ProgrammeService(db).list_for_user(user)


@router.post("", response_model=ProgrammeRead, status_code=status.HTTP_201_CREATED)
def create_programme(
    payload: ProgrammeCreate,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ProgrammeService(db).create(
        payload.name, payload.language, payload.tenant_id
    )


@router.get("/{programme_id}", response_model=ProgrammeRead)
def get_programme(
    programme_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProgrammeService(db).get_for_user(user, programme_id)


@router.patch("/{programme_id}", response_model=ProgrammeRead)
def patch_programme(
    programme_id: str,
    payload: ProgrammePatch,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ProgrammeService(db).patch(
        programme_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/{programme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_programme(
    programme_id: str,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ProgrammeService(db).delete(programme_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- modules nested under programme ----


@router.post(
    "/{programme_id}/modules",
    response_model=ModuleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_module(
    programme_id: str,
    payload: ModuleCreate,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    return ModuleService(db).create(
        user, programme_id, payload.title, payload.order_index
    )
