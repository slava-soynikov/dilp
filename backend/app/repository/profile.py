from sqlalchemy.orm import Session

from app.model.profile import (
    ChildProfile,
    ParentChildRelation,
    ParentProfile,
    TeacherProfile,
)


class ParentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> ParentProfile | None:
        return (
            self.db.query(ParentProfile)
            .filter(ParentProfile.user_id == user_id)
            .first()
        )

    def list_children(self, parent_profile_id: str) -> list[ChildProfile]:
        return (
            self.db.query(ChildProfile)
            .join(ParentChildRelation, ParentChildRelation.child_id == ChildProfile.id)
            .filter(
                ParentChildRelation.parent_id == parent_profile_id,
                ChildProfile.deleted_at.is_(None),
            )
            .all()
        )


class ChildRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, child_id: str) -> ChildProfile | None:
        return (
            self.db.query(ChildProfile)
            .filter(ChildProfile.id == child_id, ChildProfile.deleted_at.is_(None))
            .first()
        )

    def get_by_user_id(self, user_id: str) -> ChildProfile | None:
        return (
            self.db.query(ChildProfile)
            .filter(ChildProfile.user_id == user_id, ChildProfile.deleted_at.is_(None))
            .first()
        )


class TeacherRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> TeacherProfile | None:
        return (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == user_id)
            .first()
        )