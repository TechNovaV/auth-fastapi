'use strict';

/*
 * ===== Composition Root =====
 * Nối các tầng và khởi động app.
 * Phụ thuộc một chiều: Presentation -> Domain -> Data.
 */

import * as view from './presentation/authView.js';
import * as store from './presentation/authStore.js';
import * as theme from './presentation/theme.js';
import { initParticles } from './presentation/particles.js';

theme.init();              // gắn nút toggle + lắng nghe prefers-color-scheme
initParticles();           // hiệu ứng hạt nền
view.init();
store.init();              // auto-login khi mở/tải lại trang
