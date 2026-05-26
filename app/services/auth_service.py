"""Tầng Domain: logic nghiệp vụ Auth.

Để code đơn giản, service ném thẳng HTTPException của FastAPI khi có lỗi
nghiệp vụ (tầng API chỉ việc gọi và trả kết quả).
"""
import secrets

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import rate_limit, security
from app.core.config import settings
from app.repositories import user_repository as users
from app.repositories import password_reset_repository as resets
from app.schemas.auth import RegisterIn, LoginIn, ResetIn
from app.utils import mailer


def _issue_tokens(user) -> tuple[str, str]:
    """Cấp đồng thời access token + refresh token."""
    return security.create_access_token(user), security.create_refresh_token(user)


def register(db: Session, data: RegisterIn):
    # Pydantic đã validate username/email/mật khẩu mạnh ở schema.
    if users.get_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã được đăng ký")
    if users.get_by_username(db, data.username):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tên đăng nhập này đã được sử dụng")

    password_hash = security.hash_password(data.password)
    # role mặc định 'user' (KHÔNG cho client tự đặt role).
    user = users.create(db, username=data.username, email=data.email, password_hash=password_hash)

    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token


def login(db: Session, data: LoginIn, ip: str):
    # 1) Chống brute force: đang bị khoá thì chặn ngay.
    locked = rate_limit.minutes_locked(ip, data.email)
    if locked > 0:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Đăng nhập sai quá nhiều lần. Thử lại sau {locked} phút.",
        )

    user = users.get_by_email(db, data.email)

    # 2) Dùng chung 1 thông báo cho "không có user" và "sai mật khẩu".
    if not user or not security.verify_password(data.password, user.password_hash):
        rate_limit.record_failure(ip, data.email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")

    # 3) Đăng nhập thành công.
    rate_limit.reset(ip, data.email)
    users.update_last_login(db, user)

    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token


def refresh(db: Session, refresh_token: str):
    import jwt

    try:
        payload = security.decode_refresh_token(refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token không hợp lệ hoặc đã hết hạn")

    user = users.get_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Người dùng không tồn tại")

    access_token, new_refresh = _issue_tokens(user)  # xoay vòng refresh token
    return user, access_token, new_refresh


# ---------- Quên mật khẩu (OTP) ----------

def _generate_otp() -> str:
    """OTP 6 chữ số bằng nguồn ngẫu nhiên an toàn."""
    return f"{secrets.randbelow(1_000_000):06d}"


def forgot_password(db: Session, email: str) -> str:
    """Bước 1: gửi OTP. Luôn trả thông báo chung để chống dò email."""
    user = users.get_by_email(db, email)
    if user:
        resets.invalidate_all_for_user(db, user.id)  # huỷ mã cũ
        otp = _generate_otp()
        otp_hash = bcrypt.hashpw(otp.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode("utf-8")
        resets.create(db, user_id=user.id, otp_hash=otp_hash, ttl_minutes=settings.otp_ttl_minutes)

        mailer.send_email(
            to=user.email,
            subject="Mã đặt lại mật khẩu",
            body=(
                f"Xin chào {user.username},\n\n"
                f"Mã OTP đặt lại mật khẩu của bạn là: {otp}\n"
                f"Mã có hiệu lực trong {settings.otp_ttl_minutes} phút.\n\n"
                f"Nếu bạn không yêu cầu, hãy bỏ qua email này."
            ),
        )

    return "Nếu email tồn tại, mã OTP đã được gửi. Vui lòng kiểm tra hộp thư."


def reset_password(db: Session, data: ResetIn) -> str:
    """Bước 2: xác minh OTP và đổi mật khẩu."""
    generic = HTTPException(status.HTTP_400_BAD_REQUEST, "Mã OTP không đúng hoặc đã hết hạn")

    user = users.get_by_email(db, data.email)
    if not user:
        raise generic

    pr = resets.find_latest_valid(db, user.id)
    if not pr:
        raise generic

    # Chống dò OTP: quá số lần thì huỷ mã.
    if pr.attempts >= rate_limit.MAX_FAILURES:
        resets.mark_used(db, pr)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Nhập sai quá nhiều lần. Vui lòng yêu cầu mã mới.")

    if not bcrypt.checkpw(data.otp.encode("utf-8"), pr.otp_hash.encode("utf-8")):
        resets.increment_attempts(db, pr)
        raise generic

    # OTP đúng => đổi mật khẩu + đánh dấu đã dùng.
    users.update_password(db, user, security.hash_password(data.new_password))
    resets.mark_used(db, pr)
    return "Đặt lại mật khẩu thành công. Vui lòng đăng nhập lại."
