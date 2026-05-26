'use strict';

/*
 * ===== TẦNG DOMAIN: Entity User =====
 * Chuẩn hoá dữ liệu user từ API (snake_case) sang hình dạng dùng trong app.
 */
export function createUser(raw) {
  if (!raw) return null;
  return {
    id: raw.id,
    username: raw.username,
    email: raw.email,
    role: raw.role || 'user',
    createdAt: raw.created_at || null,
    lastLogin: raw.last_login || null,
  };
}
