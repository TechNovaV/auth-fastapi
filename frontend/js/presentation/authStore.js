'use strict';

/*
 * ===== TẦNG PRESENTATION: State Management =====
 * Store observable (pub/sub): giữ state xác thực ở một nơi; View subscribe để
 * tự vẽ lại khi state đổi. Action gọi use case rồi cập nhật state.
 *
 * status: 'loading' | 'authenticated' | 'unauthenticated'
 */

import * as useCases from '../domain/authUseCases.js';

const state = { status: 'loading', user: null, error: null };
const listeners = [];

export function getState() {
  return { status: state.status, user: state.user, error: state.error };
}

export function subscribe(listener) {
  listeners.push(listener);
  listener(getState());
}

function setState(patch) {
  if (patch.status !== undefined) state.status = patch.status;
  if (patch.user !== undefined) state.user = patch.user;
  if (patch.error !== undefined) state.error = patch.error;

  const snapshot = getState();
  for (let i = 0; i < listeners.length; i++) {
    listeners[i](snapshot);
  }
}

// Auto-login khi khởi động app.
export async function init() {
  setState({ status: 'loading', error: null });
  try {
    const user = await useCases.tryAutoLogin();
    if (user) setState({ status: 'authenticated', user, error: null });
    else setState({ status: 'unauthenticated', user: null, error: null });
  } catch (_) {
    setState({ status: 'unauthenticated', user: null, error: null });
  }
}

export async function login(credentials) {
  try {
    const user = await useCases.loginUser(credentials);
    setState({ status: 'authenticated', user, error: null });
    return { ok: true };
  } catch (err) {
    setState({ error: err.message });
    return { ok: false, error: err.message };
  }
}

export async function register(payload) {
  try {
    const user = await useCases.registerUser(payload);
    setState({ status: 'authenticated', user, error: null });
    return { ok: true };
  } catch (err) {
    setState({ error: err.message });
    return { ok: false, error: err.message };
  }
}

export async function logout() {
  await useCases.logoutUser();
  setState({ status: 'unauthenticated', user: null, error: null });
}
