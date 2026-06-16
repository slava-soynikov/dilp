from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.model.profile import TeacherProfile
from app.model.user import User
from app.schema.profile import TeacherListItem
from app.schema.user import UserRead
from app.service.admin import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


class TeacherInviteIn(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class TeacherInviteOut(UserRead):
    temp_password: str


class ResetPasswordIn(BaseModel):
    identifier: str  # email or username


class ResetPasswordOut(BaseModel):
    user_id: str
    email: str | None
    username: str | None
    new_password: str


@router.post(
    "/teachers",
    response_model=TeacherInviteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher(
    payload: TeacherInviteIn,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user, temp_pwd = AdminService(db).create_teacher(
        payload.email, payload.first_name, payload.last_name
    )
    return TeacherInviteOut(
        **UserRead.model_validate(user).model_dump(),
        temp_password=temp_pwd,
    )


@router.get("/teachers", response_model=list[TeacherListItem])
def list_teachers(
    q: str | None = None,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List teachers for admin pickers. Optional ?q filters by last/first name
    or email (case-insensitive substring)."""
    query = (
        db.query(TeacherProfile, User)
        .join(User, User.id == TeacherProfile.user_id)
        .filter(User.deleted_at.is_(None))
    )
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                User.email.ilike(like),
                TeacherProfile.last_name.ilike(like),
                TeacherProfile.first_name.ilike(like),
            )
        )
    rows = query.order_by(TeacherProfile.last_name, TeacherProfile.first_name).all()
    return [
        TeacherListItem(
            id=tp.id,
            user_id=tp.user_id,
            email=u.email,
            first_name=tp.first_name,
            last_name=tp.last_name,
        )
        for tp, u in rows
    ]


@router.post(
    "/users/reset-password",
    response_model=ResetPasswordOut,
    status_code=status.HTTP_200_OK,
)
def reset_user_password(
    payload: ResetPasswordIn,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user, new_pwd = AdminService(db).reset_user_password(payload.identifier)
    return ResetPasswordOut(
        user_id=user.id,
        email=user.email,
        username=user.username,
        new_password=new_pwd,
    )