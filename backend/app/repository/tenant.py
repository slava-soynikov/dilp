from sqlalchemy.orm import Session

from app.model.tenant import School, Tenant


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tenant_id: str) -> Tenant | None:
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def list_all(self) -> list[Tenant]:
        return self.db.query(Tenant).order_by(Tenant.created_at.desc()).all()

    def create(self, name: str) -> Tenant:
        t = Tenant(name=name)
        self.db.add(t)
        self.db.flush()
        return t

    def delete(self, t: Tenant) -> None:
        self.db.delete(t)
        self.db.flush()


class SchoolRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, school_id: str) -> School | None:
        return self.db.query(School).filter(School.id == school_id).first()

    def list_by_tenant(self, tenant_id: str) -> list[School]:
        return (
            self.db.query(School)
            .filter(School.tenant_id == tenant_id)
            .order_by(School.created_at.desc())
            .all()
        )

    def list_all(self) -> list[School]:
        return self.db.query(School).order_by(School.created_at.desc()).all()

    def list_by_ids(self, ids: set[str]) -> list[School]:
        if not ids:
            return []
        return self.db.query(School).filter(School.id.in_(ids)).all()

    def create(self, tenant_id: str, name: str) -> School:
        s = School(tenant_id=tenant_id, name=name)
        self.db.add(s)
        self.db.flush()
        return s

    def delete(self, s: School) -> None:
        self.db.delete(s)
        self.db.flush()
