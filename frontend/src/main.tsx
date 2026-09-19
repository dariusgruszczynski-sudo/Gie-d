import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AuthGate } from "./components/AuthGate";
import "./index.css";
import "./console.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthGate>
      <App />
    </AuthGate>
  </React.StrictMode>,
);

// Register the service worker so the dashboard is installable as an app.
// Requires HTTPS (trusted cert) -- see deploy/README-hardening.md.
//
// Self-healing updates: a redeploy ships a new sw.js (bumped CACHE) which
// skipWaiting()s and clients.claim()s, so it takes control immediately. The
// page listens for that takeover and reloads ONCE, so an installed PWA (esp.
// iOS, which never revalidates on its own) picks up the new bundle without the
// user having to delete/re-add the app. We also poke reg.update() on every
// foreground so a reopened PWA actually looks for the new worker.
if ("serviceWorker" in navigator) {
  let reloadedForUpdate = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    // Fires when a freshly-activated SW claims this page. Reload once to swap in
    // the new hashed assets; the guard prevents an update->reload->update loop.
    if (reloadedForUpdate) return;
    reloadedForUpdate = true;
    window.location.reload();
  });
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((reg) => {
        const check = () => reg.update().catch(() => {});
        check(); // check right away in case a redeploy already happened
        // Re-check whenever the app is brought back to the foreground.
        document.addEventListener("visibilitychange", () => {
          if (document.visibilityState === "visible") check();
        });
        // And on a slow cadence while it stays open (long-running dashboard).
        setInterval(check, 60 * 60 * 1000);
      })
      .catch(() => {
        /* SW is a progressive enhancement; ignore registration failures. */
      });
  });
}
