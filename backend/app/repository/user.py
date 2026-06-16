from datetime import datetime

from sqlalchemy.orm import Session

from app.model.user import RefreshToken, Role, User, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username, User.deleted_at.is_(None)).first()

    def get_by_identifier(self, identifier: str) -> User | None:
        """Resolve login identifier: email if it looks like one, else username."""
        ident = identifier.strip().lower()
        if "@" in ident:
            return self.get_by_email(ident)
        return self.get_by_username(ident)

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()

    def create(self, email: str, password_hash: str, role_name: str, status: str = "pending") -> User:
        user = User(email=email, password_hash=password_hash, status=status)
        self.db.add(user)
        self.db.flush()
        role = self.db.query(Role).filter_by(name=role_name).one()
        self.db.add(UserRole(user_id=user.id, role_id=role.id))
        self.db.flush()
        return user

    def list_roles(self, user_id: str) -> list[str]:
        rows = (
            self.db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        return [r[0] for r in rows]


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(rt)
        self.db.flush()
        return rt

    def get_active_by_hash(self, token_hash: str) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.utcnow(),
            )
            .first()
        )

    def revoke(self, rt: RefreshToken) -> None:
        rt.revoked_at = datetime.utcnow()
        self.db.flush()