// Śpiewnik — lekki serwer bez zależności (czysty Node.js >= 18).
// Serwuje statyczny frontend z ../public oraz udostępnia proxy do:
//   - wyszukiwania tekstów piosenek (darmowe API lyrics.ovh, bez klucza),
//   - importu strony z chwytami/tabami po URL (pobiera i oczyszcza HTML).
//
// Uruchomienie:  node server.js   (domyślnie http://localhost:8080)

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const PORT = process.env.PORT || 8080;

// Katalog na dane synchronizowane między urządzeniami (montowany wolumen w Dockerze).
const DATA_DIR = process.env.SONGBOOK_DATA_DIR || path.join(__dirname, '..', 'data');
const LIBRARY_FILE = path.join(DATA_DIR, 'library.json');
// Opcjonalny token dostępu. Gdy ustawiony, biblioteka wymaga nagłówka
// `Authorization: Bearer <token>`. Gdy pusty — dostęp otwarty (tylko do użytku
// prywatnego / za VPN-em). Zalecane: ustaw SONGBOOK_TOKEN w .env.
const TOKEN = (process.env.SONGBOOK_TOKEN || '').trim();
try { fs.mkdirSync(DATA_DIR, { recursive: true }); } catch { /* ignore */ }

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.png': 'image/png',
  '.woff2': 'font/woff2',
};

function sendJson(res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  });
  res.end(body);
}

// --- Pobieranie tekstu piosenki (lyrics.ovh — darmowe, bez klucza) ---
async function fetchLyrics(artist, title) {
  const url = `https://api.lyrics.ovh/v1/${encodeURIComponent(artist)}/${encodeURIComponent(title)}`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 12000);
  try {
    const r = await fetch(url, { signal: ctrl.signal, headers: { 'Accept': 'application/json' } });
    if (!r.ok) return { ok: false, error: `Źródło tekstów zwróciło status ${r.status}` };
    const data = await r.json();
    if (!data || !data.lyrics) return { ok: false, error: 'Nie znaleziono tekstu dla tego tytułu/wykonawcy.' };
    // lyrics.ovh potrafi zwracać \r\n oraz nadmiarowe puste linie
    const lyrics = String(data.lyrics).replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
    return { ok: true, lyrics };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? 'Przekroczono czas oczekiwania na źródło.' : String(e.message || e) };
  } finally {
    clearTimeout(t);
  }
}

// --- Import dowolnej strony z chwytami/tabami po URL ---
// Zwracamy oczyszczony tekst; preferujemy zawartość znaczników <pre> (typowe dla
// serwisów z chwytami/tabaturą), a jeśli ich nie ma — cały tekst strony.
function htmlToText(html) {
  // wytnij skrypty/style
  let s = html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ');

  // preferuj bloki <pre> (zwykle trzymają chwyty nad tekstem)
  const pres = [...s.matchAll(/<pre[^>]*>([\s\S]*?)<\/pre>/gi)].map((m) => m[1]);
  let core = pres.length ? pres.join('\n\n') : s;

  core = core
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|tr|li|h[1-6])>/gi, '\n')
    .replace(/<[^>]+>/g, '') // usuń pozostałe tagi
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&#x27;/gi, "'")
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  return core;
}

async function fetchPage(targetUrl) {
  let u;
  try {
    u = new URL(targetUrl);
  } catch {
    return { ok: false, error: 'Niepoprawny adres URL.' };
  }
  if (!/^https?:$/.test(u.protocol)) return { ok: false, error: 'Dozwolone są tylko adresy http/https.' };

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15000);
  try {
    const r = await fetch(u.href, {
      signal: ctrl.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; SpiewnikBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
      },
    });
    if (!r.ok) return { ok: false, error: `Strona zwróciła status ${r.status}` };
    const html = await r.text();
    const text = htmlToText(html);
    if (!text) return { ok: false, error: 'Nie udało się wyodrębnić tekstu ze strony.' };
    return { ok: true, text, source: u.href };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? 'Przekroczono czas oczekiwania na stronę.' : String(e.message || e) };
  } finally {
    clearTimeout(t);
  }
}

function serveStatic(req, res) {
  let urlPath = decodeURIComponent(req.url.split('?')[0]);
  if (urlPath === '/') urlPath = '/index.html';
  // zabezpieczenie przed path traversal
  const safe = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, '');
  const filePath = path.join(PUBLIC_DIR, safe);
  if (!filePath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403); res.end('Forbidden'); return;
  }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      // SPA fallback -> index.html
      fs.readFile(path.join(PUBLIC_DIR, 'index.html'), (e2, idx) => {
        if (e2) { res.writeHead(404); res.end('Not found'); return; }
        res.writeHead(200, { 'Content-Type': MIME['.html'] });
        res.end(idx);
      });
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

// --- Biblioteka synchronizowana (server-side storage) ---
function authorized(req) {
  if (!TOKEN) return true; // brak tokenu = dostęp otwarty
  const h = req.headers['authorization'] || '';
  const m = h.match(/^Bearer\s+(.+)$/i);
  return !!m && m[1] === TOKEN;
}

function readBody(req, limit = 8 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    let data = ''; let size = 0;
    req.on('data', (c) => {
      size += c.length;
      if (size > limit) { reject(new Error('Za duży ładunek.')); req.destroy(); return; }
      data += c;
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function loadLibrary() {
  try { return JSON.parse(fs.readFileSync(LIBRARY_FILE, 'utf8')); }
  catch { return null; }
}
function saveLibrary(obj) {
  const tmp = LIBRARY_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(obj));
  fs.renameSync(tmp, LIBRARY_FILE); // zapis atomowy
}

const server = http.createServer(async (req, res) => {
  const { pathname, searchParams } = new URL(req.url, `http://${req.headers.host}`);

  if (pathname === '/api/health') {
    return sendJson(res, 200, { ok: true, service: 'spiewnik', time: new Date().toISOString() });
  }

  // Informacja dla frontendu: czy dostępna jest synchronizacja i czy wymaga tokenu.
  if (pathname === '/api/config') {
    return sendJson(res, 200, { ok: true, service: 'spiewnik', sync: true, authRequired: !!TOKEN });
  }

  // Biblioteka piosenek/list synchronizowana między urządzeniami.
  if (pathname === '/api/library') {
    if (!authorized(req)) return sendJson(res, 401, { ok: false, error: 'Wymagany prawidłowy token.' });

    if (req.method === 'GET') {
      const lib = loadLibrary();
      return sendJson(res, 200, { ok: true, library: lib, empty: lib === null });
    }
    if (req.method === 'PUT' || req.method === 'POST') {
      try {
        const raw = await readBody(req);
        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.songs) || !Array.isArray(parsed.lists)) {
          return sendJson(res, 400, { ok: false, error: 'Nieprawidłowy format biblioteki.' });
        }
        parsed.savedAt = Date.now();
        saveLibrary(parsed);
        return sendJson(res, 200, { ok: true, savedAt: parsed.savedAt });
      } catch (e) {
        return sendJson(res, 400, { ok: false, error: String(e.message || e) });
      }
    }
    return sendJson(res, 405, { ok: false, error: 'Metoda nieobsługiwana.' });
  }

  if (pathname === '/api/lyrics') {
    const artist = (searchParams.get('artist') || '').trim();
    const title = (searchParams.get('title') || '').trim();
    if (!artist || !title) return sendJson(res, 400, { ok: false, error: 'Podaj wykonawcę (artist) i tytuł (title).' });
    const result = await fetchLyrics(artist, title);
    return sendJson(res, result.ok ? 200 : 404, result);
  }

  if (pathname === '/api/import') {
    const target = (searchParams.get('url') || '').trim();
    if (!target) return sendJson(res, 400, { ok: false, error: 'Podaj parametr url.' });
    const result = await fetchPage(target);
    return sendJson(res, result.ok ? 200 : 502, result);
  }

  if (pathname.startsWith('/api/')) {
    return sendJson(res, 404, { ok: false, error: 'Nieznany endpoint API.' });
  }

  return serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`🎵 Śpiewnik działa na http://localhost:${PORT}`);
  console.log(`   Dane: ${LIBRARY_FILE}`);
  console.log(`   Synchronizacja: WŁ.  |  Token dostępu: ${TOKEN ? 'wymagany' : 'BRAK (dostęp otwarty)'}`);
});
