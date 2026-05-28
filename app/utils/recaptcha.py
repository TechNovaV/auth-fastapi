"""Xác minh token Google reCAPTCHA v3 (ẩn) — chống bot.

Cách bật:
  1) Đăng ký site key + secret key tại https://www.google.com/recaptcha/admin (loại v3).
  2) Đặt biến môi trường RECAPTCHA_SECRET (secret key), RECAPTCHA_MIN_SCORE (0.5 mặc định).
  3) Frontend nhúng script reCAPTCHA và gọi grecaptcha.execute(siteKey, {action:'login'}) -> nhận token.
  4) Gửi token kèm body request lên các API nhạy cảm (/login, /register, /request-otp).
  5) Server dùng module này verify token với Google.

Nếu RECAPTCHA_SECRET chưa được đặt, verify_recaptcha() KHÔNG chặn (chế độ dev).
"""
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.config import settings

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha(token: str | None, expected_action: str | None = None) -> None:
    """Verify token reCAPTCHA v3.
    - Bỏ qua nếu chưa cấu hình RECAPTCHA_SECRET (dev).
    - Ném HTTPException 400 nếu token thiếu/sai/score thấp.
    """
    secret = settings.recaptcha_secret
    if not secret:
        # Chưa bật reCAPTCHA -> không chặn (dùng cho dev/local).
        return

    if not token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiếu reCAPTCHA token")

    data = urlencode({"secret": secret, "response": token}).encode("utf-8")
    req = Request(VERIFY_URL, data=data, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Không xác minh được reCAPTCHA")

    if not payload.get("success"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "reCAPTCHA không hợp lệ")

    # v3 trả về score 0.0..1.0; càng cao càng "giống người".
    score = float(payload.get("score", 0))
    if score < settings.recaptcha_min_score:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Yêu cầu nghi ngờ là bot (score thấp)")

    if expected_action and payload.get("action") != expected_action:
        # Chống "stolen token" reuse cho action khác.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "reCAPTCHA action không khớp")
