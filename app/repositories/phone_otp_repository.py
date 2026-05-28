"""Tầng Data: bảng phone_otps (OTP đăng nhập SMS)."""
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import PhoneOtp
from app.utils.timeutil import utcnow


def invalidate_all_for_phone(db: Session, phone: str) -> None:
    """Huỷ mọi OTP chưa dùng của số này trước khi phát mã mới."""
    db.execute(
        update(PhoneOtp)
        .where(PhoneOtp.phone == phone, PhoneOtp.used.is_(False))
        .values(used=True)
    )
    db.commit()


def create(db: Session, *, phone: str, otp_hash: str, ttl_minutes: int) -> PhoneOtp:
    pr = PhoneOtp(
        phone=phone,
        otp_hash=otp_hash,
        expires_at=utcnow() + timedelta(minutes=ttl_minutes),
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def find_latest_valid(db: Session, phone: str) -> PhoneOtp | None:
    return db.scalar(
        select(PhoneOtp)
        .where(
            PhoneOtp.phone == phone,
            PhoneOtp.used.is_(False),
            PhoneOtp.expires_at > utcnow(),
        )
        .order_by(PhoneOtp.id.desc())
    )


def increment_attempts(db: Session, pr: PhoneOtp) -> None:
    pr.attempts += 1
    db.commit()


def mark_used(db: Session, pr: PhoneOtp) -> None:
    pr.used = True
    db.commit()
