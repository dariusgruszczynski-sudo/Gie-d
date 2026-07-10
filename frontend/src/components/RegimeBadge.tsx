import { MarketRegime } from "../api/client";

const REGIME_META: Record<string, { label: string; className: string; icon: string }> = {
  risk_on: { label: "RISK-ON", className: "regime-on", icon: "▲" },
  neutral: { label: "NEUTRALNY", className: "regime-neutral", icon: "●" },
  risk_off: { label: "RISK-OFF", className: "regime-off", icon: "▼" },
};

// Reżim rynku wyliczony przez silnik (trend benchmarku + VIX + dzisiejsza
// sesja). W risk_off automat kupuje tylko nazwy defensywne/odwrotne.
export function RegimeBadge({ regime, prefix = "Rynek" }: { regime: MarketRegime | null; prefix?: string }) {
  if (!regime) return null;
  const meta = REGIME_META[regime.regime] ?? REGIME_META.neutral;
  const title = regime.reasons.length ? regime.reasons.join(" · ") : "Reżim rynku";
  return (
    <span className={`regime-badge ${meta.className}`} title={title}>
      <span className="regime-badge-icon">{meta.icon}</span>
      {prefix}: {meta.label}
    </span>
  );
}
