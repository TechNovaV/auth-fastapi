"""Tầng Data: bảng device_sessions.

Yêu cầu: khi LỌC/XOÁ phiên cũ trong danh sách, dùng vòng for/while cơ bản
thay cho list comprehension hay filter() để code dễ đọc và dễ tinh chỉnh.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import DeviceSession
from app.utils.timeutil import utcnow


def create(
    db: Session,
    *,
    session_id: str,
    user_id: int,
    device_name: str,
    user_agent: str,
    ip_address: str,
) -> DeviceSession:
    sess = DeviceSession(
        session_id=session_id,
        user_id=user_id,
        device_name=device_name,
        user_agent=user_agent[:500],
        ip_address=ip_address[:64],
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def find_by_sid(db: Session, session_id: str) -> DeviceSession | None:
    return db.scalar(select(DeviceSession).where(DeviceSession.session_id == session_id))


def update_last_active(db: Session, sess: DeviceSession) -> None:
    sess.last_active = utcnow()
    db.commit()


def revoke(db: Session, sess: DeviceSession) -> None:
    sess.revoked_at = utcnow()
    db.commit()


def list_active_for_user(db: Session, user_id: int) -> list[DeviceSession]:
    """Trả về danh sách các phiên CÒN HOẠT ĐỘNG của user (sắp xếp mới nhất trước).

    Lưu ý: dùng vòng for cơ bản để LỌC, không dùng list comprehension.
    """
    # Tải tất cả phiên của user (mới nhất trước).
    all_sessions = list(
        db.scalars(
            select(DeviceSession)
            .where(DeviceSession.user_id == user_id)
            .order_by(DeviceSession.last_active.desc())
        )
    )

    # Lọc bằng for cơ bản: chỉ giữ phiên chưa bị revoke.
    active: list[DeviceSession] = []
    for sess in all_sessions:
        if sess.revoked_at is None:
            active.append(sess)
    return active


def revoke_others(db: Session, user_id: int, keep_session_id: str) -> int:
    """Đăng xuất khỏi mọi thiết bị KHÁC (giữ phiên hiện tại).

    Trả về số phiên đã bị huỷ. Dùng vòng for cơ bản.
    """
    sessions = list_active_for_user(db, user_id)

    revoked_count = 0
    now = utcnow()
    for sess in sessions:
        if sess.session_id == keep_session_id:
            continue  # bỏ qua phiên hiện tại
        sess.revoked_at = now
        revoked_count += 1

    db.commit()
    return revoked_count


def revoke_one(db: Session, user_id: int, session_id: str) -> bool:
    """Huỷ 1 phiên cụ thể (chỉ chủ phiên mới có quyền). True nếu đã huỷ."""
    sessions = list_active_for_user(db, user_id)

    # Tìm phiên cần huỷ bằng vòng for cơ bản.
    target = None
    for sess in sessions:
        if sess.session_id == session_id:
            target = sess
            break

    if target is None:
        return False

    target.revoked_at = utcnow()
    db.commit()
    return True
