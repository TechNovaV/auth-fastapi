"""Mailer GIẢ LẬP (mock) cho dev: in ra console + ghi file sent-emails.log.

--- Đổi sang gửi mail THẬT ---
Cài thư viện và thay thân hàm send_email, ví dụ dùng SMTP chuẩn thư viện:

    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(host, port) as s:
        s.starttls(); s.login(user, pwd); s.send_message(msg)

(Hoặc dùng dịch vụ SendGrid/Mailgun/Resend qua API của họ.)
"""
from datetime import datetime
from pathlib import Path

from app.core.config import settings

# Ghi vào file ở thư mục gốc project (cùng cấp với thư mục app/).
LOG_FILE = Path(__file__).resolve().parents[2] / "sent-emails.log"


def send_email(to: str, subject: str, body: str) -> None:
    entry = (
        f"\n===== EMAIL (giả lập) @ {datetime.now().isoformat()} =====\n"
        f"From: {settings.mail_from}\n"
        f"To: {to}\n"
        f"Subject: {subject}\n\n"
        f"{body}\n"
        f"{'=' * 47}\n"
    )
    # In ra console nếu được (một số console Windows không hỗ trợ Unicode).
    try:
        print(entry)
    except UnicodeEncodeError:
        print(entry.encode("ascii", "replace").decode("ascii"))

    # Ghi file utf-8 (đây mới là nơi đáng tin để lấy OTP khi test).
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass
