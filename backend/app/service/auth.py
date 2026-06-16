import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_purpose_token,
    decode_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    validate_password_policy,
    verify_password,
)
from app.integrations import mailer
from app.model.profile import ParentProfile
from app.model.user import User
from app.repository.user import RefreshTokenRepository, UserRepository

logger = logging.getLogger("auth")

PUBLIC_REGISTRATION_ROLES = {"parent"}  # MVP: teacher/child/admin not via public endpoint

# Per-account brute-force protection (architecture §7.2). The global IP
# rate-limit doesn't stop distributed guessing of an 8-digit child PIN.
LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION_MIN = 15


def _normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.refresh = RefreshTokenRepository(db)

    def register(self, email: str, password: str, role: str) -> User:
        if role not in PUBLIC_REGISTRATION_ROLES:
            logger.info("auth.register.forbidden_role email=%s role=%s", email, role)
            raise HTTPException(status.HTTP_403_FORBIDDEN, "role not allowed for public registration")
        err = validate_password_policy(password)
        if err:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, err)

        email = _normalize_email(email)
        if self.users.get_by_email(email):
            raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")

        # Parents are active immediately — no email verification step.
        # Child placement into groups by age/abilities is done manually by teachers.
        user = self.users.create(
            email=email, password_hash=hash_password(password), role_name=role, status="active"
        )
        if role == "parent":
            self.db.add(ParentProfile(user_id=user.id))
            self.db.flush()
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")

        logger.info("auth.register.ok user_id=%s email=%s role=%s", user.id, email, role)
        return user

    def login(self, identifier: str, password: str) -> dict:
        identifier = identifier.strip().lower()
        user = self.users.get_by_identifier(identifier)
        now = datetime.utcnow()
        if user and user.lockout_until and user.lockout_until > now:
            logger.info("auth.login.locked identifier=%s until=%s", identifier, user.lockout_until)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "account temporarily locked")
        if not user or not verify_password(password, user.password_hash):
            if user:
                user.failed_login_count = (user.failed_login_count or 0) + 1
                if user.failed_login_count >= LOCKOUT_THRESHOLD:
                    user.lockout_until = now + timedelta(minutes=LOCKOUT_DURATION_MIN)
                    logger.info(
                        "auth.login.lockout user_id=%s until=%s",
                        user.id,
                        user.lockout_until,
                    )
                self.db.commit()
            logger.info("auth.login.fail identifier=%s", identifier)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
        if user.status == "disabled":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "account disabled")
        if user.status == "pending" and user.email is None:
            # Child without granted consent — cannot use the platform yet.
            raise HTTPException(status.HTTP_403_FORBIDDEN, "consent required")

        user.failed_login_count = 0
        user.lockout_until = None
        user.last_login_at = now
        roles = self.users.list_roles(user.id)
        access = create_access_token(user.id, roles)
        _, raw_refresh, expires_at = generate_refresh_token()
        self.refresh.create(user.id, hash_refresh_token(raw_refresh), expires_at)
        self.db.commit()
        logger.info("auth.login.ok user_id=%s", user.id)
        return {"access_token": access, "refresh_token": raw_refresh, "token_type": "bearer"}

    def refresh_tokens(self, raw_refresh: str) -> dict:
        rt = self.refresh.get_active_by_hash(hash_refresh_token(raw_refresh))
        if not rt:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")
        self.refresh.revoke(rt)
        user = self.users.get_by_id(rt.user_id)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")
        roles = self.users.list_roles(user.id)
        access = create_access_token(user.id, roles)
        _, new_raw, expires_at = generate_refresh_token()
        self.refresh.create(user.id, hash_refresh_token(new_raw), expires_at)
        self.db.commit()
        return {"access_token": access, "refresh_token": new_raw, "token_type": "bearer"}

    def logout(self, raw_refresh: str) -> None:
        rt = self.refresh.get_active_by_hash(hash_refresh_token(raw_refresh))
        if rt:
            self.refresh.revoke(rt)
            self.db.commit()
            logger.info("auth.logout.ok user_id=%s", rt.user_id)

    def forgot_password(self, email: str) -> None:
        email = _normalize_email(email)
        user = self.users.get_by_email(email)
        if user:
            token = create_purpose_token(user.id, "reset_password", settings.PASSWORD_RESET_TOKEN_TTL_HOURS)
            mailer.send_password_reset(email, token)
            logger.info("auth.forgot_password.sent user_id=%s", user.id)
        else:
            logger.info("auth.forgot_password.unknown_email email=%s", email)

    def reset_password(self, token: str, new_password: str) -> None:
        err = validate_password_policy(new_password)
        if err:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, err)
        payload = self._decode_purpose(token, "reset_password")
        user = self.users.get_by_id(payload["sub"])
        if not user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid token")
        user.password_hash = hash_password(new_password)
        for rt in user.refresh_tokens:
            if rt.revoked_at is None:
                rt.revoked_at = datetime.utcnow()
        self.db.commit()
        logger.info("auth.reset_password.ok user_id=%s", user.id)

    @staticmethod
    def _decode_purpose(token: str, expected_purpose: str) -> dict:
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid token")
        if payload.get("purpose") != expected_purpose or payload.get("type") != "purpose":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid token")
        return payload