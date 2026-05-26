"""Cấu hình ứng dụng — đọc từ biến môi trường / file .env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Đường dẫn .env tuyệt đối (project root) => nạp đúng dù chạy từ thư mục nào.
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # Đọc file .env, bỏ qua biến lạ không khai báo ở đây.
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH), env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"  # "development" | "production"

    # Chuỗi kết nối DB. Mặc định MySQL (đã chọn). Có thể đổi sang SQLite để chạy
    # ngay khi chưa có MySQL: sqlite:///./auth.db
    database_url: str = "mysql+pymysql://root:password@localhost:3306/auth_db"

    # JWT — token kép, 2 secret KHÁC NHAU.
    jwt_secret: str = "change-me-access-secret"
    jwt_refresh_secret: str = "change-me-refresh-secret"
    access_token_expires_min: int = 15      # access token sống ngắn
    refresh_token_expires_days: int = 7      # refresh token sống dài

    bcrypt_rounds: int = 12                   # số vòng bcrypt (càng cao càng an toàn/chậm)

    # CORS: danh sách origin được phép, phân tách bằng dấu phẩy.
    cors_origins: str = "http://localhost:8000"

    # Quên mật khẩu
    otp_ttl_minutes: int = 5
    mail_from: str = "no-reply@auth-demo.local"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
