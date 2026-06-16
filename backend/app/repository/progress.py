"""Repository helpers for ModuleProgress / LessonProgress (Sprint 5)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.model.progress import LessonProgress, ModuleProgress


class ModuleProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, child_id: str, module_id: str) -> ModuleProgress | None:
        return (
            self.db.query(ModuleProgress)
            .filter(
                ModuleProgress.child_id == child_id,
                ModuleProgress.module_id == module_id,
            )
            .first()
        )

    def create(self, child_id: str, module_id: str) -> ModuleProgress:
        mp = ModuleProgress(
            child_id=child_id,
            module_id=module_id,
            status="not_started",
        )
        self.db.add(mp)
        self.db.flush()
        return mp


class LessonProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, child_id: str, lesson_id: str) -> LessonProgress | None:
        return (
            self.db.query(LessonProgress)
            .filter(
                LessonProgress.child_id == child_id,
                LessonProgress.lesson_id == lesson_id,
            )
            .first()
        )

    def create(self, child_id: str, lesson_id: str) -> LessonProgress:
        lp = LessonProgress(
            child_id=child_id,
            lesson_id=lesson_id,
            status="not_started",
        )
        self.db.add(lp)
        self.db.flush()
        return lp

    def list_for_module(
        self, child_id: str, lesson_ids: list[str]
    ) -> list[LessonProgress]:
        if not lesson_ids:
            return []
        return (
            self.db.query(LessonProgress)
            .filter(
                LessonProgress.child_id == child_id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
            .all()
        )
