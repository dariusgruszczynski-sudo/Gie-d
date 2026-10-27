import json
from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.api import routes_dashboard
from app.api.routes_dashboard import _account_view, get_claude_edge, get_portfolio, get_status
from app.models import PortfolioSnapshot
from app.services import market_hours


def test_account_view_counts_shared_cash_once(db_session):
    """One Alpaca account, two engines: both per-engine snapshots record the
    SAME account cash. The account view must count that cash ONCE plus each
    engine's position value -- not sum the two snapshot totals (which would
    double-count the cash, the "two portfolios" bug)."""
    now = datetime.now(UTC)
    # cash=100 in both; equities holds 50 of positions, extended holds 30.
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=150.0, usdt_balance=100.0, venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=130.0, usdt_balance=100.0, venue="extended"))
    db_session.commit()

    # Dwa silniki włączone -- ten test bada właśnie sumowanie obu nóg.
    from app.config import Settings
    acc = _account_view(db_session, Settings(extended_enabled=True))
    assert acc["cash"] == 100.0
    assert acc["equity_positions_value"] == 50.0
    assert acc["extended_positions_value"] == 30.0
    # 100 + 50 + 30 = 180, NOT 150 + 130 = 280 (cash counted once).
    assert acc["total_value"] == 180.0


def test_account_view_none_when_no_snapshots(db_session):
    assert _account_view(db_session) is None


def test_coins_tab_aggregates_pnl_per_symbol(db_session):
    """Zakładka MONETY: bilans historyczny per moneta (zarobił/stracił i ile),
    plus monety z uniwersum skanera oznaczone jako obserwowane (bilans 0)."""
    from app.api.routes_dashboard import get_coins
    from app.models import Trade, TradeMode
    from app.services import risk_manager

    now = datetime.now(UTC)
    # SOL: kupione 100, sprzedane 130 -> +30 (wygrana). ETH: 100 -> 80 -> -20 (strata).
    db_session.add(Trade(timestamp=now - timedelta(days=3), symbol="SOL/USD", side="BUY", quantity=1.0, price=100.0, usdt_value=100.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(Trade(timestamp=now - timedelta(days=2), symbol="SOL/USD", side="SELL", quantity=1.0, price=130.0, usdt_value=130.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(Trade(timestamp=now - timedelta(days=3), symbol="ETH/USD", side="BUY", quantity=1.0, price=100.0, usdt_value=100.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(Trade(timestamp=now - timedelta(days=1), symbol="ETH/USD", side="SELL", quantity=1.0, price=80.0, usdt_value=80.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()
    # Uniwersum skanera: SOL + AVAX (AVAX nietknięte -> ma być "watch").
    st = risk_manager.get_state(db_session)
    st.crypto_scanner_universe_json = json.dumps({"universe": ["SOL/USD", "AVAX/USD"], "pool_size": 36})
    db_session.commit()

    body = get_coins(db=db_session)
    by = {c["symbol"]: c for c in body["coins"]}
    assert by["SOL/USD"]["realized_usd"] == 30.0 and by["SOL/USD"]["status"] == "won"
    assert by["ETH/USD"]["realized_usd"] == -20.0 and by["ETH/USD"]["status"] == "lost"
    assert by["AVAX/USD"]["status"] == "watch" and by["AVAX/USD"]["closes"] == 0
    assert by["SOL/USD"]["in_universe"] is True and by["ETH/USD"]["in_universe"] is False
    # Najlepszy zarabiacz przed stratnym; obserwowane na końcu.
    assert body["coins"][0]["symbol"] == "SOL/USD"
    assert body["coins"][-1]["symbol"] == "AVAX/USD"
    assert body["summary"]["total_realized_usd"] == 10.0
    assert body["summary"]["won_count"] == 1 and body["summary"]["lost_count"] == 1


def test_coins_tab_excludes_pre_epoch_blowout(db_session, settings):
    """„Żeby było dobrze": zamknięcia SPRZED startu obecnej strategii krypto
    (crypto_stats_epoch_default — po blowoutcie) są wykluczone z bilansu, żeby
    błąd operacyjny nie zatruwał werdyktu. Pełna historia zostaje w logu."""
    from app.api.routes_dashboard import get_coins
    from app.models import Trade, TradeMode

    s = settings.model_copy(update={"crypto_stats_epoch_default": "2026-10-16T00:00:00+00:00"})
    before = datetime(2026, 10, 14, tzinfo=UTC)   # blowout — przed epoką
    after = datetime(2026, 10, 20, tzinfo=UTC)     # obecna strategia — po epoce
    # BLOW/USD: duża strata w blowoutcie (ma zniknąć z bilansu).
    db_session.add(Trade(timestamp=before, symbol="BLOW/USD", side="BUY", quantity=1.0, price=1000.0, usdt_value=1000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(Trade(timestamp=before, symbol="BLOW/USD", side="SELL", quantity=1.0, price=100.0, usdt_value=100.0, mode=TradeMode.LIVE, venue="crypto"))
    # SOL/USD: realny trejd po epoce (ma się liczyć).
    db_session.add(Trade(timestamp=after, symbol="SOL/USD", side="BUY", quantity=1.0, price=100.0, usdt_value=100.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(Trade(timestamp=after, symbol="SOL/USD", side="SELL", quantity=1.0, price=120.0, usdt_value=120.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()

    body = get_coins(db=db_session, settings=s)
    by = {c["symbol"]: c for c in body["coins"]}
    assert "BLOW/USD" not in by                       # blowout wykluczony z bilansu
    assert by["SOL/USD"]["realized_usd"] == 20.0       # trejd po epoce się liczy
    assert body["summary"]["total_realized_usd"] == 20.0  # NIE −880 z blowoutu
    assert body["summary"]["since_epoch"] == "2026-10-16T00:00:00+00:00"


def test_portfolio_cost_basis_covers_non_whitelist_held(db_session, settings):
    """+/- na pozycji: cena wejścia musi się policzyć dla KAŻDEJ trzymanej nazwy,
    także spoza statycznej whitelisty (np. z dynamicznego uniwersum). Wcześniej
    pętla szła tylko po whiteliście, więc taka pozycja nie pokazywała zysku."""
    from app.models import Trade, TradeMode

    now = datetime.now(UTC)
    # TSLA nie jest w domyślnej trading_whitelist -- kupione z uniwersum.
    db_session.add(Trade(timestamp=now, symbol="TSLA", side="BUY", quantity=2.0, price=200.0,
                         usdt_value=400.0, mode=TradeMode.LIVE, venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=550.0, usdt_balance=50.0,
                                     balances_json=json.dumps({"TSLA": 2.0}),
                                     prices_json=json.dumps({"TSLA": 250.0}), venue="alpaca"))
    db_session.commit()

    body = get_portfolio(limit=200, venue="alpaca", db=db_session, settings=settings)
    assert body["cost_basis"].get("TSLA") == 200.0


def test_pnl_series_is_deposit_proof(db_session, settings):
    """Krzywa 'Zysk automatu w czasie' nie może skakać przy wpłacie: przy tych
    samych pozycjach i cenach, sam wzrost gotówki (dopłata) nie zmienia P&L."""
    from app.models import Trade, TradeMode

    t0 = datetime.now(UTC) - timedelta(hours=2)
    db_session.add(Trade(timestamp=t0, symbol="SPY", side="BUY", quantity=1.0, price=100.0,
                         usdt_value=100.0, mode=TradeMode.LIVE, venue="alpaca"))
    # Snapshot 1: cash 100. Snapshot 2: cash 400 (wpłata +300), te same pozycje/ceny.
    db_session.add(PortfolioSnapshot(timestamp=t0 + timedelta(hours=1), total_value_usdt=210.0, usdt_balance=100.0,
                                     balances_json=json.dumps({"SPY": 1.0}),
                                     prices_json=json.dumps({"SPY": 110.0}), venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=t0 + timedelta(hours=2), total_value_usdt=510.0, usdt_balance=400.0,
                                     balances_json=json.dumps({"SPY": 1.0}),
                                     prices_json=json.dumps({"SPY": 110.0}), venue="alpaca"))
    db_session.commit()

    body = get_portfolio(limit=200, venue="alpaca", db=db_session, settings=settings)
    # Unrealized = (110-100)*1 = 10 na OBU snapshotach -- wpłata nic nie zmienia.
    assert body["pnl_history"] == [10.0, 10.0]


def test_status_net_result_is_realized_pnl_minus_claude_spend(db_session, settings):
    """The honest bottom line: realized P&L across BOTH engines minus what
    Claude has actually cost this month -- not brutto P&L."""
    from app.models import Trade, TradeMode
    from app.services import budget_tracker

    now = datetime.now(UTC)
    db_session.add(Trade(
        timestamp=now, symbol="SPY", side="BUY", quantity=1, price=100.0, usdt_value=100.0,
        mode=TradeMode.LIVE, venue="alpaca",
    ))
    db_session.add(Trade(
        timestamp=now, symbol="SPY", side="SELL", quantity=1, price=110.0, usdt_value=110.0,
        mode=TradeMode.LIVE, venue="alpaca",
    ))
    db_session.commit()
    budget_tracker.record_usage_cost(db_session, 4.0, 100, 100)

    body = get_status(db=db_session, settings=settings)

    assert body["realized_pnl_usd"] == 10.0
    assert body["net_result_usd"] == 6.0


def test_status_net_result_uses_lifetime_spend_not_just_this_month(db_session, settings):
    """realized_pnl_usd is cumulative since inception, so the Claude-cost side
    of net_result_usd must be too -- comparing lifetime P&L against only this
    month's spend would understate cost (and overstate "net") more and more as
    months pass."""
    from app.models import SystemState, Trade, TradeMode
    from app.services import budget_tracker

    now = datetime.now(UTC)
    db_session.add(Trade(
        timestamp=now, symbol="SPY", side="BUY", quantity=1, price=100.0, usdt_value=100.0,
        mode=TradeMode.LIVE, venue="alpaca",
    ))
    db_session.add(Trade(
        timestamp=now, symbol="SPY", side="SELL", quantity=1, price=110.0, usdt_value=110.0,
        mode=TradeMode.LIVE, venue="alpaca",
    ))
    db_session.commit()
    # Spend from previous months (already rolled over -> this_month is 0, but
    # lifetime keeps accumulating) plus a bit this month.
    budget_tracker.record_usage_cost(db_session, 20.0, 500, 500)
    state = db_session.get(SystemState, 1)
    state.claude_spend_usd_this_month = 3.0  # simulate a month rollover already happened
    db_session.commit()

    body = get_status(db=db_session, settings=settings)

    assert body["realized_pnl_usd"] == 10.0
    assert body["claude_spend_usd_this_month"] == 3.0
    # net must reflect the full $20 lifetime spend, not just this month's $3.
    assert body["net_result_usd"] == -10.0


def test_status_includes_per_engine_profiles(db_session, settings):
    body = get_status(db=db_session, settings=settings)

    assert body["profiles"]["alpaca"]["signal_timeframe"] == settings.signal_timeframe
    assert body["profiles"]["extended"]["signal_timeframe"] == settings.extended_signal_timeframe
    assert body["profiles"]["extended"]["poll_interval_minutes"] == settings.extended_poll_interval_minutes


def test_widget_endpoint_returns_compact_payload(db_session, settings):
    from app.api.routes_dashboard import get_widget
    from app.models import Trade, TradeMode

    now = datetime.now(UTC)
    # A held position + a couple of value snapshots for the sparkline.
    db_session.add(Trade(
        timestamp=now, symbol="SPY", side="BUY", quantity=2, price=100.0, usdt_value=200.0,
        mode=TradeMode.LIVE, venue="alpaca",
    ))
    db_session.add(PortfolioSnapshot(
        timestamp=now, total_value_usdt=1020.0, usdt_balance=800.0,
        balances_json=json.dumps({"SPY": 2.0}), prices_json=json.dumps({"SPY": 110.0}), venue="alpaca",
    ))
    # A MORE RECENT extended snapshot (extended polls more often) with only the
    # shared cash -- day P&L must use the COMBINED account, not this slice.
    db_session.add(PortfolioSnapshot(
        timestamp=now + timedelta(seconds=30), total_value_usdt=800.0, usdt_balance=800.0,
        balances_json=json.dumps({}), prices_json=json.dumps({}), venue="extended",
    ))
    # Day baseline = the combined account (1020), same as it's now recorded.
    from app.services import risk_manager
    st = risk_manager.get_state(db_session)
    st.day_start_value = 1020.0
    st.day_start_date = now.date().isoformat()
    db_session.commit()

    body = get_widget(db=db_session, settings=settings)

    assert body["cash"] == 800.0
    assert body["total"] == 1020.0  # 800 cash + 2*110 position
    # Flat vs baseline -> ~0%, NOT a fake -22% from the extended-only 800 slice.
    assert body["day_pnl_pct"] == 0.0
    assert isinstance(body["spark"], list) and len(body["spark"]) >= 1
    assert body["positions"][0]["asset"] == "SPY"
    assert body["positions"][0]["pnl_pct"] == 10.0  # entry 100 -> 110


def test_claude_edge_endpoint_returns_both_sides(db_session, settings):
    body = get_claude_edge(venue="alpaca", db=db_session, settings=settings)

    assert body["venue"] == "alpaca"
    assert "mechanical_only" in body
    assert "with_claude" in body


def test_portfolio_venue_filter_separates_portfolios(db_session, settings):
    """/api/portfolio?venue=... must return only that venue's snapshots, so the
    equities and extended portfolios never bleed into each other on the dashboard."""
    now = datetime.now(UTC)
    db_session.add(
        PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=500.0, venue="alpaca")
    )
    db_session.add(
        PortfolioSnapshot(timestamp=now, total_value_usdt=42.0, usdt_balance=42.0, venue="extended")
    )
    db_session.commit()

    alpaca = get_portfolio(limit=200, venue="alpaca", db=db_session, settings=settings)
    extended = get_portfolio(limit=200, venue="extended", db=db_session, settings=settings)

    assert alpaca["current"]["total_value_usdt"] == 500.0
    assert extended["current"]["total_value_usdt"] == 42.0
    assert extended["scorecard"] is None  # extended venue has no SPY scorecard


def test_portfolio_inception_is_the_very_first_snapshot_even_beyond_limit(db_session, settings):
    """/api/portfolio's `limit` truncates `history`, but `inception` must
    still reflect the true first-ever snapshot so "since the beginning" P&L
    doesn't quietly drift once more than `limit` snapshots have accumulated."""
    base = datetime.now(UTC) - timedelta(days=10)
    for i in range(5):
        db_session.add(
            PortfolioSnapshot(
                timestamp=base + timedelta(hours=i),
                total_value_usdt=1000.0 + i * 10,
                usdt_balance=1000.0,
                balances_json="{}",
                prices_json=json.dumps({"SPY": 50000.0 + i * 100}),
            )
        )
    db_session.commit()

    body = get_portfolio(limit=2, db=db_session, settings=settings)

    assert len(body["history"]) == 2
    assert body["inception"] is not None
    assert body["inception"]["total_value_usdt"] == 1000.0


def test_portfolio_inception_is_none_when_no_snapshots_exist(db_session, settings):
    body = get_portfolio(limit=200, db=db_session, settings=settings)
    assert body["current"] is None
    assert body["inception"] is None


def test_day_pnl_uses_combined_account_not_whichever_venue_polled_last(db_session, settings):
    """day_pnl_pct/week_pnl_pct must compare the combined account (cash once +
    both engines' positions) against the day/week baseline -- NOT whichever
    single venue's snapshot happens to be most recent. Extended polls far more
    often than equities, so picking "the latest snapshot" naively almost always
    picks the extended-only total, which is a completely different (usually much
    smaller) scope than an equities-baselined day_start_value -- a scope
    mismatch that shows a large, entirely fake loss."""
    from app.services import risk_manager

    # Equities holds a real position on top of shared cash: cash 1000, $2000 in
    # stock -> total 3000. This was the day's opening baseline.
    morning = datetime.now(UTC) - timedelta(hours=6)
    db_session.add(PortfolioSnapshot(timestamp=morning, total_value_usdt=3000.0, usdt_balance=1000.0, venue="alpaca"))
    db_session.commit()
    state = risk_manager.get_state(db_session)
    state.day_start_date = datetime.now(UTC).date().isoformat()
    state.day_start_value = 3000.0
    db_session.commit()

    # Extended polls again a moment ago (much more recently than equities), same
    # shared cash, holding nothing -> its OWN snapshot total is just 1000.
    # Naively using "the latest snapshot across either venue" here would read
    # 1000 and compare it to the 3000 baseline -> a fake -66% "loss".
    just_now = datetime.now(UTC)
    db_session.add(PortfolioSnapshot(timestamp=just_now, total_value_usdt=1000.0, usdt_balance=1000.0, venue="extended"))
    db_session.commit()

    body = get_status(db=db_session, settings=settings)

    # True combined account is still 1000 cash + 2000 equity + 0 extended = 3000
    # -> unchanged from the morning baseline, day_pnl_pct must be ~0, not -66%.
    assert body["day_pnl_pct"] == pytest.approx(0.0)


def test_status_includes_market_session_and_bounds(db_session, settings, monkeypatch):
    now = datetime.now(market_hours.ET)
    info = market_hours.SessionInfo(
        session=market_hours.REGULAR,
        regular_open=now,
        regular_close=now,
    )
    # /api/status czyta sesję WYŁĄCZNIE z cache (bez synchronicznego wywołania
    # brokera -- grzeje je scheduler/prime w tle), więc patchujemy cache.
    monkeypatch.setattr(routes_dashboard.market_hours, "cached_session_info", lambda: info)

    body = get_status(db=db_session, settings=settings)

    assert body["market_session"] == "regular"
    assert body["session_bounds"]["regular_open"] == now.isoformat()


def test_status_degrades_gracefully_when_session_lookup_fails(db_session, settings, monkeypatch):
    # Zimny/pusty cache sesji (broker jeszcze nie odpytany) -> pola null, a reszta
    # endpointu i tak działa. To zastąpiło dawny synchroniczny lookup w /api/status.
    monkeypatch.setattr(routes_dashboard.market_hours, "cached_session_info", lambda: None)

    body = get_status(db=db_session, settings=settings)

    assert body["market_session"] is None
    assert body["session_bounds"] is None
    # The rest of the endpoint must still work despite the cold session cache.
    assert "is_paused" in body


# (Testy /monthly usunięte wraz z martwym endpointem — zasilał tylko usuniętą
# zakładkę „Analiza". Rozbicie miesięczne wróci jako venue-aware, gdy będzie potrzebne.)


def test_widget_includes_edge_and_last_trade(db_session, settings):
    from app.api.routes_dashboard import get_widget
    from app.models import Trade, TradeMode

    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="SPY", side="BUY", quantity=1, price=100.0, usdt_value=100.0, mode=TradeMode.LIVE, venue="alpaca"))
    db_session.add(Trade(timestamp=now + timedelta(minutes=1), symbol="SPY", side="SELL", quantity=1, price=110.0, usdt_value=110.0, mode=TradeMode.LIVE, venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=1010.0, usdt_balance=1010.0, venue="alpaca"))
    db_session.commit()

    body = get_widget(db=db_session, settings=settings)
    assert "edge" in body and "last_trade" in body
    assert body["edge"]["avg_win_usd"] == 10.0
    assert body["last_trade"]["symbol"] == "SPY"
    assert body["last_trade"]["pnl_usd"] == 10.0


def test_entry_gate_reports_halt_pause_and_scanning(db_session, settings):
    """#30: endpoint mówi, co blokuje nowe wejścia — halt > pauza > reżim, a przy
    braku blokad: 'skanuje'. Dodaje własne słowa silnika z ostatniej decyzji."""
    from app.api.routes_dashboard import get_entry_gate
    from app.models import Decision, TradeAction
    from app.services import risk_manager

    s = settings.model_copy(update={"crypto_enabled": True})
    # Ostatnia decyzja krypto — jej reasoning ma wrócić jako engine_note.
    db_session.add(Decision(symbol=None, action=TradeAction.HOLD, size_pct=0.0, confidence=0.0,
                            reasoning="Cały koszyk w jednoczesnym spadku 1h — HOLD.", venue="crypto", executed=False))
    db_session.commit()

    # Bez halt/pauzy (wznowione): skanuje.
    risk_manager.get_state(db_session).crypto_paused = False
    db_session.commit()
    g = get_entry_gate(db=db_session, settings=s)
    assert g["verdict"] == "scanning" and "koszyk" in g["engine_note"]

    # Pauza ręczna -> blocked/paused.
    risk_manager.get_state(db_session).crypto_paused = True
    db_session.commit()
    g2 = get_entry_gate(db=db_session, settings=s)
    assert g2["verdict"] == "blocked" and g2["code"] == "paused"

    # Halt > pauza.
    st = risk_manager.get_state(db_session)
    st.is_halted = True
    st.halted_reason = "Kill-switch dźwigni"
    db_session.commit()
    g3 = get_entry_gate(db=db_session, settings=s)
    assert g3["code"] == "halt" and "Kill-switch" in g3["message"]


# --- Fix #1 (2026-10-27): monitor rekonsyliacji baza↔broker. Geneza: baza myślała,
# że trzyma ~$476k crypto (HYPE+XRP+PAXG), broker widział ~$110k -- rozjazd ~$366k,
# który realized+unrealized całkowicie mijały ('+$1 174' przy koncie −27%). ---

def test_reconciliation_flags_ledger_broker_divergence(db_session, settings):
    """Gdy baza myśli, że trzymamy pozycję, a broker jej nie ma (fille okazały się
    fikcją), monitor liczy rozjazd i reconciled=False -> czerwony baner."""
    from app.api.routes_dashboard import _reconciliation_view
    from app.models import Trade, TradeMode
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="HYPE/USD", side="BUY", quantity=100.0,
                         price=80.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    # Broker: 0 HYPE (pozycja „wyparowała"), sama gotówka.
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=2000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({}),
                                     prices_json=json.dumps({"HYPE/USD": 80.0}), venue="crypto"))
    db_session.commit()
    rec = _reconciliation_view(db_session, settings.model_copy(update={"crypto_enabled": True}))
    assert rec is not None
    assert rec["ledger_crypto_usd"] == pytest.approx(8000.0)
    assert rec["broker_crypto_usd"] == pytest.approx(0.0)
    assert rec["residual_usd"] == pytest.approx(8000.0)
    assert rec["reconciled"] is False
    assert rec["by_symbol"][0]["symbol"] == "HYPE/USD"


def test_reconciliation_ok_when_ledger_matches_broker(db_session, settings):
    """Gdy baza zgadza się z brokerem, reconciled=True (brak banera)."""
    from app.api.routes_dashboard import _reconciliation_view
    from app.models import Trade, TradeMode
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="BTC/USD", side="BUY", quantity=0.1,
                         price=80000.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=10000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({"BTC/USD": 0.1}),
                                     prices_json=json.dumps({"BTC/USD": 80000.0}), venue="crypto"))
    db_session.commit()
    rec = _reconciliation_view(db_session, settings.model_copy(update={"crypto_enabled": True}))
    assert rec["reconciled"] is True
    assert rec["residual_usd"] == pytest.approx(0.0)


def test_reconciliation_none_when_crypto_disabled(db_session, settings):
    from app.api.routes_dashboard import _reconciliation_view
    assert _reconciliation_view(db_session, settings.model_copy(update={"crypto_enabled": False})) is None
