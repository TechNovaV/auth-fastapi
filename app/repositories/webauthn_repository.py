"""Tầng Data: bảng webauthn_credentials."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import WebAuthnCredential


def create(
    db: Session,
    *,
    user_id: int,
    credential_id: bytes,
    public_key: bytes,
    sign_count: int,
    transports: str | None,
) -> WebAuthnCredential:
    cred = WebAuthnCredential(
        user_id=user_id,
        credential_id=credential_id,
        public_key=public_key,
        sign_count=sign_count,
        transports=transports,
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return cred


def find_by_credential_id(db: Session, credential_id: bytes) -> WebAuthnCredential | None:
    return db.scalar(select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id))


def list_for_user(db: Session, user_id: int) -> list[WebAuthnCredential]:
    return list(
        db.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.user_id == user_id)
        )
    )


def update_sign_count(db: Session, cred: WebAuthnCredential, new_count: int) -> None:
    cred.sign_count = new_count
    db.commit()
