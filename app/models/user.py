"""Models (bảng) cho SQLAlchemy ORM."""
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, LargeBinary, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    # ID, Username, Email, PasswordHash, Role, CreatedAt, LastLogin (+ Phone cho OTP).
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    # email/phone đều có thể null, NHƯNG user mới phải có ÍT NHẤT một trong hai (kiểm tra ở service).
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    # Mật khẩu hash — có thể null cho user đăng ký bằng OTP/Google (chưa đặt mật khẩu).
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PasswordReset(Base):
    """OTP đặt lại mật khẩu (chỉ lưu HASH của OTP)."""
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PhoneOtp(Base):
    """OTP đăng nhập / xác minh số điện thoại (TTL 2 phút).

    Lưu theo phone (không cần user_id) vì có thể là user mới chưa tồn tại.
    """
    __tablename__ = "phone_otps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DeviceSession(Base):
    """Phiên đăng nhập theo thiết bị — phục vụ liệt kê & đăng xuất phiên khác."""
    __tablename__ = "device_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # session_id (UUID) được nhúng vào access/refresh token để định danh phiên.
    session_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)   # vd: "Chrome on Windows"
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # NULL = còn hoạt động


class WebAuthnCredential(Base):
    """Khoá công khai đăng ký bằng vân tay/FaceID (WebAuthn / FIDO2)."""
    __tablename__ = "webauthn_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # credential_id do trình duyệt sinh (bytes). Lưu LargeBinary để portable.
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True, nullable=False, index=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transports: Mapped[str | None] = mapped_column(String(100), nullable=True)  # "usb,nfc,internal"
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
