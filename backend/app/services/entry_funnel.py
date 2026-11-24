"""Lejek wejścia (#6/#7 z backloga) — „dlaczego bot nie wchodzi".

Czysta agregacja po JUŻ zapisanych decyzjach silnika. Każda zablokowana próba
BUY ma ustawione `rejection_reason` z konkretnej bramki (patrz trading_engine:
evaluate_and_execute). Tutaj klasyfikujemy ten tekst do kubełka bramki i liczymy,
ilu kandydatów odpadło NA KTÓREJ bramce w oknie — bez dotykania gorącej ścieżki
(zero zmian w handlu, czysta obserwowalność).

Odpowiada wprost na ból właściciela: „automat stoi od dni, nie ma ani jednej akcji".
Lejek pokazuje, która bramka faktycznie dławi wejścia.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# Katalog bramek: (klucz, etykieta PL, lista fragmentów do dopasowania w reason).
# Kolejność = od najbardziej specyficznej do ogólnej — pierwszy trafiony wygrywa,
# więc konkretne bramki muszą być PRZED ogólnym kubełkiem ryzyka/halt.
_GATES: list[tuple[str, str, tuple[str, ...]]] = [
    ("regime", "Reżim rynku (risk-off)", ("reżim risk-off", "risk-off")),
    ("btc_core", "BTC-rdzeń — alty wstrzymane w bessie", ("btc-rdzeń", "btc-rdzen")),
    ("confluence", "Konfluencja techniczna (brak sygnału wejścia)", ("filtr konfluencji", "konfluencj")),
    ("conviction", "Próg pewności (sygnał za słaby)", ("zbyt niska pewność", "niska pewność")),
    ("concentration", "Limit koncentracji (jedna moneta za duża)", ("limit koncentracji", "koncentracj")),
    ("concurrency", "Limit równoczesnych pozycji", ("limit równoczesnych", "równoczesnych pozycji")),
    ("daily_cap", "Limit nowych wejść na dziś (anty-churn)", ("limit nowych wejść",)),
    ("allocation", "Przydział kapitału silnika wyczerpany", ("przydział kapitału",)),
    # Małe konto: wolny kapitał nie pokrywa min. zlecenia Krakena (ordermin × cena).
    # PRZED kubełkiem ryzyka, bo tekst zawiera też "niewykonaln" (łapany niżej jako risk).
    ("affordability", "Za mało kapitału na min. zlecenie Krakena", (
        "min. zlecenia", "min zlecenia", "min-zlecenia", "ordermin",
        "nie mieszczą min", "nie stać na min", "wolny kapitał",
    )),
    ("auto_demote", "Auto-degradacja (ujemna historia symbolu)", ("auto-degradacja",)),
    ("cooldown", "Cooldown po stop-lossie", ("cooldown po stop", "cooldown")),
    ("earnings", "Blackout przed earnings", ("blackout przed earnings", "earnings")),
    ("news", "News blackout", ("news blackout",)),
    ("liquidity", "Płynność / jakość danych", ("płynno", "jakość świec", "obrót")),
    ("session", "Rynek zamknięty", ("rynek zamknięty",)),
    ("risk", "Walidacja ryzyka / bezpiecznik / min-hold", (
        "bezpiecznik", "zatrzyman", "halt", "pauz", "min-hold",
        "za wcześnie", "minimalny czas", "walidacj", "niewykonaln",
    )),
]

# Słownik klucz->etykieta (do UI i stabilnej kolejności kubełków).
GATE_LABELS: dict[str, str] = {key: label for key, label, _ in _GATES}
GATE_LABELS["other"] = "Inne"


def classify_rejection(reason: str | None) -> str:
    """Mapuje tekst `rejection_reason` na klucz bramki.

    Pusty/None => "" (decyzja nie była zablokowaną próbą wejścia — np. executed
    albo HOLD; dzwoniący decyduje, co z tym zrobić). Nierozpoznany => "other"."""
    if not reason or not reason.strip():
        return ""
    r = reason.lower()
    for key, _label, needles in _GATES:
        if any(n in r for n in needles):
            return key
    return "other"


@dataclass(frozen=True)
class FunnelStage:
    key: str
    label: str
    count: int


@dataclass(frozen=True)
class EntryFunnel:
    evaluated: int          # wszystkie decyzje w oknie
    holds: int              # HOLD — brak sygnału wejścia w ogóle (szczyt lejka)
    buy_attempts: int       # action == BUY (chciał wejść)
    entered: int            # BUY faktycznie wykonane
    blocked: int            # BUY zablokowane przez bramkę
    gates: list[FunnelStage]        # rozbicie zablokowanych po bramkach, malejąco
    top_gate: FunnelStage | None    # najczęstsza bramka blokująca ("dlaczego nie wchodzi")
    samples: dict[str, str]         # klucz bramki -> przykładowy pełny reason

    @property
    def fill_rate(self) -> float | None:
        """#10 fill-rate: ile prób wejścia faktycznie weszło (entered/buy_attempts).
        None gdy zero prób (nie ma czego liczyć)."""
        if self.buy_attempts <= 0:
            return None
        return self.entered / self.buy_attempts

    def as_dict(self) -> dict:
        return {
            "evaluated": self.evaluated,
            "holds": self.holds,
            "buy_attempts": self.buy_attempts,
            "entered": self.entered,
            "blocked": self.blocked,
            "fill_rate": self.fill_rate,
            "gates": [{"key": g.key, "label": g.label, "count": g.count} for g in self.gates],
            "top_gate": (
                {"key": self.top_gate.key, "label": self.top_gate.label, "count": self.top_gate.count}
                if self.top_gate else None
            ),
            "samples": self.samples,
        }


def _norm(d: object) -> tuple[str, bool, str | None]:
    """Wyciąga (action, executed, rejection_reason) z dicta albo z obiektu ORM."""
    if isinstance(d, dict):
        return (
            str(d.get("action") or "").upper(),
            bool(d.get("executed")),
            d.get("rejection_reason"),
        )
    return (
        str(getattr(d, "action", "") or "").upper(),
        bool(getattr(d, "executed", False)),
        getattr(d, "rejection_reason", None),
    )


def entry_funnel(decisions: Iterable[object]) -> EntryFunnel:
    """Buduje lejek z listy decyzji (dicty lub obiekty ORM z polami
    action/executed/rejection_reason). Czysta funkcja — bez DB, łatwa do testu."""
    evaluated = holds = buy_attempts = entered = blocked = 0
    counts: dict[str, int] = {}
    samples: dict[str, str] = {}

    for d in decisions:
        evaluated += 1
        action, executed, reason = _norm(d)
        if action == "HOLD":
            holds += 1
            continue
        if action != "BUY":
            continue  # SELL i wyjścia mechaniczne nie są częścią lejka WEJŚCIA
        buy_attempts += 1
        if executed:
            entered += 1
            continue
        key = classify_rejection(reason)
        if not key:
            continue  # BUY niewykonane, ale bez powodu — pomijamy (nie klasyfikowalne)
        blocked += 1
        counts[key] = counts.get(key, 0) + 1
        if key not in samples and reason:
            samples[key] = reason.strip()

    gates = [
        FunnelStage(key=k, label=GATE_LABELS.get(k, k), count=c)
        for k, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    top_gate = gates[0] if gates else None
    return EntryFunnel(
        evaluated=evaluated, holds=holds, buy_attempts=buy_attempts,
        entered=entered, blocked=blocked, gates=gates, top_gate=top_gate,
        samples=samples,
    )
