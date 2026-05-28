"""Hàm bảo mật: băm mật khẩu (bcrypt) và tạo/giải mã JWT (token kép)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# ---------- Mật khẩu (bcrypt) ----------

def hash_password(password: str) -> str:
    """Băm mật khẩu bằng bcrypt với salt ngẫu nhiên. KHÔNG lưu mật khẩu gốc."""
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """So khớp mật khẩu người dùng nhập với hash đã lưu."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------- JWT (token kép) ----------

def _create_token(payload: dict, secret: str, expires_delta: timedelta) -> str:
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({"iat": now, "exp": now + expires_delta})
    return jwt.encode(to_encode, secret, algorithm="HS256")


def create_access_token(user, sid: str | None = None) -> str:
    """Access token sống ngắn — nhúng role (RBAC) và sid (định danh phiên)."""
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role,
    }
    if sid:
        payload["sid"] = sid
    return _create_token(
        payload,
        settings.jwt_secret,
        timedelta(minutes=settings.access_token_expires_min),
    )


def create_refresh_token(user, sid: str | None = None) -> str:
    """Refresh token sống dài — chứa id user + sid phiên."""
    payload = {"sub": str(user.id)}
    if sid:
        payload["sid"] = sid
    return _create_token(
        payload,
        settings.jwt_refresh_secret,
        timedelta(days=settings.refresh_token_expires_days),
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def decode_refresh_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_refresh_secret, algorithms=["HS256"])
