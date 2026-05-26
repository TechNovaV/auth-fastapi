'use strict';

/*
 * ===== Composition Root =====
 * Nối các tầng và khởi động app.
 * Phụ thuộc một chiều: Presentation -> Domain -> Data.
 */

import * as view from './presentation/authView.js';
import * as store from './presentation/authStore.js';
import { initParticles } from './presentation/particles.js';

initParticles();  // hiệu ứng hạt nền
view.init();
store.init();     // auto-login khi mở/tải lại trang
