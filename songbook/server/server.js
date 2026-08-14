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

const server = http.createServer(async (req, res) => {
  const { pathname, searchParams } = new URL(req.url, `http://${req.headers.host}`);

  if (pathname === '/api/health') {
    return sendJson(res, 200, { ok: true, service: 'spiewnik', time: new Date().toISOString() });
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
});
