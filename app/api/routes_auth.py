"""Tầng Presentation (API): các endpoint REST."""
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
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

router = APIRouter()

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Refresh token đặt trong cookie HttpOnly + Secure (prod) + SameSite=Strict.

    => JS không đọc được (chống XSS) và không gửi kèm khi cross-site (chống CSRF).
    """
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.is_production,  # chỉ qua HTTPS ở production
        samesite="strict",
        max_age=settings.refresh_token_expires_days * 24 * 3600,
        path="/api",
    )


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, response: Response, db: Session = Depends(get_db)):
    user, access_token, refresh_token = auth_service.register(db, data)
    _set_refresh_cookie(response, refresh_token)
    return {"message": "Đăng ký thành công", "user": user, "access_token": access_token}


@router.post("/login", response_model=AuthOut)
def login(data: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    user, access_token, refresh_token = auth_service.login(db, data, ip)
    _set_refresh_cookie(response, refresh_token)
    return {"message": "Đăng nhập thành công", "user": user, "access_token": access_token}


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Không có refresh token")
    user, access_token, new_refresh = auth_service.refresh(db, token)
    _set_refresh_cookie(response, new_refresh)  # xoay vòng refresh token
    return {"access_token": access_token, "user": user}


@router.post("/logout", response_model=MessageOut)
def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE, path="/api")
    return {"message": "Đã đăng xuất"}


@router.get("/profile", response_model=UserOut)
def profile(current_user: User = Depends(get_current_user)):
    # Route được bảo vệ: cần access token hợp lệ.
    return current_user


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(data: ForgotIn, db: Session = Depends(get_db)):
    message = auth_service.forgot_password(db, data.email)
    return {"message": message}


@router.post("/reset-password", response_model=MessageOut)
def reset_password(data: ResetIn, db: Session = Depends(get_db)):
    message = auth_service.reset_password(db, data)
    return {"message": message}


@router.get("/admin/users", response_model=list[UserOut])
def admin_list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),  # RBAC: chỉ admin
):
    return users.list_all(db)
