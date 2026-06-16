from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.model.group import GroupProgramme
from app.model.programme import Lesson, Module, Programme


class ProgrammeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, programme_id: str) -> Programme | None:
        return self.db.query(Programme).filter(Programme.id == programme_id).first()

    def list_all(self) -> list[Programme]:
        return self.db.query(Programme).order_by(Programme.created_at.desc()).all()

    def list_by_tenants_and_global(self, tenant_ids: set[str]) -> list[Programme]:
        if not tenant_ids:
            return (
                self.db.query(Programme)
                .filter(Programme.tenant_id.is_(None))
                .order_by(Programme.created_at.desc())
                .all()
            )
        return (
            self.db.query(Programme)
            .filter(
                or_(
                    Programme.tenant_id.is_(None),
                    Programme.tenant_id.in_(tenant_ids),
                )
            )
            .order_by(Programme.created_at.desc())
            .all()
        )

    def list_by_ids(self, ids: set[str]) -> list[Programme]:
        if not ids:
            return []
        return self.db.query(Programme).filter(Programme.id.in_(ids)).all()

    def create(
        self, name: str, language: str, tenant_id: str | None
    ) -> Programme:
        p = Programme(name=name, language=language, tenant_id=tenant_id)
        self.db.add(p)
        self.db.flush()
        return p

    def delete(self, p: Programme) -> None:
        self.db.delete(p)
        self.db.flush()


class ModuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, module_id: str) -> Module | None:
        return self.db.query(Module).filter(Module.id == module_id).first()

    def order_exists(self, programme_id: str, order_index: int) -> bool:
        return (
            self.db.query(Module)
            .filter_by(programme_id=programme_id, order_index=order_index)
            .first()
            is not None
        )

    def create(self, programme_id: str, title: str, order_index: int) -> Module:
        m = Module(programme_id=programme_id, title=title, order_index=order_index)
        self.db.add(m)
        self.db.flush()
        return m

    def delete(self, m: Module) -> None:
        self.db.delete(m)
        self.db.flush()


class LessonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, lesson_id: str) -> Lesson | None:
        return self.db.query(Lesson).filter(Lesson.id == lesson_id).first()

    def order_exists(self, module_id: str, order_index: int) -> bool:
        return (
            self.db.query(Lesson)
            .filter_by(module_id=module_id, order_index=order_index)
            .first()
            is not None
        )

    def create(
        self,
        module_id: str,
        title: str,
        content_ref: str | None,
        order_index: int,
        meeting_url: str | None = None,
    ) -> Lesson:
        l = Lesson(
            module_id=module_id,
            title=title,
            content_ref=content_ref,
            order_index=order_index,
            meeting_url=meeting_url,
        )
        self.db.add(l)
        self.db.flush()
        return l

    def delete(self, l: Lesson) -> None:
        self.db.delete(l)
        self.db.flush()


class GroupProgrammeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, group_id: str, programme_id: str) -> GroupProgramme | None:
        return (
            self.db.query(GroupProgramme)
            .filter_by(group_id=group_id, programme_id=programme_id)
            .first()
        )

    def list_by_group(self, group_id: str) -> list[GroupProgramme]:
        return (
            self.db.query(GroupProgramme)
            .filter(GroupProgramme.group_id == group_id)
            .all()
        )

    def list_programme_ids_by_groups(self, group_ids: set[str]) -> set[str]:
        if not group_ids:
            return set()
        rows = (
            self.db.query(GroupProgramme.programme_id)
            .filter(GroupProgramme.group_id.in_(group_ids))
            .all()
        )
        return {r[0] for r in rows}

    def list_group_ids_by_programme(self, programme_id: str) -> set[str]:
        rows = (
            self.db.query(GroupProgramme.group_id)
            .filter(GroupProgramme.programme_id == programme_id)
            .all()
        )
        return {r[0] for r in rows}

    def add(self, group_id: str, programme_id: str) -> GroupProgramme:
        gp = GroupProgramme(group_id=group_id, programme_id=programme_id)
        self.db.add(gp)
        self.db.flush()
        return gp

    def remove(self, gp: GroupProgramme) -> None:
        self.db.delete(gp)
        self.db.flush()