'use strict';

/*
 * ===== TẦNG DATA: Auth Repository =====
 * Nơi DUY NHẤT biết các endpoint API + cách thao tác token.
 * Khớp với FastAPI: trường token là `access_token`, profile ở `/api/profile`,
 * đổi mật khẩu dùng `new_password`.
 */

import { httpRequest, messageFromError } from './httpClient.js';
import * as tokenStorage from './tokenStorage.js';

export async function register(payload) {
  const { ok, data } = await httpRequest('/api/register', { method: 'POST', body: payload });
  if (!ok) throw new Error(messageFromError(data));
  tokenStorage.setAccessToken(data.access_token);
  return data.user;
}

export async function login(payload) {
  const { ok, data } = await httpRequest('/api/login', { method: 'POST', body: payload });
  if (!ok) throw new Error(messageFromError(data));
  tokenStorage.setAccessToken(data.access_token);
  return data.user;
}

// Xin access token mới bằng refresh token (cookie). Trả user hoặc null.
export async function refreshSession() {
  const { ok, data } = await httpRequest('/api/refresh', { method: 'POST' });
  if (!ok || !data.access_token) {
    tokenStorage.clearAccessToken();
    return null;
  }
  tokenStorage.setAccessToken(data.access_token);
  return data.user;
}

export async function logout() {
  try {
    await httpRequest('/api/logout', { method: 'POST' });
  } catch (_) {
    // bỏ qua lỗi mạng — vẫn xoá access token phía client
  }
  tokenStorage.clearAccessToken();
}

// Lấy hồ sơ user hiện tại (tự refresh nếu cần). Trả về object user.
export async function getProfile() {
  return authedRequest('/api/profile');
}

export async function forgotPassword(email) {
  const { ok, data } = await httpRequest('/api/forgot-password', { method: 'POST', body: { email } });
  if (!ok) throw new Error(messageFromError(data));
  return data;
}

export async function resetPassword({ email, otp, newPassword }) {
  const { ok, data } = await httpRequest('/api/reset-password', {
    method: 'POST',
    body: { email, otp, new_password: newPassword },
  });
  if (!ok) throw new Error(messageFromError(data));
  return data;
}

/*
 * Gọi API cần xác thực với 2 lớp tự phục hồi token:
 *  1) Chủ động: token thiếu/hết hạn (đọc exp ở client) -> refresh trước.
 *  2) Bị động: server trả 401 -> refresh rồi thử lại 1 lần.
 */
async function authedRequest(path, options = {}) {
  let token = tokenStorage.getAccessToken();

  if (!token || tokenStorage.isExpired(token)) {
    await refreshSession();
    token = tokenStorage.getAccessToken();
  }

  let result = await httpRequest(path, { ...options, token });

  if (result.status === 401) {
    const user = await refreshSession();
    if (user) {
      token = tokenStorage.getAccessToken();
      result = await httpRequest(path, { ...options, token });
    }
  }

  if (!result.ok) throw new Error(messageFromError(result.data));
  return result.data;
}
