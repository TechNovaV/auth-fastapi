"""Tầng Data: truy cập bảng users qua SQLAlchemy (đã tham số hoá)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.timeutil import utcnow


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create(db: Session, *, username: str, email: str, password_hash: str, role: str = "user") -> User:
    user = User(username=username, email=email, password_hash=password_hash, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: User) -> None:
    user.last_login = utcnow()
    db.commit()


def update_password(db: Session, user: User, password_hash: str) -> None:
    user.password_hash = password_hash
    db.commit()


def list_all(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))
