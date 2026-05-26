"""Pydantic schemas: định nghĩa & validate dữ liệu vào/ra.

Pydantic tự kiểm tra kiểu + định dạng (vd EmailStr) ngay ở cửa ngõ API =>
chống dữ liệu bẩn. Kết hợp ORM tham số hoá => chống SQL/NoSQL Injection.
"""
import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,30}$")
OTP_RE = re.compile(r"^\d{6}$")


def validate_password_strength(password: str) -> str:
    """Mật khẩu mạnh: 8-72 ký tự, có chữ cái, chữ số và ký tự đặc biệt.

    Dùng vòng lặp for cơ bản để duyệt từng ký tự cho dễ theo dõi.
    """
    if len(password) < 8:
        raise ValueError("Mật khẩu tối thiểu 8 ký tự")
    if len(password.encode("utf-8")) > 72:
        # bcrypt chỉ dùng 72 byte đầu => chặn để tránh hiểu nhầm.
        raise ValueError("Mật khẩu tối đa 72 ký tự")

    has_letter = False
    has_digit = False
    has_special = False
    for ch in password:
        if ch.isalpha():
            has_letter = True
        elif ch.isdigit():
            has_digit = True
        else:
            has_special = True

    if not has_letter:
        raise ValueError("Mật khẩu phải có ít nhất 1 chữ cái")
    if not has_digit:
        raise ValueError("Mật khẩu phải có ít nhất 1 chữ số")
    if not has_special:
        raise ValueError("Mật khẩu phải có ít nhất 1 ký tự đặc biệt")
    return password


# ---------- Request ----------

class RegisterIn(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: str) -> str:
        v = v.strip()
        if not USERNAME_RE.match(v):
            raise ValueError('Tên đăng nhập 3-30 ký tự, chỉ gồm chữ, số, "_" hoặc "."')
        return v

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    @field_validator("otp")
    @classmethod
    def _check_otp(cls, v: str) -> str:
        if not OTP_RE.match(v or ""):
            raise ValueError("Mã OTP phải gồm 6 chữ số")
        return v

    @field_validator("new_password")
    @classmethod
    def _check_new_password(cls, v: str) -> str:
        return validate_password_strength(v)


# ---------- Response ----------

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime | None = None
    last_login: datetime | None = None

    # Cho phép tạo từ ORM object (user.id, user.username, ...).
    model_config = {"from_attributes": True}


class AuthOut(BaseModel):
    message: str
    user: UserOut
    access_token: str
    token_type: str = "bearer"


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageOut(BaseModel):
    message: str
