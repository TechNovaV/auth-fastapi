"""Service: đăng nhập / đăng ký bằng OTP qua SMS."""
import secrets
import uuid

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core import security
from app.repositories import user_repository as users
from app.repositories import phone_otp_repository as otps
from app.repositories import session_repository as sessions
from app.utils import sms
from app.utils.device import parse_device_name
from app.utils.timeutil import utcnow


def _generate_otp() -> str:
    """OTP 6 số bằng nguồn ngẫu nhiên an toàn (crypto)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def request_otp(db: Session, phone: str) -> str:
    """Tạo & 'gửi' OTP cho 1 số điện thoại (TTL 2 phút)."""
    # Chống gửi quá dày (mỗi <SMS_OTP_RESEND_SECONDS> giây mới được xin mã mới).
    latest = otps.find_latest_valid(db, phone)
    if latest:
        wait = settings.sms_otp_resend_seconds - (utcnow() - latest.created_at).total_seconds()
        if wait > 0:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Vui lòng đợi {int(wait)} giây nữa rồi xin mã mới.",
            )

    # Huỷ các mã cũ + sinh mã mới.
    otps.invalidate_all_for_phone(db, phone)
    otp = _generate_otp()
    otp_hash = bcrypt.hashpw(
        otp.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    ).decode("utf-8")
    otps.create(db, phone=phone, otp_hash=otp_hash, ttl_minutes=settings.sms_otp_ttl_minutes)

    sms.send_sms(
        to=phone,
        message=f"[Auth System] Ma OTP cua ban la: {otp}. Hieu luc {settings.sms_otp_ttl_minutes} phut.",
    )
    return f"Đã gửi OTP đến {phone} (hết hạn sau {settings.sms_otp_ttl_minutes} phút)."


def verify_otp(
    db: Session,
    *,
    phone: str,
    otp: str,
    username: str | None,
    user_agent: str,
    ip_address: str,
):
    """Xác minh OTP -> đăng nhập / đăng ký tự động -> cấp token + tạo phiên."""
    generic = HTTPException(status.HTTP_400_BAD_REQUEST, "Mã OTP không đúng hoặc đã hết hạn")

    pr = otps.find_latest_valid(db, phone)
    if not pr:
        raise generic
    if pr.attempts >= 5:
        otps.mark_used(db, pr)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Nhập sai quá nhiều lần. Vui lòng xin mã mới.")

    if not bcrypt.checkpw(otp.encode("utf-8"), pr.otp_hash.encode("utf-8")):
        otps.increment_attempts(db, pr)
        raise generic

    otps.mark_used(db, pr)

    # Tìm user theo phone; nếu chưa có thì tạo (username = phone nếu không nhập, đảm bảo duy nhất).
    user = users.get_by_phone(db, phone)
    if not user:
        candidate = (username or f"user_{phone}").strip()[:30]
        # Đảm bảo username không trùng (vòng for cơ bản, thêm hậu tố nếu trùng).
        base = candidate
        i = 0
        while users.get_by_username(db, candidate) is not None:
            i += 1
            candidate = f"{base[:26]}{i}"
        user = users.create(db, username=candidate, phone=phone)

    users.update_last_login(db, user)

    # Tạo phiên mới.
    sid = str(uuid.uuid4())
    sessions.create(
        db,
        session_id=sid,
        user_id=user.id,
        device_name=parse_device_name(user_agent),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    access = security.create_access_token(user, sid)
    refresh = security.create_refresh_token(user, sid)
    return user, access, refresh
