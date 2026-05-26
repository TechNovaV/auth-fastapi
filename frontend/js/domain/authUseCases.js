'use strict';

/*
 * ===== TẦNG DOMAIN: Use Cases =====
 * Điều phối repository và trả về Entity. Presentation chỉ gọi xuống đây.
 */

import * as repo from '../data/authRepository.js';
import { createUser } from './user.js';

export async function registerUser({ username, email, password }) {
  const raw = await repo.register({ username, email, password });
  return createUser(raw);
}

export async function loginUser({ email, password }) {
  const raw = await repo.login({ email, password });
  return createUser(raw);
}

export async function logoutUser() {
  await repo.logout();
}

export async function loadCurrentUser() {
  const raw = await repo.getProfile();
  return createUser(raw);
}

/*
 * Auto-login khi mở lại trang:
 *  1) Dùng refresh token (cookie) xin access token mới.
 *  2) Gọi /api/profile lấy User Profile.
 * Trả về user, hoặc null nếu không có phiên hợp lệ.
 */
export async function tryAutoLogin() {
  const refreshed = await repo.refreshSession();
  if (!refreshed) return null;
  return loadCurrentUser();
}

export async function requestPasswordReset(email) {
  return repo.forgotPassword(email);
}

export async function resetPasswordWithOtp({ email, otp, newPassword }) {
  return repo.resetPassword({ email, otp, newPassword });
}
