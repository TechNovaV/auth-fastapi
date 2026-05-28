"""WebAuthn / FIDO2 — đăng ký + đăng nhập bằng vân tay/FaceID (qua trình duyệt).

Luồng bảo mật rút gọn:

  ĐĂNG KÝ (cần đã đăng nhập sẵn để biết user là ai):
   1. Client gọi /webauthn/register/begin -> server sinh CHALLENGE ngẫu nhiên +
      tham số (rp, user, pubKeyCredParams...) gửi xuống.
   2. Trình duyệt kích hoạt navigator.credentials.create() -> hệ điều hành/thiết bị
      bảo mật (TPM/Secure Enclave) tạo cặp khoá public/private. Private key NẰM
      LẠI thiết bị, KHÔNG ai (kể cả server) lấy được. Vân tay/FaceID chỉ dùng
      để "mở khoá" private key trong enclave.
   3. Client gửi credential lên /webauthn/register/finish -> server VERIFY:
      attestation hợp lệ + challenge khớp + rpId khớp origin -> lưu public_key
      + credential_id vào DB.

  ĐĂNG NHẬP (không cần mật khẩu / cookie sẵn):
   1. Client gọi /webauthn/login/begin với "username" -> server tìm các credential
      đã đăng ký của user, sinh CHALLENGE ngẫu nhiên + allowCredentials, gửi xuống.
   2. Trình duyệt kích hoạt navigator.credentials.get() -> user quét vân tay/FaceID
      để mở khoá private key, KÝ challenge.
   3. Client gửi assertion lên /webauthn/login/finish -> server VERIFY chữ ký bằng
      public_key đã lưu + challenge khớp -> nếu ổn thì CẤP JWT + tạo phiên như
      đăng nhập thường.

  Token an toàn sau khi xác thực: chữ ký được verify trên server -> server CHỦ
  ĐỘNG cấp Access/Refresh Token mới (giống login email/password). Token KHÔNG
  được lưu sẵn trên thiết bị; chỉ private key vân tay nằm trong enclave.

Lưu ý dev local: trình duyệt yêu cầu HTTPS hoặc http://localhost. RP_ID phải là
domain (không port), RP_ORIGIN là origin đầy đủ.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core import security
from app.core.config import settings
from app.repositories import session_repository as sessions
from app.repositories import user_repository as users
from app.repositories import webauthn_repository as creds
from app.utils.device import parse_device_name

# Lưu challenge tạm thời theo (user_id, mục đích). Cho đơn giản dùng RAM —
# production nên Redis để chia sẻ giữa nhiều instance + tự hết hạn.
_pending: dict[str, bytes] = {}


def _key(scope: str, ident: str) -> str:
    return f"{scope}:{ident}"


# ---------- Đăng ký credential ----------

def begin_registration(db: Session, user) -> str:
    """Sinh registration options + lưu challenge tạm. Trả về JSON (chuỗi)."""
    existing = creds.list_for_user(db, user.id)

    # Loại các credential đã có để tránh đăng ký trùng (vòng for cơ bản).
    exclude: list[PublicKeyCredentialDescriptor] = []
    for c in existing:
        exclude.append(PublicKeyCredentialDescriptor(id=c.credential_id))

    options = generate_registration_options(
        rp_id=settings.rp_id,
        rp_name=settings.rp_name,
        user_id=str(user.id).encode("utf-8"),
        user_name=user.username,
        user_display_name=user.username,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )

    _pending[_key("reg", str(user.id))] = options.challenge
    return options_to_json(options)


def finish_registration(db: Session, user, credential_json: dict) -> dict:
    """Verify response từ trình duyệt và lưu khoá công khai."""
    challenge = _pending.pop(_key("reg", str(user.id)), None)
    if not challenge:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không có phiên đăng ký đang chờ")

    try:
        verification = verify_registration_response(
            credential=credential_json,
            expected_challenge=challenge,
            expected_origin=settings.rp_origin,
            expected_rp_id=settings.rp_id,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Đăng ký WebAuthn thất bại: {e}")

    creds.create(
        db,
        user_id=user.id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=None,
    )
    return {"message": "Đã đăng ký vân tay / FaceID thành công"}


# ---------- Đăng nhập bằng credential ----------

def begin_authentication(db: Session, username: str) -> str:
    user = users.get_by_username(db, username)
    if not user:
        # Tránh lộ user nào tồn tại: vẫn sinh options nhưng allow_credentials rỗng.
        allow: list[PublicKeyCredentialDescriptor] = []
        challenge_key = _key("auth", f"anon-{uuid.uuid4()}")
    else:
        user_creds = creds.list_for_user(db, user.id)
        allow = []
        for c in user_creds:    # for cơ bản
            allow.append(PublicKeyCredentialDescriptor(id=c.credential_id))
        challenge_key = _key("auth", str(user.id))

    options = generate_authentication_options(
        rp_id=settings.rp_id,
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    _pending[challenge_key] = options.challenge
    return options_to_json(options)


def finish_authentication(
    db: Session,
    *,
    username: str,
    credential_json: dict,
    user_agent: str,
    ip_address: str,
):
    user = users.get_by_username(db, username)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Xác thực thất bại")

    challenge = _pending.pop(_key("auth", str(user.id)), None)
    if not challenge:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không có phiên đăng nhập đang chờ")

    # Tìm credential trùng id (vòng for cơ bản).
    raw_id_b64 = credential_json.get("rawId") or credential_json.get("id")
    from webauthn.helpers import base64url_to_bytes
    try:
        raw_id = base64url_to_bytes(raw_id_b64)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "credential id không hợp lệ")

    matched = None
    for c in creds.list_for_user(db, user.id):
        if c.credential_id == raw_id:
            matched = c
            break

    if not matched:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credential chưa được đăng ký")

    try:
        verification = verify_authentication_response(
            credential=credential_json,
            expected_challenge=challenge,
            expected_origin=settings.rp_origin,
            expected_rp_id=settings.rp_id,
            credential_public_key=matched.public_key,
            credential_current_sign_count=matched.sign_count,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Xác thực thất bại: {e}")

    creds.update_sign_count(db, matched, verification.new_sign_count)
    users.update_last_login(db, user)

    # Cấp token + tạo phiên (giống đăng nhập thường).
    sid = str(uuid.uuid4())
    sessions.create(
        db,
        session_id=sid,
        user_id=user.id,
        device_name=parse_device_name(user_agent),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return (
        user,
        security.create_access_token(user, sid),
        security.create_refresh_token(user, sid),
    )
