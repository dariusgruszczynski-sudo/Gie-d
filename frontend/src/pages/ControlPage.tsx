import { ReactNode } from "react";
import { ControlToolbar } from "../components/ControlToolbar";
import { NotificationSettings } from "../components/NotificationSettings";
import { SectionTitle } from "../components/SectionTitle";
import { ShareLinkPanel } from "../components/ShareLinkPanel";
import { VenueControls } from "../components/VenueControls";
import { EngineProfile, isReadOnly, StatusResponse } from "../api/client";
import { PageData } from "./types";

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="profile-row">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

function EngineProfileColumn({
  dot,
  title,
  status,
  profile,
  whitelistCount,
  whitelistLabel,
  extra,
}: {
  dot: "alpaca" | "extended";
  title: string;
  status: StatusResponse;
  profile: EngineProfile;
  whitelistCount: number;
  whitelistLabel: string;
  extra?: ReactNode;
}) {
  const regime = dot === "extended" ? status.extended_market_regime : status.market_regime;
  return (
    <div className="profile-col">
      <div className="profile-col-head">
        <span className={`venue-dot venue-dot-${dot}`} /> {title}
      </div>
      {extra}
      <ProfileRow label="Interwał sygnału" value={profile.signal_timeframe} />
      <ProfileRow label="Sprawdza co" value={`${profile.poll_interval_minutes} min`} />
      <ProfileRow label="Próg wybudzenia (ruch ceny)" value={`${profile.price_move_trigger_pct}%`} />
      <ProfileRow label="Heartbeat (pełna analiza)" value={`co ${profile.full_analysis_every_minutes} min`} />
      <ProfileRow label="Ryzyko / transakcję" value={`${profile.risk_per_trade_pct}% konta`} />
      <ProfileRow label="Próg pewności BUY" value={profile.min_buy_confidence.toFixed(2)} />
      {regime?.aggression_label && <ProfileRow label="Bieżąca agresja (auto)" value={regime.aggression_label} />}
      <ProfileRow label="Nowe wejścia / dzień" value={`do ${profile.max_new_positions_per_day}`} />
      <ProfileRow label="Równoległe pozycje" value={`do ${profile.max_concurrent_positions}`} />
      <ProfileRow label="Min. czas trzymania" value={`${profile.min_hold_minutes} min`} />
      <ProfileRow label="Maks. wielkość pozycji" value={`${profile.max_position_pct}% konta`} />
      <ProfileRow label="Przydział kapitału" value={`${profile.allocation_pct}% konta`} />
      <ProfileRow label="Zakres stop-loss" value={`-${profile.stop_loss_min_pct}% do -${profile.stop_loss_max_pct}%`} />
      <ProfileRow label="Reward/risk (trailing arm)" value={`${profile.reward_risk_ratio}×`} />
      <ProfileRow label="Trailing stop" value={`${(profile.trailing_stop_frac * 100).toFixed(0)}% dystansu stopa`} />
      <ProfileRow
        label="Częściowa realizacja"
        value={`${(profile.partial_take_profit_frac * 100).toFixed(0)}% przy +${profile.partial_take_profit_r}R`}
      />
      <ProfileRow label="Instrumenty (whitelist)" value={`${whitelistCount} ${whitelistLabel}`} />
    </div>
  );
}

/** Zachowanie silników jest sterowane profilami w konfiguracji (.env / strategy
 *  profiles). Tu pokazujemy DOKŁADNIE aktualne nastawy każdego silnika, jeden
 *  do jednego z tym, na czym silnik faktycznie działa (effective_settings) --
 *  a akcje (START/STOP itd.) są w panelach obok. */
function EngineProfiles({ status }: { status: StatusResponse }) {
  return (
    <div className="panel">
      <h2 style={{ marginTop: 0 }}>Zachowanie silników — dokładne nastawy</h2>
      <p className="subtitle">
        To realnie działające parametry (nie przybliżenie) — dokładnie to, na czym silnik teraz pracuje. Zmienia się
        je w <code>.env</code> na serwerze, po czym restart apki.
      </p>
      <div className="profile-grid">
        <EngineProfileColumn
          dot="alpaca"
          title="Akcje US (sesja dzienna)"
          status={status}
          profile={status.profiles.alpaca}
          whitelistCount={status.whitelist.length}
          whitelistLabel="tickerów"
        />
        <EngineProfileColumn
          dot="extended"
          title="Poza sesją (pre & after-market)"
          status={status}
          profile={status.profiles.extended}
          whitelistCount={status.extended_whitelist.length}
          whitelistLabel="par"
          extra={
            <>
              <ProfileRow label="Silnik" value={status.extended_enabled ? "włączony" : "wyłączony"} />
              <ProfileRow label="Handel" value={status.extended_paused ? "zatrzymany" : "aktywny"} />
            </>
          }
        />
      </div>
    </div>
  );
}

/** Centrum sterowania: wszystkie akcje (START/STOP per silnik, raport, restart),
 *  powiadomienia push i nastawy zachowań silników w jednym miejscu. */
export function ControlPage({ data }: { data: PageData }) {
  const { status, refresh, muted, toggleMuted } = data;
  return (
    <>
      {isReadOnly && (
        <div className="panel">
          <p className="subtitle" style={{ margin: 0 }}>
            Widok tylko do odczytu — sterowanie silnikami, powiadomienia i ręczne transakcje są ukryte. Poniżej podgląd
            nastaw.
          </p>
        </div>
      )}

      {!isReadOnly && (
        <>
          <SectionTitle eyebrow="Sterowanie" title="Silniki — START / STOP" />
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
              venue="extended"
              label="Silnik — Poza sesją"
              paused={status.extended_paused}
              enabled={status.extended_enabled}
              onChanged={refresh}
            />
          </div>

          <SectionTitle eyebrow="Akcje" title="Panel operatora" />
          <ControlToolbar
            status={status}
            onChanged={refresh}
            muted={muted}
            onToggleMuted={toggleMuted}
            onShutdown={data.shutdown}
          />

          <SectionTitle eyebrow="Łączność" title="Powiadomienia i dostęp" />
          <NotificationSettings />
          <ShareLinkPanel />
        </>
      )}

      <SectionTitle eyebrow="Nastawy" title="Profile silników" />
      <EngineProfiles status={status} />
    </>
  );
}
