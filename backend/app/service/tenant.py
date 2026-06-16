"""Tenant + School services. Admin-only mutations; scoped reads for others."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.scope import resolve_scope
from app.model.tenant import School, Tenant
from app.model.user import User
from app.repository.tenant import SchoolRepository, TenantRepository


class TenantService:
    def __init__(self, db: Session):
        self.db = db
        self.tenants = TenantRepository(db)

    def list_all(self) -> list[Tenant]:
        return self.tenants.list_all()

    def create(self, name: str) -> Tenant:
        t = self.tenants.create(name)
        self.db.commit()
        return t

    def patch(self, tenant_id: str, payload: dict) -> Tenant:
        t = self.tenants.get_by_id(tenant_id)
        if not t:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")
        if "name" in payload and payload["name"] is not None:
            t.name = payload["name"]
        self.db.commit()
        return t

    def delete(self, tenant_id: str) -> None:
        t = self.tenants.get_by_id(tenant_id)
        if not t:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")
        self.tenants.delete(t)
        self.db.commit()


class SchoolService:
    def __init__(self, db: Session):
        self.db = db
        self.schools = SchoolRepository(db)
        self.tenants = TenantRepository(db)

    def list_for_user(self, user: User) -> list[School]:
        scope = resolve_scope(self.db, user)
        if scope.is_admin:
            return self.schools.list_all()
        return self.schools.list_by_ids(scope.school_ids)

    def create(self, tenant_id: str, name: str) -> School:
        if not self.tenants.get_by_id(tenant_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")
        s = self.schools.create(tenant_id, name)
        self.db.commit()
        return s

    def patch(self, school_id: str, payload: dict) -> School:
        s = self.schools.get_by_id(school_id)
        if not s:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "school not found")
        if "name" in payload and payload["name"] is not None:
            s.name = payload["name"]
        self.db.commit()
        return s

    def delete(self, school_id: str) -> None:
        s = self.schools.get_by_id(school_id)
        if not s:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "school not found")
        self.schools.delete(s)
        self.db.commit()