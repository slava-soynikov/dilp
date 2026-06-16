from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.model.user import User
from app.repository.profile import TeacherRepository
from app.schema.profile import TeacherProfileRead

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("/me", response_model=TeacherProfileRead)
def get_my_teacher_profile(
    user: User = Depends(require_role("teacher")),
    db: Session = Depends(get_db),
):
    profile = TeacherRepository(db).get_by_user_id(user.id)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "teacher profile not found")
    return profile