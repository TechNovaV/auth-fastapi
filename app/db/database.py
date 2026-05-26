"""Thiết lập SQLAlchemy: engine, session, Base.

Dùng ORM => mọi truy vấn đều tham số hoá tự động => chống SQL Injection.
Đổi DB chỉ cần đổi DATABASE_URL (MySQL <-> SQLite), code không cần sửa.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Chuẩn hoá URL Postgres: Render/Heroku trả "postgres://" nhưng SQLAlchemy 2.0
# yêu cầu "postgresql://" và cần khai báo driver (psycopg2).
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = "postgresql+psycopg2://" + db_url[len("postgres://"):]
elif db_url.startswith("postgresql://"):
    db_url = "postgresql+psycopg2://" + db_url[len("postgresql://"):]

# SQLite cần check_same_thread=False khi dùng trong web server đa luồng.
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # tự kiểm tra kết nối "chết" trước khi dùng
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    """Dependency của FastAPI: mở session cho mỗi request rồi đóng lại."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
