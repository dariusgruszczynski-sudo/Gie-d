"""Lejek wejścia (#6/#7): klasyfikacja bramek + agregacja „dlaczego nie wchodzi"."""
from app.services.entry_funnel import classify_rejection, entry_funnel


def test_classify_known_gates():
    assert classify_rejection("Reżim risk-off (VIX wysoki) — nowe wejście tylko defensywne") == "regime"
    assert classify_rejection("Tryb BTC-rdzeń: BTC w trendzie spadkowym — wejście w ETH/USD wstrzymane") == "btc_core"
    assert classify_rejection("Filtr konfluencji: brak zgodnego sygnału (score 1/3)") == "confluence"
    assert classify_rejection("Zbyt niska pewność: 0.40 < próg 0.55") == "conviction"
    assert classify_rejection("Limit koncentracji: BTC to już 20% konta (sufit 15%)") == "concentration"
    assert classify_rejection("Limit równoczesnych pozycji osiągnięty (5)") == "concurrency"
    assert classify_rejection("Limit nowych wejść na dziś osiągnięty (3)") == "daily_cap"
    assert classify_rejection("Silnik osiągnął swój przydział kapitału (50% konta)") == "allocation"
    assert classify_rejection("Auto-degradacja PEPE: ujemna historia (1W/4L)") == "auto_demote"
    assert classify_rejection("Cooldown po stop-lossie: ETH zablokowany jeszcze ~30 min") == "cooldown"
    assert classify_rejection("Rynek zamknięty -- transakcja niewykonana") == "session"


def test_classify_affordability_before_generic_risk():
    """Małe konto: brak kapitału na min. zlecenie to własna bramka (kapitał), NIE
    generyczny kubełek ryzyka — mimo że tekst zawiera 'niewykonalne'."""
    assert classify_rejection(
        "Za mało kapitału na min. zlecenia Krakena: wolny €3.20 < min ATOM €4.24 (× bufor) — pomijam 5 kandydatów"
    ) == "affordability"
    assert classify_rejection(
        "Zlecenie niewykonane: Rozmiar SOL: twarde limity (sufit €2.10) nie mieszczą min. zlecenia Krakena €7.50 — pomijam"
    ) == "affordability"


def test_classify_empty_and_unknown():
    assert classify_rejection(None) == ""
    assert classify_rejection("   ") == ""
    assert classify_rejection("coś zupełnie nowego i nieznanego") == "other"


def test_funnel_counts_and_top_gate():
    decisions = [
        {"action": "HOLD", "executed": False, "rejection_reason": None},
        {"action": "HOLD", "executed": False, "rejection_reason": None},
        {"action": "BUY", "executed": True, "rejection_reason": None},
        {"action": "BUY", "executed": False, "rejection_reason": "Tryb BTC-rdzeń: BTC spada — wejście wstrzymane"},
        {"action": "BUY", "executed": False, "rejection_reason": "Tryb BTC-rdzeń: BTC spada — wejście wstrzymane"},
        {"action": "BUY", "executed": False, "rejection_reason": "Filtr konfluencji: brak sygnału"},
        {"action": "SELL", "executed": True, "rejection_reason": None},
    ]
    f = entry_funnel(decisions)
    assert f.evaluated == 7
    assert f.holds == 2
    assert f.buy_attempts == 4
    assert f.entered == 1
    assert f.blocked == 3
    assert f.top_gate is not None and f.top_gate.key == "btc_core" and f.top_gate.count == 2
    assert {g.key for g in f.gates} == {"btc_core", "confluence"}
    assert "btc_core" in f.samples
    assert f.exits == 1  # jeden wykonany SELL w oknie


def test_funnel_counts_exits_not_as_entries():
    """Same wyjścia (stop/breakeven) bez nowych wejść: buy_attempts=0, ale exits>0 —
    panel ma pokazać, że handel trwał po stronie wyjść, nie udawać zastoju (skarga
    'jakie 7 dni jak wczoraj było kilka' — widoczne sprzedaże, a lejek mówił 'zero')."""
    decisions = [
        {"action": "SELL", "executed": True, "rejection_reason": None},
        {"action": "SELL", "executed": True, "rejection_reason": None},
        {"action": "SELL", "executed": False, "rejection_reason": "min-hold: za wcześnie"},  # niewykonany SELL nie liczy się jako wyjście
        {"action": "HOLD", "executed": False, "rejection_reason": None},
    ]
    f = entry_funnel(decisions)
    assert f.buy_attempts == 0 and f.entered == 0 and f.blocked == 0
    assert f.exits == 2  # tylko WYKONANE zamknięcia
    assert f.as_dict()["exits"] == 2


def test_funnel_fill_rate():
    # 1 weszło na 4 próby BUY -> 25%.
    decisions = [
        {"action": "BUY", "executed": True, "rejection_reason": None},
        {"action": "BUY", "executed": False, "rejection_reason": "Filtr konfluencji: brak"},
        {"action": "BUY", "executed": False, "rejection_reason": "Filtr konfluencji: brak"},
        {"action": "BUY", "executed": False, "rejection_reason": "Cooldown po stop-lossie: ETH"},
    ]
    f = entry_funnel(decisions)
    assert f.fill_rate == 0.25
    assert f.as_dict()["fill_rate"] == 0.25
    # Zero prób -> None (nie ma czego liczyć).
    assert entry_funnel([{"action": "HOLD", "executed": False, "rejection_reason": None}]).fill_rate is None


def test_funnel_empty_has_no_top_gate():
    f = entry_funnel([])
    assert f.evaluated == 0 and f.blocked == 0 and f.top_gate is None
    assert f.as_dict()["top_gate"] is None


def test_funnel_accepts_orm_like_objects():
    class D:
        def __init__(self, action, executed, reason):
            self.action, self.executed, self.rejection_reason = action, executed, reason

    f = entry_funnel([D("BUY", False, "Zbyt niska pewność: 0.3 < 0.5"), D("BUY", True, None)])
    assert f.entered == 1 and f.blocked == 1 and f.top_gate.key == "conviction"


def test_funnel_handles_tradeaction_enum_orm():
    """REGRESJA: żywy endpoint czyta obiekty ORM, gdzie `action` to enum TradeAction
    (str, Enum). str(enum) daje 'TradeAction.HOLD' != 'HOLD', więc stary kod liczył
    WSZYSTKO jako 0 (objaw właściciela: ocen=53, a bez sygnału/chciał/weszło/zdławione=0).
    Karmimy PRAWDZIWYMI enumami i sprawdzamy, że liczniki działają."""
    from app.models import TradeAction

    class D:
        def __init__(self, action, executed, reason):
            self.action, self.executed, self.rejection_reason = action, executed, reason

    rows = [
        D(TradeAction.HOLD, False, None),                 # bez sygnału
        D(TradeAction.HOLD, False, None),
        D(TradeAction.BUY, True, None),                   # weszło
        D(TradeAction.BUY, False, "Filtr konfluencji: brak sygnału"),  # zdławione
        D(TradeAction.SELL, True, None),                  # wyjście
    ]
    f = entry_funnel(rows)
    assert f.evaluated == 5
    assert f.holds == 2          # NIE 0 — to był bug
    assert f.buy_attempts == 2
    assert f.entered == 1
    assert f.blocked == 1
    assert f.exits == 1
