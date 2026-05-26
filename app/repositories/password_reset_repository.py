"""Tầng Data: truy cập bảng password_resets."""
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import PasswordReset
from app.utils.timeutil import utcnow


def invalidate_all_for_user(db: Session, user_id: int) -> None:
    """Huỷ mọi OTP chưa dùng của user (trước khi phát mã mới)."""
    db.execute(
        update(PasswordReset)
        .where(PasswordReset.user_id == user_id, PasswordReset.used.is_(False))
        .values(used=True)
    )
    db.commit()


def create(db: Session, *, user_id: int, otp_hash: str, ttl_minutes: int) -> PasswordReset:
    pr = PasswordReset(
        user_id=user_id,
        otp_hash=otp_hash,
        expires_at=utcnow() + timedelta(minutes=ttl_minutes),
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def find_latest_valid(db: Session, user_id: int) -> PasswordReset | None:
    """OTP mới nhất còn hiệu lực (chưa dùng, chưa hết hạn)."""
    return db.scalar(
        select(PasswordReset)
        .where(
            PasswordReset.user_id == user_id,
            PasswordReset.used.is_(False),
            PasswordReset.expires_at > utcnow(),
        )
        .order_by(PasswordReset.id.desc())
    )


def increment_attempts(db: Session, pr: PasswordReset) -> None:
    pr.attempts += 1
    db.commit()


def mark_used(db: Session, pr: PasswordReset) -> None:
    pr.used = True
    db.commit()
