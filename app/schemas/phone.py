"""Schemas cho luồng OTP đăng nhập bằng số điện thoại."""
import re

from pydantic import BaseModel, field_validator

# Cho phép tuỳ chọn dấu + đầu, theo sau là 8-15 chữ số.
PHONE_RE = re.compile(r"^\+?[0-9]{8,15}$")


def _normalize_phone(v: str) -> str:
    """Chuẩn hoá: bỏ khoảng trắng/dấu gạch, giữ + nếu có."""
    s = (v or "").strip().replace(" ", "").replace("-", "").replace(".", "")
    if not PHONE_RE.match(s):
        raise ValueError("Số điện thoại không hợp lệ (8-15 chữ số, có thể có dấu + ở đầu)")
    return s


class PhoneOtpRequestIn(BaseModel):
    phone: str
    recaptcha_token: str | None = None

    @field_validator("phone")
    @classmethod
    def _v_phone(cls, v: str) -> str:
        return _normalize_phone(v)


class PhoneOtpVerifyIn(BaseModel):
    phone: str
    otp: str
    # Khi user mới đăng ký qua phone, có thể đặt thêm username (tuỳ chọn).
    username: str | None = None

    @field_validator("phone")
    @classmethod
    def _v_phone(cls, v: str) -> str:
        return _normalize_phone(v)

    @field_validator("otp")
    @classmethod
    def _v_otp(cls, v: str) -> str:
        if not re.fullmatch(r"\d{6}", v or ""):
            raise ValueError("Mã OTP phải gồm 6 chữ số")
        return v
