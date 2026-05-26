"""Dependencies dùng chung: lấy user hiện tại + middleware phân quyền (RBAC)."""
import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User
from app.repositories import user_repository as users


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Đọc access token từ header 'Authorization: Bearer <token>' và xác thực."""
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
    return user


def require_role(*allowed_roles: str):
    """Factory tạo dependency RBAC: chỉ cho qua nếu role nằm trong allowed_roles."""

    def checker(user: User = Depends(get_current_user)) -> User:
        allowed = False
        for role in allowed_roles:  # vòng lặp for cơ bản
            if user.role == role:
                allowed = True
                break
        if not allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền truy cập tài nguyên này")
        return user

    return checker
