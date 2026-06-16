from sqlalchemy.orm import Session

from app.model.group import Group, GroupMember


class GroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, group_id: str) -> Group | None:
        return self.db.query(Group).filter(Group.id == group_id).first()

    def list_all(self) -> list[Group]:
        return self.db.query(Group).order_by(Group.created_at.desc()).all()

    def list_by_school(self, school_id: str) -> list[Group]:
        return self.db.query(Group).filter(Group.school_id == school_id).all()

    def list_by_ids(self, ids: set[str]) -> list[Group]:
        if not ids:
            return []
        return self.db.query(Group).filter(Group.id.in_(ids)).all()

    def create(self, school_id: str, teacher_id: str, name: str) -> Group:
        g = Group(school_id=school_id, teacher_id=teacher_id, name=name)
        self.db.add(g)
        self.db.flush()
        return g

    def delete(self, g: Group) -> None:
        self.db.delete(g)
        self.db.flush()


class GroupMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, group_id: str, child_id: str) -> GroupMember | None:
        return (
            self.db.query(GroupMember)
            .filter_by(group_id=group_id, child_id=child_id)
            .first()
        )

    def list_by_group(self, group_id: str) -> list[GroupMember]:
        return self.db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

    def add(self, group_id: str, child_id: str) -> GroupMember:
        m = GroupMember(group_id=group_id, child_id=child_id)
        self.db.add(m)
        self.db.flush()
        return m

    def remove(self, m: GroupMember) -> None:
        self.db.delete(m)
        self.db.flush()
