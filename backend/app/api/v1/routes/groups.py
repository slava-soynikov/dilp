from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.group import GroupCreate, GroupMemberCreate, GroupMemberRead, GroupRead
from app.schema.profile import ChildProfileRead
from app.schema.programme import GroupProgrammeAssign, GroupProgrammeRead
from app.service.group import GroupService
from app.service.programme import GroupProgrammeService

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupPatch(BaseModel):
    name: str | None = None


@router.get("", response_model=list[GroupRead])
def list_groups(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return GroupService(db).list_for_user(user)


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return GroupService(db).create(payload.school_id, payload.teacher_id, payload.name)


@router.patch("/{group_id}", response_model=GroupRead)
def patch_group(
    group_id: str,
    payload: GroupPatch,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    return GroupService(db).patch(user, group_id, payload.model_dump(exclude_unset=True))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: str,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    GroupService(db).delete(group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{group_id}/members", response_model=list[ChildProfileRead])
def list_members(
    group_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GroupService(db).list_members(user, group_id)


@router.post(
    "/{group_id}/members",
    response_model=GroupMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    group_id: str,
    payload: GroupMemberCreate,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    return GroupService(db).add_member(user, group_id, payload.child_id)


@router.delete(
    "/{group_id}/members/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    group_id: str,
    child_id: str,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    GroupService(db).remove_member(user, group_id, child_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- group ↔ programme assignment ----


@router.get("/{group_id}/programmes", response_model=list[GroupProgrammeRead])
def list_group_programmes(
    group_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GroupProgrammeService(db).list_for_group(user, group_id)


@router.post(
    "/{group_id}/programmes",
    response_model=GroupProgrammeRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_programme(
    group_id: str,
    payload: GroupProgrammeAssign,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    return GroupProgrammeService(db).assign(user, group_id, payload.programme_id)


@router.delete(
    "/{group_id}/programmes/{programme_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_programme(
    group_id: str,
    programme_id: str,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    GroupProgrammeService(db).unassign(user, group_id, programme_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)