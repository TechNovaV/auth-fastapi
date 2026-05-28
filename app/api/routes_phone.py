"""Endpoint cho luồng đăng nhập SMS-OTP."""
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import request_context
from app.core.config import settings
from app.db.database import get_db
from app.schemas.auth import AuthOut, MessageOut
from app.schemas.phone import PhoneOtpRequestIn, PhoneOtpVerifyIn
from app.services import phone_otp_service
from app.utils.recaptcha import verify_recaptcha

router = APIRouter()

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        max_age=settings.refresh_token_expires_days * 24 * 3600,
        path="/api",
    )


@router.post("/request-otp", response_model=MessageOut)
def request_otp(data: PhoneOtpRequestIn, db: Session = Depends(get_db)):
    # Chống bot: yêu cầu reCAPTCHA cho endpoint gửi SMS (đắt + dễ bị abuse).
    verify_recaptcha(data.recaptcha_token, expected_action="request_otp")
    msg = phone_otp_service.request_otp(db, data.phone)
    return {"message": msg}


@router.post("/verify-otp", response_model=AuthOut, status_code=status.HTTP_200_OK)
def verify_otp(
    data: PhoneOtpVerifyIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ua, ip = request_context(request)
    user, access_token, refresh_token = phone_otp_service.verify_otp(
        db,
        phone=data.phone,
        otp=data.otp,
        username=data.username,
        user_agent=ua,
        ip_address=ip,
    )
    _set_refresh_cookie(response, refresh_token)
    return {"message": "Xác minh OTP thành công", "user": user, "access_token": access_token}
