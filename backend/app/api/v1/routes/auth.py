from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.rate_limit import auth_rate_limit, limiter
from app.db.session import get_db
from app.schema.auth import (
    ForgotPasswordIn,
    RefreshIn,
    RegisterIn,
    ResetPasswordIn,
    TokenOut,
)
from app.schema.user import UserRead
from app.service.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(auth_rate_limit)
def register(request: Request, payload: RegisterIn, db: Session = Depends(get_db)):
    user = AuthService(db).register(payload.email, payload.password, payload.role)
    return user


@router.post("/login", response_model=TokenOut)
@limiter.limit(auth_rate_limit)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return AuthService(db).login(form.username, form.password)


@router.post("/refresh", response_model=TokenOut)
@limiter.limit(auth_rate_limit)
def refresh(request: Request, payload: RefreshIn, db: Session = Depends(get_db)):
    return AuthService(db).refresh_tokens(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshIn, db: Session = Depends(get_db)):
    AuthService(db).logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password")
@limiter.limit(auth_rate_limit)
def forgot_password(request: Request, payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    AuthService(db).forgot_password(payload.email)
    return {"status": "ok"}


@router.post("/reset-password")
@limiter.limit(auth_rate_limit)
def reset_password(request: Request, payload: ResetPasswordIn, db: Session = Depends(get_db)):
    AuthService(db).reset_password(payload.token, payload.new_password)
    return {"status": "ok"}