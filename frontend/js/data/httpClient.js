'use strict';

/*
 * ===== TẦNG DATA: HTTP client =====
 * Bọc fetch: gắn header, đính access token (nếu có), luôn gửi kèm cookie
 * (credentials) để refresh token đi theo, parse JSON.
 * Trả về { ok, status, data }.
 */

const BASE_URL = ''; // cùng origin với server (FastAPI phục vụ luôn frontend)

export async function httpRequest(path, options = {}) {
  const method = options.method || 'GET';
  const body = options.body;
  const token = options.token;

  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });

  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

/*
 * FastAPI trả lỗi ở khoá "detail":
 *  - HTTPException => detail là chuỗi.
 *  - Lỗi validate (422) => detail là mảng [{msg, loc, ...}].
 * Hàm này gộp lại thành 1 thông báo thân thiện.
 */
export function messageFromError(data) {
  const detail = data && data.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = [];
    for (let i = 0; i < detail.length; i++) {
      messages.push(detail[i].msg || 'Dữ liệu không hợp lệ');
    }
    return messages.join('; ');
  }
  return 'Có lỗi xảy ra, vui lòng thử lại';
}
