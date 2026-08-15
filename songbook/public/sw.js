// sw.js — service worker: apka działa OFFLINE (na scenie bez zasięgu).
// Strategia: shell (HTML/CSS/JS/ikony) z cache (stale-while-revalidate),
// zapytania /api/* zawsze z sieci (nie cache'ujemy danych/wyszukiwań).
const CACHE = 'spiewnik-shell-v1';
const ASSETS = [
  './', './index.html',
  './css/styles.css',
  './js/app.js', './js/chordpro.js', './js/chords.js', './js/store.js',
  './js/sync.js', './js/suggestions.js', './js/search-client.js',
  './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()).catch(() => {}));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/')) return; // dane zawsze z sieci
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const network = fetch(e.request).then((res) => {
        if (res && res.ok && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        }
        return res;
      }).catch(() => cached);
      return cached || network;
    })
  );
});
