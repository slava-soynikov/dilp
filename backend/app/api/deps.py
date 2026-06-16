from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.model.user import User
from app.repository.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")
    user = UserRepository(db).get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


def require_role(*allowed: str):
    def _dep(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        roles = UserRepository(db).list_roles(user.id)
        if not set(roles) & set(allowed):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
        return user

    return _dep