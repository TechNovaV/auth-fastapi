'use strict';

/*
 * ===== TẦNG PRESENTATION: View =====
 * Chỉ lo DOM: bắt sự kiện, validate client, gọi store/use case, và "điều hướng"
 * (hiện màn hình tương ứng) theo state. KHÔNG gọi API trực tiếp.
 */

import * as store from './authStore.js';
import * as useCases from '../domain/authUseCases.js';
import {
  validateLogin,
  validateRegister,
  validateForgotRequest,
  validateReset,
} from '../domain/validators.js';

let el = {};

export function init() {
  el = {
    tabButtons: document.querySelectorAll('.tab-btn'),
    tabs: document.querySelector('.tabs'),
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    appLoader: document.getElementById('app-loader'),
    welcomeBox: document.getElementById('welcome-box'),
    welcomeAvatar: document.getElementById('welcome-avatar'),
    welcomeName: document.getElementById('welcome-name'),
    welcomeRole: document.getElementById('welcome-role'),
    welcomeEmail: document.getElementById('welcome-email'),
    logoutBtn: document.getElementById('logout-btn'),
    toastContainer: document.getElementById('toast-container'),
    forgotLink: document.getElementById('forgot-link'),
    backToLogin: document.getElementById('back-to-login'),
    forgotScreen: document.getElementById('forgot-screen'),
    forgotRequestForm: document.getElementById('forgot-request-form'),
    forgotResetForm: document.getElementById('forgot-reset-form'),
    forgotSentTo: document.getElementById('forgot-sent-to'),
  };

  bindEvents();
  store.subscribe(render); // state đổi -> render tự chạy
}

// "Điều hướng" theo state.
function render(state) {
  // Khi đang auto-login (loading) thì giữ splash loader, chưa render gì.
  if (state.status === 'loading') return;

  // State đã rõ -> ẩn splash loader rồi hiện màn hình tương ứng.
  if (el.appLoader) el.appLoader.classList.add('hidden-loader');

  if (state.status === 'authenticated') showWelcome(state.user);
  else showForms();
}

function bindEvents() {
  for (let i = 0; i < el.tabButtons.length; i++) {
    const btn = el.tabButtons[i];
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  }

  el.loginForm.addEventListener('submit', onLoginSubmit);
  el.registerForm.addEventListener('submit', onRegisterSubmit);
  el.logoutBtn.addEventListener('click', onLogout);

  el.forgotLink.addEventListener('click', (e) => { e.preventDefault(); showForgot(); });
  el.backToLogin.addEventListener('click', (e) => { e.preventDefault(); showForms(); });
  el.forgotRequestForm.addEventListener('submit', onForgotRequestSubmit);
  el.forgotResetForm.addEventListener('submit', onResetSubmit);
}

async function onLoginSubmit(e) {
  e.preventDefault();
  const payload = {
    email: el.loginForm.email.value.trim(),
    password: el.loginForm.password.value,
  };
  const errors = validateLogin(payload);
  renderErrors(el.loginForm, errors);
  if (hasErrors(errors)) return;

  const btn = el.loginForm.querySelector('button[type="submit"]');
  btn.disabled = true;
  const result = await store.login(payload);
  btn.disabled = false;

  if (result.ok) { showToast('Đăng nhập thành công', 'success'); el.loginForm.reset(); }
  else showToast(result.error, 'error');
}

async function onRegisterSubmit(e) {
  e.preventDefault();
  const payload = {
    username: el.registerForm.username.value.trim(),
    email: el.registerForm.email.value.trim(),
    password: el.registerForm.password.value,
    confirm: el.registerForm.confirm.value,
  };
  const errors = validateRegister(payload);
  renderErrors(el.registerForm, errors);
  if (hasErrors(errors)) return;

  const btn = el.registerForm.querySelector('button[type="submit"]');
  btn.disabled = true;
  const result = await store.register({
    username: payload.username,
    email: payload.email,
    password: payload.password,
  });
  btn.disabled = false;

  if (result.ok) { showToast('Đăng ký thành công', 'success'); el.registerForm.reset(); }
  else showToast(result.error, 'error');
}

async function onLogout() {
  await store.logout(); // xoá token client + gọi API; state -> unauthenticated -> redirect
  showToast('Đã đăng xuất', 'success');
}

// Bước 1 quên mật khẩu: gửi email nhận OTP.
async function onForgotRequestSubmit(e) {
  e.preventDefault();
  const email = el.forgotRequestForm.email.value.trim();
  const errors = validateForgotRequest({ email });
  renderErrors(el.forgotRequestForm, errors);
  if (hasErrors(errors)) return;

  const btn = el.forgotRequestForm.querySelector('button[type="submit"]');
  btn.disabled = true;
  try {
    const data = await useCases.requestPasswordReset(email);
    showToast(data.message, 'success');
    el.forgotSentTo.textContent = email;
    el.forgotRequestForm.classList.add('hidden');
    el.forgotResetForm.classList.remove('hidden');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// Bước 2 quên mật khẩu: xác minh OTP + đặt mật khẩu mới.
async function onResetSubmit(e) {
  e.preventDefault();
  const payload = {
    email: el.forgotSentTo.textContent,
    otp: el.forgotResetForm.otp.value.trim(),
    password: el.forgotResetForm.password.value,
    confirm: el.forgotResetForm.confirm.value,
  };
  const errors = validateReset(payload);
  renderErrors(el.forgotResetForm, errors);
  if (hasErrors(errors)) return;

  const btn = el.forgotResetForm.querySelector('button[type="submit"]');
  btn.disabled = true;
  try {
    const data = await useCases.resetPasswordWithOtp({
      email: payload.email,
      otp: payload.otp,
      newPassword: payload.password,
    });
    showToast(data.message, 'success');
    el.forgotResetForm.reset();
    showForms();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ---- Vẽ giao diện ----
function switchTab(tabName) {
  for (let i = 0; i < el.tabButtons.length; i++) {
    const btn = el.tabButtons[i];
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  }
  el.loginForm.classList.toggle('active', tabName === 'login');
  el.registerForm.classList.toggle('active', tabName === 'register');
}

function showWelcome(user) {
  el.loginForm.classList.remove('active');
  el.registerForm.classList.remove('active');
  el.forgotScreen.classList.remove('active');
  el.tabs.style.display = 'none';
  el.welcomeBox.classList.add('active');
  el.welcomeName.textContent = user.username;
  el.welcomeEmail.textContent = user.email;
  el.welcomeRole.textContent = user.role;
  el.welcomeRole.classList.toggle('admin', user.role === 'admin');
  // Avatar = chữ cái đầu của username.
  if (el.welcomeAvatar) {
    el.welcomeAvatar.textContent = (user.username || '?').charAt(0).toUpperCase();
  }
}

function showForms() {
  el.welcomeBox.classList.remove('active');
  el.forgotScreen.classList.remove('active');
  el.tabs.style.display = 'flex';
  switchTab('login');
}

function showForgot() {
  el.welcomeBox.classList.remove('active');
  el.loginForm.classList.remove('active');
  el.registerForm.classList.remove('active');
  el.tabs.style.display = 'none';
  el.forgotScreen.classList.add('active');
  el.forgotResetForm.classList.add('hidden');
  el.forgotRequestForm.classList.remove('hidden');
  el.forgotRequestForm.reset();
  el.forgotResetForm.reset();
}

// Gắn lỗi vào từng input.
function renderErrors(formEl, errors) {
  const msgEls = formEl.querySelectorAll('.error-msg');
  for (let i = 0; i < msgEls.length; i++) msgEls[i].textContent = '';
  const inputEls = formEl.querySelectorAll('input');
  for (let i = 0; i < inputEls.length; i++) inputEls[i].classList.remove('invalid');

  for (const inputId in errors) {
    const msgEl = formEl.querySelector(`.error-msg[data-for="${inputId}"]`);
    const inputEl = document.getElementById(inputId);
    if (msgEl) msgEl.textContent = errors[inputId];
    if (inputEl) inputEl.classList.add('invalid');
  }
}

function hasErrors(errors) {
  for (const key in errors) return true;
  return false;
}

function showToast(message, type) {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = document.createElement('div');
  icon.className = 'toast-icon';
  icon.textContent = type === 'success' ? '✓' : '!';

  const msg = document.createElement('div');
  msg.className = 'toast-msg';
  msg.textContent = message;

  const bar = document.createElement('div'); // thanh tiến trình tự rút
  bar.className = 'toast-bar';

  toast.append(icon, msg, bar);
  el.toastContainer.appendChild(toast);

  // Tự ẩn sau 3.5s với hiệu ứng trượt ra.
  setTimeout(() => {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 350);
  }, 3500);
}
