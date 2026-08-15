// sync.js — synchronizacja biblioteki między urządzeniami przez serwer.
// Aktywna tylko, gdy działa backend (wersja z serwerem). W wersji czysto
// lokalnej / hostowanej jako Artefakt po prostu się nie włącza i wszystko
// działa na localStorage.
import { store } from './store.js';

const TOKEN_KEY = 'spiewnik.token';
let cfg = null;              // { sync, authRequired } z /api/config
let applyingRemote = false;  // blokada, by nie odsyłać właśnie pobranych danych
let pushTimer = null;
let lastPushedJSON = null;
let statusCb = () => {};

function getToken() { try { return localStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; } }
function authHeaders() { const t = getToken(); return t ? { Authorization: 'Bearer ' + t } : {}; }
function emitStatus(s, detail) { statusCb(s, detail); }

export const sync = {
  onStatus(cb) { statusCb = cb || (() => {}); },
  available() { return !!(cfg && cfg.sync); },
  authRequired() { return !!(cfg && cfg.authRequired); },
  hasToken() { return !!getToken(); },
  token() { return getToken(); },
  setToken(t) { try { localStorage.setItem(TOKEN_KEY, (t || '').trim()); } catch { /* ignore */ } },

  // Sprawdza, czy serwer oferuje synchronizację.
  async detect() {
    try {
      const r = await fetch('/api/config', { cache: 'no-store' });
      if (!r.ok) { cfg = null; return false; }
      const d = await r.json();
      cfg = (d && d.service === 'spiewnik' && d.sync) ? d : null;
      return this.available();
    } catch { cfg = null; return false; }
  },

  // Pobiera bibliotekę z serwera.
  async pull() {
    if (!this.available()) return { ok: false };
    try {
      const r = await fetch('/api/library', { cache: 'no-store', headers: authHeaders() });
      if (r.status === 401) { emitStatus('auth'); return { ok: false, auth: true }; }
      if (!r.ok) { emitStatus('error'); return { ok: false }; }
      const d = await r.json();
      return { ok: true, library: d.library, empty: d.empty };
    } catch { emitStatus('error'); return { ok: false }; }
  },

  // Wysyła bieżącą bibliotekę na serwer (natychmiast).
  async push() {
    if (!this.available()) return;
    const payload = JSON.stringify(store.get());
    if (payload === lastPushedJSON) { emitStatus('ok'); return; }
    emitStatus('saving');
    try {
      const r = await fetch('/api/library', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: payload,
      });
      if (r.status === 401) { emitStatus('auth'); return; }
      if (!r.ok) { emitStatus('error'); return; }
      lastPushedJSON = payload;
      emitStatus('ok');
    } catch { emitStatus('error'); }
  },

  // Zaplanuj wysyłkę po krótkiej ciszy (debounce). Wywoływane przy każdej zmianie.
  schedulePush() {
    if (applyingRemote || !this.available()) return;
    emitStatus('saving');
    clearTimeout(pushTimer);
    pushTimer = setTimeout(() => this.push(), 900);
  },

  // Zastosuj bibliotekę z serwera lokalnie, nie wywołując wysyłki z powrotem.
  applyRemote(library) {
    applyingRemote = true;
    try { store.loadFrom(library); } finally { applyingRemote = false; }
    lastPushedJSON = JSON.stringify(store.get());
  },
};
