"""Cấp quyền admin cho 1 user theo email.

Cách dùng (từ thư mục gốc project, đã kích hoạt venv):
    python -m scripts.make_admin <email>
Ví dụ:
    python -m scripts.make_admin vinh@example.com
"""
import sys

from app.db.database import SessionLocal
from app.repositories import user_repository as users


def main() -> None:
    if len(sys.argv) < 2:
        print("Thiếu email. Cách dùng: python -m scripts.make_admin <email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    db = SessionLocal()
    try:
        user = users.get_by_email(db, email)
        if not user:
            print(f"Không tìm thấy user với email: {email}")
            return
        user.role = "admin"
        db.commit()
        print(f"Đã cấp quyền admin cho: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
