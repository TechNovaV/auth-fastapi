"""Chống brute force cho /api/login.

Đếm số lần đăng nhập SAI theo (IP + email). Quá 5 lần => khoá 15 phút.
Lưu trong RAM (đủ cho 1 tiến trình / môi trường học). Production nhiều instance
nên thay bằng Redis để chia sẻ trạng thái.
"""
import time

MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60  # 15 phút

# key -> {"count": int, "locked_until": float(epoch)}
_store: dict[str, dict] = {}


def _key(ip: str, email: str) -> str:
    return f"{ip}|{(email or '').lower()}"


def minutes_locked(ip: str, email: str) -> int:
    """Trả về số phút còn bị khoá (0 nếu không bị khoá)."""
    entry = _store.get(_key(ip, email))
    if entry and entry["locked_until"] > time.time():
        remaining = entry["locked_until"] - time.time()
        return int(remaining // 60) + 1
    return 0


def record_failure(ip: str, email: str) -> None:
    key = _key(ip, email)
    entry = _store.get(key, {"count": 0, "locked_until": 0})
    entry["count"] += 1
    if entry["count"] >= MAX_FAILURES:
        entry["locked_until"] = time.time() + LOCK_SECONDS
    _store[key] = entry


def reset(ip: str, email: str) -> None:
    """Đăng nhập thành công => xoá bộ đếm."""
    _store.pop(_key(ip, email), None)
