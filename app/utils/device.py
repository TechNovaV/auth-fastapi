"""Parse chuỗi User-Agent thành tên thiết bị ngắn gọn.

Dùng vòng for/while cơ bản (không regex phức tạp) để dễ đọc và dễ tinh chỉnh.
Trả về dạng "<Browser> on <OS>" — ví dụ "Chrome on Windows".
"""

# Thứ tự ưu tiên QUAN TRỌNG: trình duyệt Edge/Brave/Opera cũng chứa "Chrome",
# nên duyệt từ cụ thể -> tổng quát.
_BROWSERS = [
    ("Edg/", "Edge"),
    ("OPR/", "Opera"),
    ("Brave", "Brave"),
    ("Firefox", "Firefox"),
    ("Chrome", "Chrome"),
    ("Safari", "Safari"),
]

_OS = [
    ("Windows NT", "Windows"),
    ("Mac OS X", "macOS"),
    ("Android", "Android"),
    ("iPhone", "iPhone"),
    ("iPad", "iPad"),
    ("Linux", "Linux"),
]


def _find_first(ua: str, candidates: list[tuple[str, str]]) -> str:
    """Trả về nhãn đầu tiên có chuỗi key xuất hiện trong UA (dùng for cơ bản)."""
    for key, label in candidates:
        if key in ua:
            return label
    return "Unknown"


def parse_device_name(user_agent: str) -> str:
    if not user_agent:
        return "Unknown device"
    ua = user_agent[:500]
    browser = _find_first(ua, _BROWSERS)
    os_name = _find_first(ua, _OS)
    return f"{browser} on {os_name}"
