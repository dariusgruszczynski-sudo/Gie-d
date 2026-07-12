import { BudgetGauge } from "../components/BudgetGauge";
import { ControlToolbar } from "../components/ControlToolbar";
import { NotificationSettings } from "../components/NotificationSettings";
import { ShareLinkPanel } from "../components/ShareLinkPanel";
import { VenueControls } from "../components/VenueControls";
import { isReadOnly, StatusResponse } from "../api/client";
import { PageData } from "./types";

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="profile-row">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

/** Zachowanie silników jest sterowane profilami w konfiguracji (.env / strategy
 *  profiles). Tu pokazujemy AKTUALNE nastawy jednym rzutem oka — co realnie
 *  ogranicza handel — a akcje (START/STOP itd.) są w panelach obok. */
function EngineProfiles({ status }: { status: StatusResponse }) {
  return (
    <div className="panel">
      <h2 style={{ marginTop: 0 }}>Zachowanie silników — aktualne nastawy</h2>
      <p className="subtitle">
        To realnie działające progi ryzyka. Zmienia się je w <code>.env</code> na serwerze (profil akcji vs
        agresywniejszy profil krypto), po czym restart apki. Poniżej stan po ostatnim starcie.
      </p>
      <div className="profile-grid">
        <div className="profile-col">
          <div className="profile-col-head">
            <span className="venue-dot venue-dot-alpaca" /> Akcje US (średnio agresywnie)
          </div>
          <ProfileRow label="Limit straty dzienny" value={`-${status.daily_loss_limit_pct}%`} />
          <ProfileRow label="Limit straty tygodniowy" value={`-${status.weekly_loss_limit_pct}%`} />
          <ProfileRow label="Maks. wielkość pozycji" value={`${status.max_position_pct}% konta`} />
          <ProfileRow label="Instrumenty (whitelist)" value={`${status.whitelist.length} tickerów`} />
          <ProfileRow label="Częstość analizy" value={`co ${status.poll_interval_minutes} min`} />
        </div>
        <div className="profile-col">
          <div className="profile-col-head">
            <span className="venue-dot venue-dot-crypto" /> Krypto 24/7 (agresywnie)
          </div>
          <ProfileRow label="Silnik" value={status.crypto_enabled ? "włączony" : "wyłączony"} />
          <ProfileRow label="Handel" value={status.crypto_paused ? "zatrzymany" : "aktywny"} />
          <ProfileRow label="Instrumenty (whitelist)" value={`${status.crypto_whitelist.length} par`} />
          <ProfileRow label="Rynek" value="24/7 (także noce i weekendy)" />
        </div>
      </div>
    </div>
  );
}

function BudgetPanel({ status }: { status: StatusResponse }) {
  const fmtTok = (v: number) =>
    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(2)}M` : v >= 1_000 ? `${(v / 1_000).toFixed(1)}k` : Math.round(v).toString();
  return (
    <div className="panel budget-panel">
      <h2 style={{ marginTop: 0 }}>Claude — budżet i tokeny (ten miesiąc)</h2>
      <div className="budget-panel-body">
        <BudgetGauge pctUsed={status.claude_budget_pct_used} alert={status.claude_budget_alert} />
        <div className="budget-panel-figs">
          <ProfileRow
            label="Wydano (szacunek)"
            value={`$${status.claude_spend_usd_this_month.toFixed(2)} / $${status.claude_monthly_budget_usd.toFixed(2)}`}
          />
          <ProfileRow label="Tokeny łącznie" value={fmtTok(status.claude_total_tokens_this_month)} />
          <ProfileRow
            label="Wejście / wyjście"
            value={`${fmtTok(status.claude_input_tokens_this_month)} / ${fmtTok(status.claude_output_tokens_this_month)}`}
          />
        </div>
      </div>
      {status.claude_budget_alert && (
        <p className="subtitle" style={{ marginBottom: 0 }}>
          💰 Ponad {status.claude_budget_pct_used.toFixed(0)}% budżetu — rozważ doładowanie na console.anthropic.com.
        </p>
      )}
    </div>
  );
}

/** Centrum sterowania: wszystkie akcje (START/STOP per silnik, raport, restart),
 *  powiadomienia push, nastawy zachowań silników i budżet Claude w jednym
 *  miejscu. */
export function ControlPage({ data }: { data: PageData }) {
  const { status, refresh, muted, toggleMuted } = data;
  return (
    <>
      {isReadOnly && (
        <div className="panel">
          <p className="subtitle" style={{ margin: 0 }}>
            Widok tylko do odczytu — sterowanie silnikami, powiadomienia i ręczne transakcje są ukryte. Poniżej podgląd
            nastaw i budżetu.
          </p>
        </div>
      )}

      {!isReadOnly && (
        <>
          <div className="grid">
            <VenueControls
              venue="alpaca"
              label="Silnik — Akcje US"
              paused={status.is_paused}
              halted={status.is_halted}
              enabled
              onChanged={refresh}
            />
            <VenueControls
              venue="crypto"
              label="Silnik — Krypto 24/7"
              paused={status.crypto_paused}
              enabled={status.crypto_enabled}
              onChanged={refresh}
            />
          </div>

          <ControlToolbar status={status} onChanged={refresh} muted={muted} onToggleMuted={toggleMuted} />

          <NotificationSettings />

          <ShareLinkPanel />
        </>
      )}

      <EngineProfiles status={status} />

      <BudgetPanel status={status} />
    </>
  );
}
