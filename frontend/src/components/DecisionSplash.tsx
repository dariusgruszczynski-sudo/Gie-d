import { useEffect } from "react";
import { Decision } from "../api/client";
import { playDecisionSound } from "../decisionSound";

function BuyIcon() {
  return (
    <svg width="76" height="76" viewBox="0 0 72 72" aria-hidden="true">
      <circle cx="36" cy="36" r="33" fill="none" stroke="var(--green)" strokeWidth="2" opacity="0.45" />
      <path d="M36 52 V20 M24 32 L36 20 L48 32" stroke="var(--green)" strokeWidth="4.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SellIcon() {
  return (
    <svg width="76" height="76" viewBox="0 0 72 72" aria-hidden="true">
      <circle cx="36" cy="36" r="33" fill="none" stroke="var(--red)" strokeWidth="2" opacity="0.45" />
      <path d="M36 20 V52 M24 40 L36 52 L48 40" stroke="var(--red)" strokeWidth="4.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function HoldIcon() {
  return (
    <svg width="76" height="76" viewBox="0 0 72 72" aria-hidden="true">
      <circle cx="36" cy="36" r="33" fill="none" stroke="var(--gold-bright)" strokeWidth="2" opacity="0.45" />
      <path
        d="M12 36 H25 L29 24 L36 48 L43 28 L47 36 H60"
        stroke="var(--gold-bright)"
        strokeWidth="3.2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const CONFIG = {
  BUY: { title: "KUPIŁEŚ", className: "splash-buy", Icon: BuyIcon },
  SELL: { title: "SPRZEDAŁEŚ", className: "splash-sell", Icon: SellIcon },
  HOLD: { title: "HOLD THE LINE", className: "splash-hold", Icon: HoldIcon },
} as const;

const AUTO_DISMISS_MS = 4200;

export function DecisionSplash({ decision, onDismiss }: { decision: Decision; onDismiss: () => void }) {
  const config = CONFIG[decision.action];

  useEffect(() => {
    playDecisionSound(decision.action);
    const timer = setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [decision.id]);

  return (
    <div className={`decision-splash ${config.className}`} onClick={onDismiss} role="status">
      <div className="decision-splash-inner">
        <config.Icon />
        <h2>{config.title}</h2>
        {decision.symbol && <p className="decision-splash-symbol">{decision.symbol}</p>}
        {decision.reasoning && <p className="decision-splash-reason">{decision.reasoning}</p>}
        <p className="decision-splash-hint">kliknij, aby zamknąć</p>
      </div>
    </div>
  );
}
