"""Reakcja na katalizatory — rdzeń Filara INFORMACJA (analiza 2026-11-21).

Bot czyta feedy 24/7 i reaguje na ZDARZENIA (hack, exploit, depeg, delisting,
unlock, listing), zanim cena je wchłonie — tam, gdzie człowiek śpi. Udowodnione:
edge w CENIE nie istnieje (173k próbek), więc przewaga musi być w INFORMACJI.

Ten moduł to CZYSTY rdzeń decyzyjny: bierze ustrukturyzowane zdarzenie + listę
trzymanych monet i zwraca AKCJĘ (exit_now / block_entry / reduce / alert / ignore).
Feedy (Rekt/PeckShield/news) i klasyfikator LLM (powaga zdarzenia) wpinają się
PÓŹNIEJ — tu logika akcji jest pure i w pełni testowalna.

DYSCYPLINA (wbudowana): master-switch domyślnie OFF; a nawet włączony startuje w
trybie 'alert_only' — tylko alarmuje, NIGDY nie handluje — aż udowodni trafność na
realnych zdarzeniach. Dopiero wtedy właściciel przełącza na 'act'. Zero wdrożeń na wiarę.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Zdarzenia, które są JEDNOZNACZNIE złe dla trzymanej pozycji -> wyjście.
EXIT_KINDS = frozenset({"hack", "exploit", "depeg", "delisting", "rug", "insolvency"})
# Zdarzenia, które psują PRZYSZŁOŚĆ (podaż/ryzyko) -> nie wchodź/zredukuj, ale nie panikuj.
AVOID_KINDS = frozenset({"unlock", "lawsuit", "regulatory_ban"})
# Zdarzenia potencjalnie BYCZE -> tylko alarm (nigdy auto-kupno bez walidacji).
BULLISH_KINDS = frozenset({"listing", "partnership", "mainnet", "upgrade"})

ACTIONS = ("exit_now", "block_entry", "reduce", "alert", "ignore")


@dataclass(frozen=True)
class CryptoEvent:
    kind: str                       # jak wyżej (hack/unlock/listing/...)
    symbol: str | None              # baza, np. "ETH" (None = całorynkowe)
    severity: float                 # 0..1, z klasyfikatora (LLM/keyword); 1 = katastrofa
    source: str = ""                # skąd (rekt.news, peckshield, coindesk, ...)
    headline: str = ""
    url: str = ""
    ts: str = ""
    days_until: float | None = None  # dla zdarzeń zaplanowanych (unlock za N dni)


@dataclass(frozen=True)
class EventDecision:
    action: str                     # jeden z ACTIONS
    symbol: str | None
    reason: str
    acted: bool                     # czy to realna akcja handlowa (True) czy tylko alarm (False)

    def as_dict(self) -> dict:
        return {"action": self.action, "symbol": self.symbol, "reason": self.reason, "acted": self.acted}


def _held(symbol: str | None, held_symbols) -> bool:
    if not symbol:
        return False
    hs = {str(s).upper().split("/")[0] for s in (held_symbols or [])}
    return symbol.upper().split("/")[0] in hs


def event_action(event: CryptoEvent, held_symbols, settings) -> EventDecision:
    """Decyzja na pojedyncze zdarzenie. CZYSTA funkcja (bez DB, bez brokera).

    `held_symbols`: iterowalne symboli trzymanych ("ETH" lub "ETH/USD").
    `settings`: musi mieć crypto_event_* (patrz config). Gdy master OFF -> 'ignore'.
    W trybie 'alert_only' każda decyzja handlowa jest SPROWADZANA do 'alert' (acted=False)."""
    enabled = bool(getattr(settings, "crypto_event_response_enabled", False))
    if not enabled:
        return EventDecision("ignore", event.symbol, "tor katalizatorów wyłączony (master OFF)", False)

    mode = getattr(settings, "crypto_event_action_mode", "alert_only")
    exit_min = float(getattr(settings, "crypto_event_exit_min_severity", 0.6))
    alert_min = float(getattr(settings, "crypto_event_alert_min_severity", 0.3))
    unlock_days = float(getattr(settings, "crypto_event_unlock_block_days", 3.0))
    sev = max(0.0, min(1.0, float(event.severity or 0.0)))
    held = _held(event.symbol, held_symbols)

    def gated(real_action: str, reason: str) -> EventDecision:
        # Dyscyplina shadow-first: realna akcja tylko w trybie 'act'; inaczej alarm.
        if mode == "act":
            return EventDecision(real_action, event.symbol, reason, True)
        return EventDecision("alert", event.symbol, f"[alert_only] {reason}", False)

    # 1) WYJŚCIE: jednoznacznie złe zdarzenie na TRZYMANEJ pozycji, powaga ≥ próg.
    if event.kind in EXIT_KINDS and held and sev >= exit_min:
        return gated("exit_now", f"{event.kind} na trzymanej {event.symbol} (powaga {sev:.2f}) — de-risk natychmiast")

    # 2) To samo złe zdarzenie, ale moneta NIEtrzymana -> blokuj nowe wejście + alarm.
    if event.kind in EXIT_KINDS and sev >= exit_min:
        return gated("block_entry", f"{event.kind} na {event.symbol} (powaga {sev:.2f}) — blokuj nowe wejście")

    # 3) Zdarzenie podażowe/ryzyka (unlock itp.): blokuj wejście, gdy blisko.
    if event.kind in AVOID_KINDS:
        close = event.days_until is None or event.days_until <= unlock_days
        if close and sev >= alert_min:
            return gated("block_entry", f"{event.kind} {event.symbol} w ≤{unlock_days:.0f} dni — blokuj/odłóż wejście")

    # 4) Bycze zdarzenie: NIGDY auto-kupno bez walidacji — tylko alarm do przeglądu.
    if event.kind in BULLISH_KINDS and sev >= alert_min:
        return EventDecision("alert", event.symbol, f"{event.kind} {event.symbol} — potencjalny katalizator (wymaga walidacji, bez auto-kupna)", False)

    # 5) Reszta: alarm, jeśli dość poważne; inaczej szum -> ignoruj.
    if sev >= alert_min:
        return EventDecision("alert", event.symbol, f"{event.kind} {event.symbol} (powaga {sev:.2f})", False)
    return EventDecision("ignore", event.symbol, f"poniżej progu alarmu (powaga {sev:.2f})", False)


# Lekki fallback klasyfikacji powagi ze słów kluczowych — używany TYLKO gdy nie ma
# klasyfikatora LLM (który poda powagę rzetelniej). Celowo konserwatywny.
_SEV_WORDS = {
    0.95: ("drained", "exploited", "stolen", "hacked", "insolvent", "halted withdrawals", "depeg", "rug"),
    0.75: ("exploit", "vulnerability", "attack", "delisting", "delisted", "lawsuit", "sec charges"),
    0.5: ("unlock", "vesting", "investigation", "outage", "downtime"),
    0.4: ("listing", "listed", "partnership", "mainnet", "upgrade"),
}


def classify_severity(text: str) -> float:
    """Zgrubna powaga 0..1 ze słów kluczowych (fallback bez LLM). Bierze NAJWYŻSZY trafiony próg."""
    if not text:
        return 0.0
    t = text.lower()
    best = 0.0
    for sev, words in _SEV_WORDS.items():
        if any(w in t for w in words):
            best = max(best, sev)
    return best


@dataclass
class EventLog:
    """Prosty bufor ostatnich decyzji — do panelu „bot czyta 24/7" i audytu."""
    items: list = field(default_factory=list)
    cap: int = 100

    def add(self, event: CryptoEvent, decision: EventDecision) -> None:
        self.items.insert(0, {"event": event.__dict__, "decision": decision.as_dict()})
        del self.items[self.cap:]
