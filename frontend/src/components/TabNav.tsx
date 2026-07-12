import { TabKey } from "../pages/types";

interface TabDef {
  key: TabKey;
  label: string;
  short: string;
  dot?: "alpaca" | "crypto";
}

const TABS: TabDef[] = [
  { key: "overview", label: "Dashboard główny", short: "Główny" },
  { key: "us", label: "Alpaca · Akcje US", short: "Akcje US", dot: "alpaca" },
  { key: "crypto", label: "Alpaca · Krypto", short: "Krypto", dot: "crypto" },
  { key: "control", label: "Centrum sterowania", short: "Sterowanie" },
];

/** Top navigation between the four dashboards. Sticky so it stays reachable
 *  while scrolling a long page; the active tab carries the accent underline. */
export function TabNav({
  active,
  onChange,
  cryptoEnabled,
}: {
  active: TabKey;
  onChange: (t: TabKey) => void;
  cryptoEnabled: boolean;
}) {
  return (
    <nav className="tabnav" aria-label="Sekcje">
      {TABS.map((t) => {
        const dimmed = t.key === "crypto" && !cryptoEnabled;
        return (
          <button
            key={t.key}
            className={`tabnav-btn ${active === t.key ? "tabnav-btn-active" : ""}`}
            onClick={() => onChange(t.key)}
            aria-current={active === t.key ? "page" : undefined}
          >
            {t.dot && <span className={`venue-dot venue-dot-${t.dot}`} />}
            <span className="tabnav-label-full">{t.label}</span>
            <span className="tabnav-label-short">{t.short}</span>
            {dimmed && <span className="tabnav-off">wył.</span>}
          </button>
        );
      })}
    </nav>
  );
}
