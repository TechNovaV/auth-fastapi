'use strict';

/*
 * ===== TẦNG DATA: Lưu trữ token =====
 * Access Token giữ TRONG BỘ NHỚ (biến module) — mất khi tải lại trang, giảm
 * rủi ro XSS so với localStorage. Refresh Token nằm trong cookie HttpOnly do
 * server quản lý (JS không đọc được) — đó là "secure storage" của web.
 */

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export function clearAccessToken() {
  accessToken = null;
}

// Giải mã payload JWT (chỉ để đọc hạn, không xác minh chữ ký).
export function decodeJwt(token) {
  if (!token) return null;
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch (_) {
    return null;
  }
}

// Kiểm tra access token đã hết hạn chưa (để chủ động refresh).
export function isExpired(token, skewSeconds = 10) {
  const payload = decodeJwt(token);
  if (!payload || !payload.exp) return true;
  const nowSeconds = Math.floor(Date.now() / 1000);
  return payload.exp <= nowSeconds + skewSeconds;
}
