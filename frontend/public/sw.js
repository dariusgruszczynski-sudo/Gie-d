/* GielDarek service worker -- makes the dashboard an installable app ("exe").
 *
 * Caching is deliberately conservative for a LIVE trading dashboard:
 *  - /api/* is NEVER cached (prices, positions, decisions must be fresh).
 *  - navigations are network-first (so a redeploy is picked up immediately
 *    when online) with the cached shell as an offline fallback.
 *  - hashed build assets (index-XXXX.js/css) are cache-first (safe: a new
 *    build produces new filenames, so the cache never serves a stale bundle).
 */
// Bump on asset changes (new icons/theme) so the activate handler purges the
// old cache and clients re-fetch the fixed-name assets (icons, favicon).
const CACHE = "gield-v21";
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

/* --- Web Push: powiadomienia o kupnie/sprzedaży (telefon / Apple Watch) --- */
self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch (_e) {
    payload = { title: "GielDarek", body: event.data ? event.data.text() : "" };
  }
  const title = payload.title || "GielDarek";
  const d = payload.data || {};
  const options = {
    body: payload.body || "",
    tag: payload.tag || "gieldarek",
    renotify: true,
    icon: "/icon-192.png",
    badge: "/favicon-64.png",
    // Kolorystyka apki (sky accent) na Androidzie/desktopie.
    data: { url: payload.url || "/", ...d },
    // Wibracja per typ (backend wysyła: zysk=triumf, strata=jeden długi,
    // kupno=podwójny tap). Fallback, gdy brak w payloadzie.
    vibrate: Array.isArray(d.vibrate) ? d.vibrate : [80, 40, 80],
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client) {
          client.navigate(target).catch(() => {});
          return client.focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(target);
    })
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Live data + SSE stream: always go to the network, never cache.
  if (url.pathname.startsWith("/api")) return;

  // Page loads: network-first, and REFRESH the cached shell on every success so
  // the offline fallback NEVER points to an old JS hash the server has already
  // replaced (that stale index -> dead asset -> white screen was the bug). Only
  // fall back to cache when the network genuinely fails (offline).
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("/index.html", copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match("/index.html").then((hit) => hit || caches.match("/")))
    );
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
