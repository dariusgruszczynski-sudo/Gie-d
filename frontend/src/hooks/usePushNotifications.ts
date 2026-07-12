import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

/** Stan powiadomień push dla TEGO urządzenia. Web Push wymaga:
 *  - HTTPS z zaufanym certem (PWA),
 *  - na iPhone/Apple Watch: apka DODANA do ekranu początkowego (iOS 16.4+),
 *    powiadomienia z iPhone'a lustrzą się wtedy na zegarku automatycznie.
 */
export type PushState =
  | "unsupported" // przeglądarka nie ma Push API / Service Workera
  | "server-off" // serwer nie ma kluczy VAPID
  | "denied" // użytkownik zablokował powiadomienia w przeglądarce
  | "off" // wszystko gotowe, ale nie zapisano subskrypcji
  | "on"; // subskrypcja aktywna na tym urządzeniu

function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const out = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

const isSupported = () =>
  typeof window !== "undefined" &&
  "serviceWorker" in navigator &&
  "PushManager" in window &&
  "Notification" in window;

export function usePushNotifications() {
  const [state, setState] = useState<PushState>("off");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [vapidKey, setVapidKey] = useState<string>("");

  const sync = useCallback(async () => {
    if (!isSupported()) {
      setState("unsupported");
      return;
    }
    let cfg: { enabled: boolean; vapid_public_key: string };
    try {
      cfg = await api.pushConfig();
    } catch {
      setState("server-off");
      return;
    }
    if (!cfg.enabled || !cfg.vapid_public_key) {
      setState("server-off");
      return;
    }
    setVapidKey(cfg.vapid_public_key);
    if (Notification.permission === "denied") {
      setState("denied");
      return;
    }
    const reg = await navigator.serviceWorker.ready;
    const existing = await reg.pushManager.getSubscription();
    setState(existing ? "on" : "off");
  }, []);

  useEffect(() => {
    sync();
  }, [sync]);

  const enable = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    try {
      const perm = await Notification.requestPermission();
      if (perm !== "granted") {
        setState("denied");
        setMessage("Powiadomienia zablokowane w ustawieniach przeglądarki.");
        return;
      }
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      });
      await api.pushSubscribe(sub.toJSON() as PushSubscriptionJSON);
      setState("on");
      setMessage("Powiadomienia włączone na tym urządzeniu.");
    } catch (e) {
      setMessage(`Nie udało się włączyć: ${String(e)}`);
    } finally {
      setBusy(false);
    }
  }, [vapidKey]);

  const disable = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        const json = sub.toJSON();
        await api
          .pushUnsubscribe({
            endpoint: json.endpoint ?? "",
            keys: { p256dh: json.keys?.p256dh ?? "", auth: json.keys?.auth ?? "" },
          })
          .catch(() => {});
        await sub.unsubscribe();
      }
      setState("off");
      setMessage("Powiadomienia wyłączone na tym urządzeniu.");
    } catch (e) {
      setMessage(`Nie udało się wyłączyć: ${String(e)}`);
    } finally {
      setBusy(false);
    }
  }, []);

  const test = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await api.pushTest();
      setMessage(res.message);
    } catch (e) {
      setMessage(`Test nieudany: ${String(e)}`);
    } finally {
      setBusy(false);
    }
  }, []);

  return { state, busy, message, enable, disable, test };
}
