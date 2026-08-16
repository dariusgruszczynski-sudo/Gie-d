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
// Klucz do wyszukiwarki webowej (SerpAPI). Gdy pusty — używamy DuckDuckGo (bez
// klucza). Możesz podać własny SONGBOOK_SEARCH_KEY albo pozwolić użyć klucza
// GielDarka (SERPAPI_API_KEY), jeśli świadomie go tu przekażesz.
const SEARCH_KEY = (process.env.SONGBOOK_SEARCH_KEY || process.env.SERPAPI_API_KEY || '').trim();
// Adres opcjonalnego mikroserwisu wykrywania akordów z audio (nakładka audio).
const AUDIO_URL = (process.env.SONGBOOK_AUDIO_URL || '').trim();
try { fs.mkdirSync(DATA_DIR, { recursive: true }); } catch { /* ignore */ }

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
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

// --- Wyszukiwarka opracowań z chwytami (web search) ---
function hostnameOf(u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch { return ''; } }
function decodeEntities(s) {
  return String(s)
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&#x27;/g, "'")
    .replace(/&nbsp;/g, ' ');
}
function stripTags(s) { return decodeEntities(String(s).replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim(); }

// Buduje zapytanie nakierowane na opracowania z chwytami (polskie + międzynarodowe).
function buildSearchQuery({ q, artist, title }) {
  const base = (q && q.trim()) || [artist, title].filter(Boolean).join(' ').trim();
  if (!base) return '';
  // Jeśli użytkownik sam nie dopisał "chwyty/akordy/chords/tab", dokładamy.
  if (/chwyt|akord|chord|tab/i.test(base)) return base;
  return `${base} chwyty akordy`;
}

// SerpAPI (Google) — zwraca listę wyników.
async function searchSerp(query, max) {
  const url = `https://serpapi.com/search.json?engine=google&hl=pl&gl=pl&num=${max}&q=${encodeURIComponent(query)}&api_key=${encodeURIComponent(SEARCH_KEY)}`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 12000);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    if (!r.ok) return { ok: false, error: `Wyszukiwarka zwróciła status ${r.status}` };
    const data = await r.json();
    const items = (data.organic_results || []).map((o) => ({
      title: o.title || '', url: o.link || '', snippet: o.snippet || '', source: hostnameOf(o.link || ''),
    })).filter((x) => x.url);
    return { ok: true, items };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? 'Przekroczono czas wyszukiwania.' : String(e.message || e) };
  } finally { clearTimeout(t); }
}

// DuckDuckGo (bez klucza) — parsujemy HTML wyników.
async function searchDuck(query, max) {
  const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}&kl=pl-pl`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 12000);
  try {
    const r = await fetch(url, {
      signal: ctrl.signal,
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; SpiewnikBot/1.0)', 'Accept': 'text/html' },
    });
    if (!r.ok) return { ok: false, error: `Wyszukiwarka zwróciła status ${r.status}` };
    const html = await r.text();
    return { ok: true, items: parseDuck(html).slice(0, max) };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? 'Przekroczono czas wyszukiwania.' : String(e.message || e) };
  } finally { clearTimeout(t); }
}

// Pure — parsuje stronę wyników DuckDuckGo HTML na listę {title,url,snippet,source}.
function parseDuck(html) {
  const items = [];
  const re = /<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = re.exec(html))) {
    let href = decodeEntities(m[1]);
    // DDG owija link w redirect z parametrem uddg=
    const ud = href.match(/[?&]uddg=([^&]+)/);
    if (ud) { try { href = decodeURIComponent(ud[1]); } catch { /* keep */ } }
    if (href.startsWith('//')) href = 'https:' + href;
    const title = stripTags(m[2]);
    if (href && title) items.push({ title, url: href, snippet: '', source: hostnameOf(href) });
  }
  // dorzuć snippety (kolejność zwykle zgodna z wynikami)
  const snips = [...html.matchAll(/<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([\s\S]*?)<\/a>/gi)].map((x) => stripTags(x[1]));
  items.forEach((it, i) => { if (snips[i]) it.snippet = snips[i]; });
  return items;
}

async function webSearch(params) {
  const query = buildSearchQuery(params);
  if (!query) return { ok: false, error: 'Podaj tytuł, zespół lub fragment tekstu.' };
  const max = Math.min(Math.max(parseInt(params.max) || 12, 1), 20);
  const res = SEARCH_KEY ? await searchSerp(query, max) : await searchDuck(query, max);
  if (!res.ok) return res;
  return { ok: true, query, provider: SEARCH_KEY ? 'serpapi' : 'duckduckgo', items: res.items };
}

// --- Rozpoznanie linku (poczekalnia): tytuł/wykonawca z oEmbed lub <title> ---
async function resolveLink(target) {
  let u;
  try { u = new URL(target); } catch { return { ok: false, error: 'Niepoprawny adres URL.' }; }
  if (!/^https?:$/.test(u.protocol)) return { ok: false, error: 'Dozwolone tylko http/https.' };
  const host = u.hostname.replace(/^www\./, '');

  const fetchJson = async (endpoint) => {
    const ctrl = new AbortController(); const t = setTimeout(() => ctrl.abort(), 10000);
    try { const r = await fetch(endpoint, { signal: ctrl.signal, headers: { 'User-Agent': 'Mozilla/5.0 (compatible; SpiewnikBot/1.0)' } });
      if (!r.ok) return null; return await r.json(); } catch { return null; } finally { clearTimeout(t); }
  };

  // oEmbed dla platform, które go udostępniają
  let oembed = null;
  if (/youtube\.com|youtu\.be/.test(host)) oembed = `https://www.youtube.com/oembed?url=${encodeURIComponent(u.href)}&format=json`;
  else if (/tiktok\.com/.test(host)) oembed = `https://www.tiktok.com/oembed?url=${encodeURIComponent(u.href)}`;
  if (oembed) {
    const d = await fetchJson(oembed);
    if (d && (d.title || d.author_name)) {
      return { ok: true, title: d.title || '', author: d.author_name || '', source: host, url: u.href, thumb: d.thumbnail_url || '' };
    }
  }

  // fallback: og:title / <title> ze strony (IG, FB i inne)
  const ctrl = new AbortController(); const t = setTimeout(() => ctrl.abort(), 12000);
  try {
    const r = await fetch(u.href, { signal: ctrl.signal, headers: { 'User-Agent': 'Mozilla/5.0 (compatible; SpiewnikBot/1.0)', 'Accept': 'text/html' } });
    if (!r.ok) return { ok: true, title: '', author: '', source: host, url: u.href };
    const html = await r.text();
    const og = html.match(/<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)["']/i);
    const tt = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    const title = decodeEntities((og && og[1]) || (tt && tt[1]) || '').replace(/\s+/g, ' ').trim();
    return { ok: true, title, author: '', source: host, url: u.href };
  } catch (e) {
    return { ok: false, error: 'Nie udało się pobrać opisu linku.' };
  } finally { clearTimeout(t); }
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

// Wersja binarna (dla wgrywanego pliku audio) — zwraca Buffer, nie string.
function readBodyBuffer(req, limit = 80 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = []; let size = 0;
    req.on('data', (c) => {
      size += c.length;
      if (size > limit) { reject(new Error('Za duży ładunek.')); req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
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
    return sendJson(res, 200, { ok: true, service: 'spiewnik', time: new Date().toISOString(), version: process.env.GIT_SHA || 'dev', builtAt: process.env.BUILD_TIME || '' });
  }

  // Informacja dla frontendu: czy dostępna jest synchronizacja i czy wymaga tokenu.
  if (pathname === '/api/config') {
    return sendJson(res, 200, { ok: true, service: 'spiewnik', sync: true, authRequired: !!TOKEN, search: true, searchProvider: SEARCH_KEY ? 'serpapi' : 'duckduckgo', audio: !!AUDIO_URL });
  }

  // Wykrywanie akordów z WGRANEGO pliku audio — pewna droga bez YouTube.
  if (pathname === '/api/chords/upload') {
    if (!AUDIO_URL) return sendJson(res, 501, { ok: false, error: 'Moduł audio nie jest włączony (uruchom nakładkę docker-compose.audio.yml).' });
    if (req.method !== 'POST') return sendJson(res, 405, { ok: false, error: 'Użyj POST.' });
    let buf;
    try { buf = await readBodyBuffer(req); }
    catch { return sendJson(res, 413, { ok: false, error: 'Plik za duży (max 80 MB). Użyj mp3/m4a.' }); }
    if (!buf.length) return sendJson(res, 400, { ok: false, error: 'Pusty plik audio.' });
    const name = (searchParams.get('name') || 'audio').trim();
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 240000);
    try {
      const r = await fetch(`${AUDIO_URL}/detect?name=${encodeURIComponent(name)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream', 'Content-Length': String(buf.length) },
        body: buf,
        signal: ctrl.signal,
      });
      const data = await r.json().catch(() => ({ ok: false, error: 'Serwis audio zwrócił nieprawidłową odpowiedź.' }));
      return sendJson(res, r.ok ? 200 : 502, data);
    } catch (e) {
      return sendJson(res, 502, { ok: false, error: e.name === 'AbortError' ? 'Wykrywanie trwało zbyt długo.' : 'Serwis audio niedostępny.' });
    } finally { clearTimeout(t); }
  }

  // Wykrywanie akordów z audio (YouTube) — proxy do opcjonalnego mikroserwisu.
  if (pathname === '/api/chords') {
    if (!AUDIO_URL) return sendJson(res, 501, { ok: false, error: 'Moduł audio nie jest włączony (uruchom nakładkę docker-compose.audio.yml).' });
    const target = (searchParams.get('url') || '').trim();
    if (!target) return sendJson(res, 400, { ok: false, error: 'Podaj parametr url.' });
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 240000); // detekcja bywa długa
    try {
      const r = await fetch(`${AUDIO_URL}/detect?url=${encodeURIComponent(target)}`, { signal: ctrl.signal });
      const data = await r.json().catch(() => ({ ok: false, error: 'Serwis audio zwrócił nieprawidłową odpowiedź.' }));
      return sendJson(res, r.ok ? 200 : 502, data);
    } catch (e) {
      return sendJson(res, 502, { ok: false, error: e.name === 'AbortError' ? 'Wykrywanie trwało zbyt długo.' : 'Serwis audio niedostępny.' });
    } finally { clearTimeout(t); }
  }

  // Wyszukiwarka opracowań z chwytami — zwraca listę wyników do wyboru.
  if (pathname === '/api/search') {
    const params = {
      q: searchParams.get('q') || '',
      artist: searchParams.get('artist') || '',
      title: searchParams.get('title') || '',
      max: searchParams.get('max') || '',
    };
    const result = await webSearch(params);
    return sendJson(res, result.ok ? 200 : 502, result);
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

  if (pathname === '/api/resolve') {
    const target = (searchParams.get('url') || '').trim();
    if (!target) return sendJson(res, 400, { ok: false, error: 'Podaj parametr url.' });
    const result = await resolveLink(target);
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
