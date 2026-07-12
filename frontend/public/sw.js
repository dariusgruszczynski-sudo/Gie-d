/* GielDarek service worker -- makes the dashboard an installable app ("exe").
 *
 * Caching is deliberately conservative for a LIVE trading dashboard:
 *  - /api/* is NEVER cached (prices, positions, decisions must be fresh).
 *  - navigations are network-first (so a redeploy is picked up immediately
 *    when online) with the cached shell as an offline fallback.
 *  - hashed build assets (index-XXXX.js/css) are cache-first (safe: a new
 *    build produces new filenames, so the cache never serves a stale bundle).
 */
const CACHE = "gield-v1";
const SHELL = ["/", "/index.html"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Live data + SSE stream: always go to the network, never cache.
  if (url.pathname.startsWith("/api")) return;

  // Page loads: network-first, fall back to the cached shell when offline.
  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(() => caches.match("/index.html")));
    return;
  }

  // Static assets (hashed): cache-first, backfill the cache on first fetch.
  event.respondWith(
    caches.match(req).then(
      (hit) =>
        hit ||
        fetch(req).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
    )
  );
});
