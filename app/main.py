"""Điểm khởi chạy FastAPI: cấu hình CORS, tạo bảng, gắn router, phục vụ frontend."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_phone import router as phone_router
from app.api.routes_sessions import router as sessions_router
from app.api.routes_webauthn import router as webauthn_router
from app.core.config import settings
from app.db.database import Base, engine
from app.models import user as _user_models  # noqa: F401  (import để create_all thấy model)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

# Tạo bảng nếu chưa có (tiện cho dev; production nên dùng Alembic migration).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth API (FastAPI + MySQL)")

# CORS chặt: chỉ cho phép origin trong whitelist, bật credentials để gửi cookie.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


# Tất cả endpoint API dưới tiền tố /api (đăng ký TRƯỚC khi mount static "/").
app.include_router(auth_router, prefix="/api")
app.include_router(phone_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(webauthn_router, prefix="/api")

# Phục vụ frontend tĩnh tại "/" => mở http://localhost:8000 là thấy giao diện.
# Cùng origin với API nên cookie refresh (SameSite=Strict) hoạt động.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
