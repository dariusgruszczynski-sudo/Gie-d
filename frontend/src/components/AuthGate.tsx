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
    (async () => {
      try {
        const res = await fetch(withShare("/api/status"));
        setPhase(res.ok ? "authenticated" : "login");
      } catch {
        // Network error unrelated to auth -- don't trap the user behind a
        // login screen; let the rest of the app surface the real problem.
        setPhase("authenticated");
      }
    })();
  }, []);

  if (phase === "checking") return null;
  if (phase === "login") return <LoginScreen onSuccess={() => setPhase("booting")} />;
  if (phase === "booting") return <BrandLoader onComplete={() => setPhase("authenticated")} />;
  return <>{children}</>;
}
