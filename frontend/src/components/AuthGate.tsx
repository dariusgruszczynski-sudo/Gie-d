import { ReactNode, useEffect, useState } from "react";
import { isReadOnly, withShare } from "../api/client";
import { BrandLoader } from "./BrandLoader";
import { LoginScreen } from "./LoginScreen";

type Phase = "checking" | "login" | "booting" | "authenticated";

export function AuthGate({ children }: { children: ReactNode }) {
  // Read-only share view skips the login screen entirely -- the ?share token on
  // each request is its credential, and it can only ever watch.
  const [phase, setPhase] = useState<Phase>(isReadOnly ? "authenticated" : "checking");

  useEffect(() => {
    if (isReadOnly) return;
    let dead = false;
    // TWARDY timeout: bez niego zawieszony /api/status trzyma fazę na "checking"
    // w NIESKOŃCZONOŚĆ, a AuthGate zwraca null => biały ekran na zawsze. Po
    // timeoucie wpuszczamy do apki (401 i tak wyświetli logowanie w środku, a
    // realny problem sieci pokaże baner "ponawiam"), zamiast trzymać pusty ekran.
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    (async () => {
      try {
        const res = await fetch(withShare("/api/status"), { signal: ctrl.signal });
        if (!dead) setPhase(res.ok ? "authenticated" : "login");
      } catch {
        // Timeout albo błąd sieci (nie auth) -- nie zamykaj użytkownika w pustym
        // ekranie; wpuść dalej, reszta apki pokaże prawdziwy problem.
        if (!dead) setPhase("authenticated");
      } finally {
        clearTimeout(timer);
      }
    })();
    return () => { dead = true; clearTimeout(timer); ctrl.abort(); };
  }, []);

  // "checking" pokazuje widoczny loader, NIGDY pustego ekranu.
  if (phase === "checking") {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", color: "#7c8aa2", fontFamily: "system-ui, sans-serif", fontSize: 14 }}>
        Łączę z automatem…
      </div>
    );
  }
  if (phase === "login") return <LoginScreen onSuccess={() => setPhase("booting")} />;
  if (phase === "booting") return <BrandLoader onComplete={() => setPhase("authenticated")} />;
  return <>{children}</>;
}
