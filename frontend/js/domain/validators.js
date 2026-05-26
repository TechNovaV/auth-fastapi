'use strict';

/*
 * ===== TẦNG DOMAIN: Quy tắc validate (client) =====
 * Báo lỗi nhanh trước khi gửi request. Server vẫn validate lại (Pydantic).
 * Trả về object lỗi { idInput: 'thông báo' }; rỗng nghĩa là hợp lệ.
 */

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const USERNAME_REGEX = /^[A-Za-z0-9_.]{3,30}$/;
const MIN_PASSWORD_LENGTH = 8;

function isValidEmail(email) {
  return EMAIL_REGEX.test((email || '').trim());
}

function isValidUsername(username) {
  return USERNAME_REGEX.test((username || '').trim());
}

// Mật khẩu mạnh: duyệt từng ký tự bằng vòng for cơ bản.
function checkStrongPassword(password) {
  const p = password || '';
  if (p.length < MIN_PASSWORD_LENGTH) return `Mật khẩu tối thiểu ${MIN_PASSWORD_LENGTH} ký tự`;

  let hasLetter = false;
  let hasDigit = false;
  let hasSpecial = false;
  for (let i = 0; i < p.length; i++) {
    const ch = p[i];
    if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) hasLetter = true;
    else if (ch >= '0' && ch <= '9') hasDigit = true;
    else hasSpecial = true;
  }

  if (!hasLetter) return 'Mật khẩu phải có ít nhất 1 chữ cái';
  if (!hasDigit) return 'Mật khẩu phải có ít nhất 1 chữ số';
  if (!hasSpecial) return 'Mật khẩu phải có ít nhất 1 ký tự đặc biệt';
  return null;
}

export function validateLogin({ email, password }) {
  const errors = {};
  if (!email) errors['login-email'] = 'Vui lòng nhập email';
  else if (!isValidEmail(email)) errors['login-email'] = 'Email không hợp lệ';
  if (!password) errors['login-password'] = 'Vui lòng nhập mật khẩu';
  return errors;
}

export function validateRegister({ username, email, password, confirm }) {
  const errors = {};

  if (!username || !username.trim()) errors['register-username'] = 'Vui lòng nhập tên đăng nhập';
  else if (!isValidUsername(username)) errors['register-username'] = 'Tên đăng nhập 3-30 ký tự: chữ, số, "_" hoặc "."';

  if (!email) errors['register-email'] = 'Vui lòng nhập email';
  else if (!isValidEmail(email)) errors['register-email'] = 'Email không hợp lệ';

  if (!password) {
    errors['register-password'] = 'Vui lòng nhập mật khẩu';
  } else {
    const pwdError = checkStrongPassword(password);
    if (pwdError) errors['register-password'] = pwdError;
  }

  if (!confirm) errors['register-confirm'] = 'Vui lòng xác nhận mật khẩu';
  else if (confirm !== password) errors['register-confirm'] = 'Mật khẩu xác nhận không khớp';

  return errors;
}

export function validateForgotRequest({ email }) {
  const errors = {};
  if (!email) errors['forgot-email'] = 'Vui lòng nhập email';
  else if (!isValidEmail(email)) errors['forgot-email'] = 'Email không hợp lệ';
  return errors;
}

export function validateReset({ otp, password, confirm }) {
  const errors = {};

  if (!otp) errors['reset-otp'] = 'Vui lòng nhập mã OTP';
  else if (!/^\d{6}$/.test(otp)) errors['reset-otp'] = 'Mã OTP gồm 6 chữ số';

  if (!password) {
    errors['reset-password'] = 'Vui lòng nhập mật khẩu mới';
  } else {
    const pwdError = checkStrongPassword(password);
    if (pwdError) errors['reset-password'] = pwdError;
  }

  if (!confirm) errors['reset-confirm'] = 'Vui lòng xác nhận mật khẩu';
  else if (confirm !== password) errors['reset-confirm'] = 'Mật khẩu xác nhận không khớp';

  return errors;
}
