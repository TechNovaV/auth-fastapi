"""Dependencies dùng chung: get_current_user, RBAC, request context."""
import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User
from app.repositories import user_repository as users


def request_context(request: Request) -> tuple[str, str]:
    """Trích User-Agent và IP từ request (dùng để ghi log phiên)."""
    ua = request.headers.get("user-agent", "")[:500]
    ip = request.client.host if request.client else "unknown"
    return ua, ip


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Đọc access token, xác minh, gắn sid vào request.state, trả về User."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Thiếu hoặc sai định dạng token")

    token = auth_header[len("Bearer "):].strip()
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token không hợp lệ hoặc đã hết hạn")

    user = users.get_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Người dùng không tồn tại")

    # Lưu session_id (sid) ra request.state để các route khác dùng (vd /sessions/logout-others).
    request.state.session_id = payload.get("sid")
    return user


def get_current_session_id(request: Request) -> str:
    """Trả về sid của phiên hiện tại (cần get_current_user đã chạy trước)."""
    sid = getattr(request.state, "session_id", None)
    if not sid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Access token thiếu thông tin phiên")
    return sid


def require_role(*allowed_roles: str):
    """RBAC: chỉ cho qua nếu role nằm trong allowed_roles."""

    def checker(user: User = Depends(get_current_user)) -> User:
        allowed = False
        for role in allowed_roles:  # for cơ bản
            if user.role == role:
                allowed = True
                break
        if not allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền truy cập tài nguyên này")
        return user

    return checker
