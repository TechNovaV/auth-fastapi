"""Tiện ích thời gian.

Dùng datetime UTC dạng "naive" (không gắn tzinfo) để so sánh nhất quán giữa
SQLite và MySQL (tránh lỗi so sánh aware vs naive khi đọc lại từ DB).
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
