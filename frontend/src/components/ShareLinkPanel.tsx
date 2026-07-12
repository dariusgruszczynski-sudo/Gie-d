import { useEffect, useState } from "react";
import { api } from "../api/client";

function LinkIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M9 15l6-6M10.5 6.5l1-1a4 4 0 0 1 6 6l-1 1M13.5 17.5l-1 1a4 4 0 0 1-6-6l1-1" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

/** Lets the owner copy a read-only share link. The token comes from the
 *  auth-gated /api/control endpoint (a share viewer can never reach it); the URL
 *  is built from the browser's own origin so it's correct behind the proxy. */
export function ShareLinkPanel() {
  const [state, setState] = useState<{ enabled: boolean; token: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.shareLink().then(setState).catch(() => setState({ enabled: false, token: "" }));
  }, []);

  const url = state?.token ? `${window.location.origin}/?share=${encodeURIComponent(state.token)}` : "";

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      /* clipboard blocked -- the field is selectable as a fallback */
    }
  }

  return (
    <div className="panel">
      <div className="notif-head">
        <span className="notif-icon">
          <LinkIcon />
        </span>
        <div>
          <h2 style={{ margin: 0 }}>Link tylko do odczytu</h2>
          <p className="subtitle" style={{ margin: "2px 0 0" }}>
            Udostępnij komuś podgląd na żywo — widzi portfel, pozycje i decyzje, ale nie może nic kliknąć ani handlować.
          </p>
        </div>
      </div>

      {state === null ? (
        <p className="subtitle notif-note">Ładowanie…</p>
      ) : state.enabled ? (
        <>
          <div className="share-link-row">
            <input className="share-link-input" readOnly value={url} onFocus={(e) => e.currentTarget.select()} />
            <button className="btn-primary" onClick={copy}>
              {copied ? "Skopiowano ✓" : "Kopiuj"}
            </button>
          </div>
          <p className="subtitle notif-fineprint">
            Każdy z tym linkiem wchodzi bez logowania, ale tylko podgląd (serwer blokuje wszystkie akcje). Żeby unieważnić
            link, zmień <code>SHARE_TOKEN</code> w <code>.env</code> i zrestartuj apkę.
          </p>
        </>
      ) : (
        <p className="subtitle notif-note">
          Udostępnianie wyłączone. Włącz je, ustawiając na serwerze losowy sekret:
          <code className="notif-code">
            python -c "import secrets; print('SHARE_TOKEN=' + secrets.token_urlsafe(24))" &gt;&gt; .env
          </code>
          potem <code>docker compose up -d --force-recreate app</code>.
        </p>
      )}
    </div>
  );
}
