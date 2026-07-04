import { ReactNode, useEffect, useState } from "react";
import { JarvisBoot } from "./JarvisBoot";
import { LoginScreen } from "./LoginScreen";

type Phase = "checking" | "login" | "booting" | "authenticated";

export function AuthGate({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<Phase>("checking");

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/status");
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
  if (phase === "booting") return <JarvisBoot onComplete={() => setPhase("authenticated")} />;
  return <>{children}</>;
}
