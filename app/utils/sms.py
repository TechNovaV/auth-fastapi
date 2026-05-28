"""SMS gửi GIẢ LẬP cho dev: in ra console + ghi file sent-sms.log.

--- Đổi sang gửi SMS THẬT ---
Thay thân hàm send_sms để gọi nhà cung cấp:
    Twilio:   pip install twilio; twilio.rest.Client(SID, TOKEN).messages.create(...)
    AWS SNS:  pip install boto3; boto3.client('sns').publish(PhoneNumber=..., Message=...)
    eSMS/VMG/SpeedSMS: gọi REST API của họ qua urllib/httpx.
"""
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "sent-sms.log"


def send_sms(to: str, message: str) -> None:
    entry = (
        f"\n===== SMS (giả lập) @ {datetime.now().isoformat()} =====\n"
        f"To: {to}\n"
        f"Message: {message}\n"
        f"{'=' * 47}\n"
    )
    try:
        print(entry)
    except UnicodeEncodeError:
        print(entry.encode("ascii", "replace").decode("ascii"))

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass
