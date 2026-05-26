# Auth System — FastAPI + MySQL + HTML/CSS/JS (Clean Architecture)

Hệ thống Đăng nhập / Đăng ký an toàn: **Python (FastAPI)** + **MySQL** (qua SQLAlchemy ORM) và **Frontend HTML/CSS/JS thuần** (Clean Architecture 3 tầng + state management). FastAPI phục vụ luôn frontend nên chạy cùng origin.

> Dùng SQLAlchemy ORM nên đổi DB chỉ cần đổi `DATABASE_URL` (MySQL ⇄ SQLite). Vì máy chưa cài MySQL, `.env` mặc định dùng **SQLite** để chạy được ngay; khi có MySQL thì bỏ comment dòng MySQL.

## Cấu trúc thư mục (backend)

```
auth-fastapi/
├── app/
│   ├── main.py                      # Khởi tạo FastAPI, CORS, tạo bảng, gắn router
│   ├── core/
│   │   ├── config.py                # Settings (đọc .env)
│   │   ├── security.py              # bcrypt + JWT (token kép)
│   │   └── rate_limit.py            # Chống brute force (in-memory)
│   ├── db/
│   │   └── database.py              # Engine, Session, Base (SQLAlchemy)
│   ├── models/
│   │   └── user.py                  # Model User + PasswordReset
│   ├── schemas/
│   │   └── auth.py                  # Pydantic (validate input/output)
│   ├── repositories/                # TẦNG DATA (truy cập DB)
│   │   ├── user_repository.py
│   │   └── password_reset_repository.py
│   ├── services/                    # TẦNG DOMAIN (logic nghiệp vụ)
│   │   └── auth_service.py
│   ├── api/                         # TẦNG PRESENTATION (HTTP)
│   │   ├── deps.py                  # get_current_user + require_role (RBAC)
│   │   └── routes_auth.py           # Các endpoint
│   └── utils/
│       ├── mailer.py                # Gửi mail giả lập
│       └── timeutil.py
├── scripts/make_admin.py            # Cấp quyền admin theo email
├── frontend/                        # FRONTEND (HTML/CSS/JS, Clean Architecture)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── data/ {httpClient, tokenStorage, authRepository}      # TẦNG DATA
│       ├── domain/ {user, validators, authUseCases}             # TẦNG DOMAIN
│       ├── presentation/ {authStore (state), authView (DOM)}    # TẦNG PRESENTATION
│       └── main.js                  # composition root
├── .env / .env.example
├── requirements.txt
└── README.md
```

> **Backend** — phụ thuộc một chiều: api (Presentation) → services (Domain) → repositories (Data) → models/db.
> **Frontend** — phụ thuộc một chiều: Presentation → Domain → Data (ES modules).

## Frontend — State management & các luồng

- **Store** (`authStore.js`): một state `{ status, user, error }` (`loading | authenticated | unauthenticated`); View `subscribe` để tự render khi state đổi.
- **Auto-login** (mở/tải lại trang): access token chỉ ở RAM (mất khi reload) → `tryAutoLogin()` dùng refresh token trong cookie HttpOnly xin access token mới → gọi `/api/profile` → vào thẳng màn hình chính.
- **Logout**: xoá access token client + gọi `/api/logout` (server xoá cookie) → state về `unauthenticated` → tự điều hướng về form đăng nhập.
- **Quên mật khẩu**: màn hình 2 bước (nhập email → nhập OTP + mật khẩu mới).
- Access token giữ **in-memory** (không dùng localStorage); validate client (email, mật khẩu mạnh, khớp xác nhận).

## Database Schema — bảng `users`

| Cột | Kiểu | Ghi chú |
|-----|------|--------|
| `id` | INT PK AUTO_INCREMENT | Khoá chính |
| `username` | VARCHAR(50) UNIQUE | Tên đăng nhập (3-30 ký tự) |
| `email` | VARCHAR(255) UNIQUE | Email |
| `password_hash` | VARCHAR(255) | Hash bcrypt (không lưu mật khẩu gốc) |
| `role` | VARCHAR(20) DEFAULT `'user'` | `user` / `admin` |
| `created_at` | DATETIME | Thời điểm tạo |
| `last_login` | DATETIME NULL | Lần đăng nhập gần nhất |

Bảng phụ `password_resets` (OTP quên mật khẩu): `id, user_id, otp_hash, expires_at, attempts, used, created_at`.

## Cài đặt & chạy (local)

```cmd
cd /d D:\auth-fastapi
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        :: rồi sửa secret/DATABASE_URL nếu cần
uvicorn app.main:app --reload --port 8000
```

- Mở **http://localhost:8000** → giao diện đăng nhập/đăng ký (frontend).
- Tài liệu API tự sinh (Swagger): **http://localhost:8000/docs**
- Bảng tự tạo lúc khởi động (SQLite: file `auth.db`).
- **Dùng MySQL:** tạo database rồi đặt trong `.env`:
  `DATABASE_URL=mysql+pymysql://root:<mật_khẩu>@localhost:3306/auth_db`

Cấp quyền admin:
```cmd
python -m scripts.make_admin <email>
```

## API

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| POST | `/api/register` | Đăng ký → access token + set cookie refresh | ❌ |
| POST | `/api/login` | Đăng nhập → access token + set cookie refresh | ❌ |
| POST | `/api/refresh` | Cấp lại access token từ cookie refresh | 🍪 cookie |
| POST | `/api/logout` | Xoá cookie refresh | ❌ |
| GET | `/api/profile` | Thông tin user hiện tại | ✅ Bearer |
| POST | `/api/forgot-password` | Gửi OTP về email (giả lập) | ❌ |
| POST | `/api/reset-password` | Đổi mật khẩu bằng OTP | ❌ |
| GET | `/api/admin/users` | (Nhạy cảm) Liệt kê user | ✅ Bearer + role `admin` |

## Bảo mật

- **Băm mật khẩu bcrypt** (`core/security.py`), không lưu mật khẩu gốc.
- **Token kép:** Access (15 phút) + Refresh (7 ngày), ký bằng 2 secret khác nhau. Refresh đặt trong cookie **HttpOnly + SameSite=Strict** (+ `Secure` khi `APP_ENV=production`) → chống XSS/CSRF.
- **RBAC:** `require_role('admin')` (`api/deps.py`) chặn API nhạy cảm (403 nếu thiếu quyền).
- **Chống brute force:** sai > 5 lần (theo IP + email) → khoá 15 phút (`core/rate_limit.py`).
- **CORS chặt:** chỉ cho phép origin trong `CORS_ORIGINS`, bật `credentials`.
- **Chống SQL/NoSQL Injection:** SQLAlchemy ORM tham số hoá toàn bộ truy vấn + Pydantic validate kiểu/định dạng đầu vào.
- **Quên mật khẩu:** OTP 6 số ngẫu nhiên (`secrets`), chỉ lưu **hash**, hết hạn **5 phút**, giới hạn 5 lần nhập sai, thông báo lỗi chung chống dò email.

## Đã kiểm thử

**Backend (curl, DB SQLite):** register (422 yếu / 201 + cookie), login (last_login cập nhật), profile (401/200), refresh (cookie), brute force (429 sau 5 lần), forgot→reset (đổi mật khẩu, login mới 200/cũ 401, reuse OTP 400), RBAC (user 403 / admin 200 + danh sách). ✅

**Frontend (trình duyệt thật):** đăng ký → màn hình chính + badge role; đăng nhập sai → toast lỗi, đúng → vào trong; **auto-login** sau reload (cookie HttpOnly, JS không đọc được); **logout** → về form + refresh 401; **quên mật khẩu** 2 bước (OTP → đổi mật khẩu → login mật khẩu mới). Không lỗi console. ✅
