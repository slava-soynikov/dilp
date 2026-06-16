from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.model.user import User
from app.repository.profile import ParentRepository
from app.schema.profile import ParentProfileRead
from app.schema.report import ChildDashboardReport
from app.service.report import ReportService

router = APIRouter(prefix="/parents", tags=["parents"])


@router.get("/me", response_model=ParentProfileRead)
def get_my_parent_profile(
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    profile = ParentRepository(db).get_by_user_id(user.id)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "parent profile not found")
    return profile


@router.get(
    "/me/children/{child_id}/dashboard",
    response_model=ChildDashboardReport,
)
def get_child_dashboard(
    child_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Per-child progress summary for the linked parent (§5.1, §7.3).

    Returns 404 when the requesting parent is not linked to ``child_id``, so
    that the existence of unrelated children is not revealed.
    """
    return ReportService(db).child_dashboard(child_id, user)