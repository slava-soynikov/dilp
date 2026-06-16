import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def validate_password_policy(password: str) -> str | None:
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return f"password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
    if not any(c.isalpha() for c in password):
        return "password must contain a letter"
    if not any(c.isdigit() for c in password):
        return "password must contain a digit"
    return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, roles: list[str]) -> str:
    payload = {
        "sub": user_id,
        "roles": roles,
        "type": "access",
        "iat": _now(),
        "exp": _now() + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def create_purpose_token(user_id: str, purpose: str, ttl_hours: int) -> str:
    payload = {
        "sub": user_id,
        "purpose": purpose,
        "type": "purpose",
        "iat": _now(),
        "exp": _now() + timedelta(hours=ttl_hours),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Returns (token_id, raw_token, expires_at). The raw token is what the client gets;
    only its SHA-256 hash is stored in DB."""
    token_id = str(uuid.uuid4())
    raw = f"{token_id}.{secrets.token_urlsafe(48)}"
    expires_at = _now().replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)
    return token_id, raw, expires_at


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()