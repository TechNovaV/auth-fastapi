'use strict';

/*
 * Sinh các hạt sáng lơ lửng ở nền bằng vòng lặp for cơ bản.
 * Mỗi hạt được gán vị trí/kích thước/thời lượng ngẫu nhiên qua CSS variables,
 * còn chuyển động do CSS keyframe `float-up` đảm nhiệm (nhẹ cho CPU).
 */
export function initParticles(count = 28) {
  const container = document.getElementById('particles');
  if (!container) return;

  // Tôn trọng người dùng tắt hiệu ứng chuyển động.
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  for (let i = 0; i < count; i++) {
    const p = document.createElement('span');
    p.className = 'particle';

    const size = 3 + Math.random() * 7;        // 3 - 10 px
    const duration = 12 + Math.random() * 14;  // 12 - 26 giây
    const delay = -Math.random() * 20;         // âm -> rải đều ngay từ đầu
    const drift = Math.random() * 80 - 40;     // -40 .. 40 px lệch ngang

    p.style.left = `${Math.random() * 100}vw`;
    p.style.setProperty('--size', `${size}px`);
    p.style.setProperty('--duration', `${duration}s`);
    p.style.setProperty('--delay', `${delay}s`);
    p.style.setProperty('--drift', `${drift}px`);

    container.appendChild(p);
  }
}
