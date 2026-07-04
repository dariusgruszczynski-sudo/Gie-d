import { useState } from "react";

export function LoginScreen({ onSuccess }: { onSuccess: () => void }) {
  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!user || !password) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user, password }),
      });
      if (res.ok) {
        onSuccess();
      } else {
        setError("Nieprawidłowy login lub hasło");
      }
    } catch {
      setError("Błąd połączenia z serwerem");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <svg width="52" height="52" viewBox="0 0 40 40" className="logo-mark" aria-hidden="true">
          <circle cx="20" cy="20" r="19" fill="url(#loginLogoGradient)" stroke="var(--gold)" strokeWidth="1" />
          <defs>
            <linearGradient id="loginLogoGradient" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#1a1608" />
              <stop offset="100%" stopColor="#0a0a0a" />
            </linearGradient>
          </defs>
          <path d="M12 24 L16 16 L20 20 L24 11 L28 15" stroke="var(--gold-bright)" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M24 11 L28 11 L28 15" stroke="var(--gold-bright)" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <h1 className="login-title">GIE-D</h1>
        <p className="login-subtitle">Zaloguj się, aby uzyskać dostęp do panelu</p>

        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="text"
            placeholder="Login"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            autoFocus
            autoComplete="username"
          />
          <input
            type="password"
            placeholder="Hasło"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          <button className="btn-primary login-submit" type="submit" disabled={busy}>
            {busy ? "Weryfikacja…" : "ZALOGUJ"}
          </button>
          {error && <p className="error-text">{error}</p>}
        </form>
      </div>
    </div>
  );
}
