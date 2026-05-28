'use strict';

/*
 * ===== TẦNG PRESENTATION: Theme Controller =====
 *
 * Tách bạch quản lý chế độ Light/Dark khỏi UI components (authView, store…).
 *
 * Cơ chế:
 *   1) Inline script trong <head> đã set data-theme từ trước khi CSS tải
 *      (chống FOUC) — đọc localStorage hoặc prefers-color-scheme.
 *   2) Module này thêm 2 việc lúc runtime:
 *       a) Gán click handler vào nút #theme-toggle để override thủ công.
 *       b) Lắng nghe matchMedia: KHI hệ thống đổi theme và user CHƯA override
 *          thì tự đổi theo. Có override thì giữ lựa chọn của user.
 *
 * Hiệu ứng fade 0.3-0.5s do CSS (transition trên màu nền/chữ/border) phụ trách.
 */

const STORAGE_KEY = 'peak-theme';     // 'light' | 'dark' | (không có = follow system)

export function getTheme() {
  return document.documentElement.getAttribute('data-theme') || 'light';
}

export function setTheme(theme, options) {
  const opts = options || {};
  document.documentElement.setAttribute('data-theme', theme);
  if (opts.persist !== false) {
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (_) {}
  }
}

export function toggleTheme() {
  setTheme(getTheme() === 'dark' ? 'light' : 'dark');
}

export function init() {
  // 1) Dùng EVENT DELEGATION trên document để bắt click vào #theme-toggle.
  //    Cách này không phụ thuộc DOM order / module load timing -> luôn ổn định.
  document.addEventListener('click', (e) => {
    const target = e.target;
    if (target && target.closest && target.closest('#theme-toggle')) {
      toggleTheme();
    }
  });

  // 2) Lắng nghe prefers-color-scheme. Nếu user chưa override thì follow.
  if (window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => {
      let stored = null;
      try { stored = localStorage.getItem(STORAGE_KEY); } catch (_) {}
      if (!stored) {
        // Đổi theo hệ thống, KHÔNG lưu vào localStorage để giữ "auto follow".
        setTheme(e.matches ? 'dark' : 'light', { persist: false });
      }
    };
    // Hỗ trợ cả API mới & cũ (Safari cũ).
    if (mq.addEventListener) mq.addEventListener('change', handler);
    else if (mq.addListener) mq.addListener(handler);
  }
}
