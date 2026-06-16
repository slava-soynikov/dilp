"""Sprint 5 — progress tracking endpoints (child-only writes)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.model.user import User
from app.schema.progress import LessonProgressRead, ModuleProgressRead
from app.service.progress import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/modules/{module_id}/start", response_model=ModuleProgressRead)
def start_module(
    module_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProgressService(db).start_module(user, module_id)


@router.post("/modules/{module_id}/complete", response_model=ModuleProgressRead)
def complete_module(
    module_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProgressService(db).complete_module(user, module_id)


@router.post("/lessons/{lesson_id}/start", response_model=LessonProgressRead)
def start_lesson(
    lesson_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProgressService(db).start_lesson(user, lesson_id)


@router.post("/lessons/{lesson_id}/complete", response_model=LessonProgressRead)
def complete_lesson(
    lesson_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProgressService(db).complete_lesson(user, lesson_id)


@router.post("/lessons/{lesson_id}/heartbeat", response_model=LessonProgressRead)
def heartbeat_lesson(
    lesson_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProgressService(db).heartbeat_lesson(user, lesson_id)
