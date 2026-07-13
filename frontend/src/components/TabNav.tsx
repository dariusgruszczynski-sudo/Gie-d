import { isReadOnly } from "../api/client";
import { TabKey } from "../pages/types";

type IconName = "home" | "stocks" | "crypto" | "sliders" | "pulse";

interface TabDef {
  key: TabKey;
  label: string;
  short: string;
  icon: IconName;
  dot?: "alpaca" | "crypto";
}

const TABS: TabDef[] = [
  { key: "overview", label: "Dashboard główny", short: "Główny", icon: "home" },
  { key: "us", label: "Alpaca · Akcje US", short: "Akcje US", icon: "stocks", dot: "alpaca" },
  { key: "crypto", label: "Alpaca · Krypto", short: "Krypto", icon: "crypto", dot: "crypto" },
  { key: "control", label: "Centrum sterowania", short: "Sterowanie", icon: "sliders" },
  { key: "health", label: "Health check", short: "Health", icon: "pulse" },
];

function TabIcon({ name }: { name: IconName }) {
  const p = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", "aria-hidden": true } as const;
  switch (name) {
    case "home":
      return (
        <svg {...p}>
          <path d="M4 11 12 4l8 7M6 10v9h12v-9" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" strokeLinecap="round" />
        </svg>
      );
    case "stocks":
      return (
        <svg {...p}>
          <path d="M4 16l4-4 3 3 5-6 4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 20h16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "crypto":
      return (
        <svg {...p}>
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.7" />
          <path d="M10 8h3.2a2 2 0 0 1 0 4H10m0 0h3.6a2 2 0 0 1 0 4H10m0-8v10M11.5 6.5v1.5M11.5 16v1.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "sliders":
      return (
        <svg {...p}>
          <path d="M5 6h14M5 12h14M5 18h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          <circle cx="9" cy="6" r="2.2" fill="var(--bg)" stroke="currentColor" strokeWidth="1.7" />
          <circle cx="15" cy="12" r="2.2" fill="var(--bg)" stroke="currentColor" strokeWidth="1.7" />
          <circle cx="8" cy="18" r="2.2" fill="var(--bg)" stroke="currentColor" strokeWidth="1.7" />
        </svg>
      );
    case "pulse":
      return (
        <svg {...p}>
          <path d="M3 12h4l2-5 3 10 2-6 2 3h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
  }
}

/** Navigation between the four dashboards. Sticky top bar on desktop; a fixed
 *  app-style bottom tab bar on phones (thumb-reachable, safe-area aware). */
export function TabNav({
  active,
  onChange,
  cryptoEnabled,
}: {
  active: TabKey;
  onChange: (t: TabKey) => void;
  cryptoEnabled: boolean;
}) {
  // Health check drives auth-gated probes/resets -- hide it from the read-only
  // share view (the endpoint would 401 there anyway).
  const tabs = isReadOnly ? TABS.filter((t) => t.key !== "health") : TABS;
  return (
    <nav className="tabnav" aria-label="Sekcje">
      {tabs.map((t) => {
        const dimmed = t.key === "crypto" && !cryptoEnabled;
        return (
          <button
            key={t.key}
            className={`tabnav-btn ${active === t.key ? "tabnav-btn-active" : ""}`}
            onClick={() => onChange(t.key)}
            aria-current={active === t.key ? "page" : undefined}
          >
            <span className="tabnav-ico">
              <TabIcon name={t.icon} />
              {t.dot && <span className={`venue-dot venue-dot-${t.dot} tabnav-dot`} />}
            </span>
            <span className="tabnav-label-full">{t.label}</span>
            <span className="tabnav-label-short">{t.short}</span>
            {dimmed && <span className="tabnav-off">wył.</span>}
          </button>
        );
      })}
    </nav>
  );
}
