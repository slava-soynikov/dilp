from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.profile import ChildCreate, ChildCreateResponse, ChildPatch, ChildProfileRead
from app.schema.programme import CurriculumRead
from app.service.child import ChildService
from app.service.programme import CurriculumService

router = APIRouter(prefix="/children", tags=["children"])


@router.get("/me/curriculum", response_model=CurriculumRead)
def get_my_curriculum(
    user: User = Depends(require_role("child")),
    db: Session = Depends(get_db),
):
    return CurriculumRead(programmes=CurriculumService(db).for_child(user))


@router.patch("/{child_id}", response_model=ChildProfileRead)
def patch_child(
    child_id: str,
    payload: ChildPatch,
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    return ChildService(db).patch(user, child_id, payload.model_dump(exclude_unset=True))


@router.post("", response_model=ChildCreateResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    payload: ChildCreate,
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    return ChildService(db).create_for_parent(user, payload.model_dump())


@router.get("", response_model=list[ChildProfileRead])
def list_children(
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    return ChildService(db).list_for_parent(user)