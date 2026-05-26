"""Models (bảng) cho SQLAlchemy ORM."""
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    # Schema bảng User theo yêu cầu: ID, Username, Email, PasswordHash, Role,
    # CreatedAt, LastLogin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # hash bcrypt, KHÔNG lưu mật khẩu gốc
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")  # mặc định 'user'
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PasswordReset(Base):
    """Lưu mã OTP đặt lại mật khẩu (chỉ lưu HASH của OTP)."""
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # hạn 5 phút
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
