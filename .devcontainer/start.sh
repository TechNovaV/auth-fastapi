#!/usr/bin/env bash
# Khởi chạy uvicorn trong Codespaces với RP_ID/RP_ORIGIN khớp URL preview.
set -e

if [ -n "$CODESPACE_NAME" ]; then
  DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
  HOST="${CODESPACE_NAME}-8000.${DOMAIN}"
  export RP_ID="$HOST"
  export RP_ORIGIN="https://$HOST"
  export CORS_ORIGINS="$RP_ORIGIN"
  echo "[start] Codespace mode -> RP_ORIGIN=$RP_ORIGIN"
fi

export DATABASE_URL="${DATABASE_URL:-sqlite:///./auth.db}"
export APP_ENV="${APP_ENV:-development}"
# Secret tự sinh cho mỗi codespace (an toàn cho demo).
export JWT_SECRET="${JWT_SECRET:-codespace-access-$(openssl rand -hex 16)}"
export JWT_REFRESH_SECRET="${JWT_REFRESH_SECRET:-codespace-refresh-$(openssl rand -hex 16)}"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
