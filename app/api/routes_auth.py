"""Tầng Presentation: các endpoint REST cho Auth (email + mật khẩu)."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role, request_context
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.repositories import user_repository as users
from app.schemas.auth import (
    RegisterIn,
    LoginIn,
    ForgotIn,
    ResetIn,
    AuthOut,
    AccessTokenOut,
    UserOut,
    MessageOut,
)
from app.services import auth_service
from app.utils.recaptcha import verify_recaptcha

router = APIRouter()

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        max_age=settings.refresh_token_expires_days * 24 * 3600,
        path="/api",
    )


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    verify_recaptcha(data.recaptcha_token, expected_action="register")
    ua, ip = request_context(request)
    user, access_token, refresh_token = auth_service.register(db, data, user_agent=ua, ip_address=ip)
    _set_refresh_cookie(response, refresh_token)
    return {"message": "Đăng ký thành công", "user": user, "access_token": access_token}


@router.post("/login", response_model=AuthOut)
def login(data: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    verify_recaptcha(data.recaptcha_token, expected_action="login")
    ua, ip = request_context(request)
    user, access_token, refresh_token = auth_service.login(db, data, user_agent=ua, ip_address=ip)
    _set_refresh_cookie(response, refresh_token)
    return {"message": "Đăng nhập thành công", "user": user, "access_token": access_token}


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Không có refresh token")
    ua, ip = request_context(request)
    user, access_token, new_refresh = auth_service.refresh(db, token, user_agent=ua, ip_address=ip)
    _set_refresh_cookie(response, new_refresh)
    return {"access_token": access_token, "user": user}


@router.post("/logout", response_model=MessageOut)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    # Revoke phiên hiện tại (nếu giải mã được cookie) trước khi xoá cookie.
    token = request.cookies.get(REFRESH_COOKIE)
    auth_service.logout(db, token)
    response.delete_cookie(REFRESH_COOKIE, path="/api")
    return {"message": "Đã đăng xuất"}


@router.get("/profile", response_model=UserOut)
def profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(data: ForgotIn, db: Session = Depends(get_db)):
    return {"message": auth_service.forgot_password(db, data.email)}


@router.post("/reset-password", response_model=MessageOut)
def reset_password(data: ResetIn, db: Session = Depends(get_db)):
    return {"message": auth_service.reset_password(db, data)}


@router.get("/admin/users", response_model=list[UserOut])
def admin_list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return users.list_all(db)
