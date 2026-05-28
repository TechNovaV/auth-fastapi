"""Endpoint quản lý phiên/thiết bị.

Yêu cầu: dùng for/while cơ bản khi lọc/xoá phiên — đã hiện thực ở
session_repository (revoke_others, list_active_for_user, ...).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_session_id, get_current_user
from app.db.database import get_db
from app.models.user import User
from app.repositories import session_repository as sessions
from app.schemas.sessions import RevokedCountOut, SessionOut

router = APIRouter()


@router.get("/sessions", response_model=list[SessionOut])
def list_my_sessions(
    user: User = Depends(get_current_user),
    sid: str = Depends(get_current_session_id),
    db: Session = Depends(get_db),
):
    """Liệt kê các phiên đang hoạt động của user; đánh dấu phiên hiện tại."""
    active = sessions.list_active_for_user(db, user.id)

    # Dựng response bằng vòng for cơ bản (KHÔNG dùng list comprehension).
    result: list[SessionOut] = []
    for sess in active:
        result.append(
            SessionOut(
                session_id=sess.session_id,
                device_name=sess.device_name,
                user_agent=sess.user_agent,
                ip_address=sess.ip_address,
                created_at=sess.created_at,
                last_active=sess.last_active,
                is_current=(sess.session_id == sid),
            )
        )
    return result


@router.post("/sessions/logout-others", response_model=RevokedCountOut)
def logout_other_sessions(
    user: User = Depends(get_current_user),
    sid: str = Depends(get_current_session_id),
    db: Session = Depends(get_db),
):
    """Đăng xuất khỏi tất cả thiết bị KHÁC, giữ phiên hiện tại."""
    n = sessions.revoke_others(db, user.id, keep_session_id=sid)
    return {"message": f"Đã đăng xuất khỏi {n} thiết bị khác.", "revoked": n}


@router.delete("/sessions/{session_id}", response_model=RevokedCountOut)
def revoke_specific_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Đăng xuất 1 phiên cụ thể (theo session_id)."""
    ok = sessions.revoke_one(db, user.id, session_id)
    return {"message": ("Đã đăng xuất phiên" if ok else "Không tìm thấy phiên"), "revoked": 1 if ok else 0}
