"""Endpoint WebAuthn: đăng ký / đăng nhập bằng vân tay - FaceID."""
import json

from fastapi import APIRouter, Body, Depends, Request, Response
from fastapi.responses import Response as FastResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, request_context
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import AuthOut, MessageOut
from app.services import webauthn_service

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


# ---------- Đăng ký credential (cần đã đăng nhập) ----------

@router.post("/webauthn/register/begin")
def webauthn_register_begin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Trả về JSON do thư viện webauthn build sẵn (đã base64url-encode đúng chuẩn).
    options_json = webauthn_service.begin_registration(db, user)
    return FastResponse(content=options_json, media_type="application/json")


@router.post("/webauthn/register/finish", response_model=MessageOut)
def webauthn_register_finish(
    credential: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return webauthn_service.finish_registration(db, user, credential)


# ---------- Đăng nhập bằng credential (không cần token sẵn) ----------

@router.post("/webauthn/login/begin")
def webauthn_login_begin(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    username = (body.get("username") or "").strip()
    options_json = webauthn_service.begin_authentication(db, username)
    return FastResponse(content=options_json, media_type="application/json")


@router.post("/webauthn/login/finish", response_model=AuthOut)
def webauthn_login_finish(
    body: dict = Body(...),
    request: Request = None,
    response: Response = None,
    db: Session = Depends(get_db),
):
    ua, ip = request_context(request)
    username = (body.get("username") or "").strip()
    credential = body.get("credential") or {}
    user, access_token, refresh_token = webauthn_service.finish_authentication(
        db,
        username=username,
        credential_json=credential,
        user_agent=ua,
        ip_address=ip,
    )
    _set_refresh_cookie(response, refresh_token)
    return {"message": "Đăng nhập bằng vân tay/FaceID thành công", "user": user, "access_token": access_token}
