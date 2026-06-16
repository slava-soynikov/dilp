"""Admin service: create teacher, reset user passwords (admin-only)."""
import secrets
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.integrations import mailer
from app.model.profile import TeacherProfile
from app.model.user import RefreshToken, Role, User, UserRole
from app.repository.user import UserRepository


def _generate_temp_password() -> str:
    """16-char URL-safe temp password, passes policy (digit+letter very likely)."""
    while True:
        pwd = secrets.token_urlsafe(12)[:16]
        if any(c.isalpha() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def create_teacher(self, email: str, first_name: str, last_name: str) -> tuple[User, str]:
        email = email.strip().lower()
        first_name = first_name.strip()
        last_name = last_name.strip()
        if self.users.get_by_email(email):
            raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")

        temp_pwd = _generate_temp_password()
        user = User(
            email=email,
            password_hash=hash_password(temp_pwd),
            status="active",
        )
        self.db.add(user)
        self.db.flush()

        teacher_role = self.db.query(Role).filter_by(name="teacher").one()
        self.db.add(UserRole(user_id=user.id, role_id=teacher_role.id))
        self.db.add(TeacherProfile(user_id=user.id, first_name=first_name, last_name=last_name))
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")

        mailer.send_teacher_invite(email, temp_pwd)
        return user, temp_pwd

    def reset_user_password(self, identifier: str) -> tuple[User, str]:
        """Generate a new password for the user (lookup by email or username),
        revoke all refresh tokens, return the plain password to the admin caller.

        Children authenticate by username + PIN, not by password — for children
        use POST /children/{id}/reset-pin instead.
        """
        ident = identifier.strip().lower()
        user = self.users.get_by_email(ident) or self.users.get_by_username(ident)
        if not user or user.deleted_at is not None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")

        new_pwd = _generate_temp_password()
        user.password_hash = hash_password(new_pwd)

        now = datetime.utcnow()
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": now}, synchronize_session=False)

        self.db.commit()
        return user, new_pwd