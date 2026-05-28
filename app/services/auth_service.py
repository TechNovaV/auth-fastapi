"""Tầng Domain: logic Auth — token kép + theo dõi phiên (DeviceSession)."""
import secrets
import uuid

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import rate_limit, security
from app.core.config import settings
from app.repositories import user_repository as users
from app.repositories import password_reset_repository as resets
from app.repositories import session_repository as sessions
from app.schemas.auth import RegisterIn, LoginIn, ResetIn
from app.utils import mailer
from app.utils.device import parse_device_name


def _start_session(db: Session, user, *, user_agent: str, ip_address: str) -> str:
    """Tạo 1 DeviceSession mới và trả về session_id (UUID)."""
    sid = str(uuid.uuid4())
    sessions.create(
        db,
        session_id=sid,
        user_id=user.id,
        device_name=parse_device_name(user_agent),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return sid


def _issue_tokens(user, sid: str) -> tuple[str, str]:
    return security.create_access_token(user, sid), security.create_refresh_token(user, sid)


# ---------- Đăng ký / Đăng nhập / Refresh / Logout ----------

def register(db: Session, data: RegisterIn, *, user_agent: str, ip_address: str):
    if users.get_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã được đăng ký")
    if users.get_by_username(db, data.username):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tên đăng nhập này đã được sử dụng")

    password_hash = security.hash_password(data.password)
    user = users.create(db, username=data.username, email=data.email, password_hash=password_hash)

    sid = _start_session(db, user, user_agent=user_agent, ip_address=ip_address)
    access, refresh = _issue_tokens(user, sid)
    return user, access, refresh


def login(db: Session, data: LoginIn, *, user_agent: str, ip_address: str):
    locked = rate_limit.minutes_locked(ip_address, data.email)
    if locked > 0:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Đăng nhập sai quá nhiều lần. Thử lại sau {locked} phút.",
        )

    user = users.get_by_email(db, data.email)
    if not user or not user.password_hash or not security.verify_password(data.password, user.password_hash):
        rate_limit.record_failure(ip_address, data.email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")

    rate_limit.reset(ip_address, data.email)
    users.update_last_login(db, user)

    sid = _start_session(db, user, user_agent=user_agent, ip_address=ip_address)
    access, refresh = _issue_tokens(user, sid)
    return user, access, refresh


def refresh(db: Session, refresh_token: str, *, user_agent: str, ip_address: str):
    """Cấp lại access token từ refresh token; kiểm tra phiên còn hợp lệ."""
    try:
        payload = security.decode_refresh_token(refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token không hợp lệ hoặc đã hết hạn")

    sid = payload.get("sid")
    if not sid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên không hợp lệ")

    sess = sessions.find_by_sid(db, sid)
    if not sess or sess.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đã bị thu hồi")

    user = users.get_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Người dùng không tồn tại")

    sessions.update_last_active(db, sess)
    access, new_refresh = _issue_tokens(user, sid)  # cùng sid (đang chỉ xoay token)
    return user, access, new_refresh


def logout(db: Session, refresh_token: str | None) -> None:
    """Revoke phiên ứng với refresh token (nếu giải mã được)."""
    if not refresh_token:
        return
    try:
        payload = security.decode_refresh_token(refresh_token)
    except jwt.PyJWTError:
        return
    sid = payload.get("sid")
    if not sid:
        return
    sess = sessions.find_by_sid(db, sid)
    if sess and sess.revoked_at is None:
        sessions.revoke(db, sess)


# ---------- Quên mật khẩu (OTP qua email) — giữ nguyên ----------

def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def forgot_password(db: Session, email: str) -> str:
    user = users.get_by_email(db, email)
    if user:
        resets.invalidate_all_for_user(db, user.id)
        otp = _generate_otp()
        otp_hash = bcrypt.hashpw(otp.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode("utf-8")
        resets.create(db, user_id=user.id, otp_hash=otp_hash, ttl_minutes=settings.otp_ttl_minutes)
        mailer.send_email(
            to=user.email,
            subject="Mã đặt lại mật khẩu",
            body=(
                f"Xin chào {user.username},\n\n"
                f"Mã OTP đặt lại mật khẩu của bạn là: {otp}\n"
                f"Mã có hiệu lực trong {settings.otp_ttl_minutes} phút.\n"
            ),
        )
    return "Nếu email tồn tại, mã OTP đã được gửi. Vui lòng kiểm tra hộp thư."


def reset_password(db: Session, data: ResetIn) -> str:
    generic = HTTPException(status.HTTP_400_BAD_REQUEST, "Mã OTP không đúng hoặc đã hết hạn")
    user = users.get_by_email(db, data.email)
    if not user:
        raise generic

    pr = resets.find_latest_valid(db, user.id)
    if not pr:
        raise generic
    if pr.attempts >= rate_limit.MAX_FAILURES:
        resets.mark_used(db, pr)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Nhập sai quá nhiều lần. Vui lòng yêu cầu mã mới.")

    if not bcrypt.checkpw(data.otp.encode("utf-8"), pr.otp_hash.encode("utf-8")):
        resets.increment_attempts(db, pr)
        raise generic

    users.update_password(db, user, security.hash_password(data.new_password))
    resets.mark_used(db, pr)
    return "Đặt lại mật khẩu thành công. Vui lòng đăng nhập lại."
