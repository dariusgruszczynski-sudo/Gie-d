"""Wpłata (top-up) nie może udawać zysku ani przewagi nad SPY.

record_deposit() dolicza wpłatę do sumy wpłat i re-kotwiczy benchmark, szczyt
obsunięcia oraz okna dnia/tygodnia o kwotę wpłaty, żeby alfa i drawdown zostały
ciągłe (to naprawia zawyżoną alfę +314% z zawieszonego baseline'u)."""

import json

from app.models import PortfolioSnapshot
from app.services import risk_manager


def _snap(db, settings, spy_price):
    db.add(
        PortfolioSnapshot(
            venue="alpaca",
            total_value_usdt=1000.0,
            usdt_balance=500.0,
            balances_json="{}",
            prices_json=json.dumps({settings.benchmark_symbol: spy_price}),
        )
    )
    db.commit()


def test_deposit_tracked_and_baselines_shift(db_session, settings):
    state = risk_manager.get_state(db_session)
    state.day_start_value = 800.0
    state.week_start_value = 750.0
    state.peak_account_value = 1000.0
    db_session.commit()

    res = risk_manager.record_deposit(db_session, settings, 120.0)

    assert res["deposits_usd_lifetime"] == 120.0
    state = risk_manager.get_state(db_session)
    assert state.deposits_usd_lifetime == 120.0
    # Wpłata to nie wynik handlu -> okna i szczyt przesunięte o dokładnie 120.
    assert state.day_start_value == 920.0
    assert state.week_start_value == 870.0
    assert state.peak_account_value == 1120.0


def test_deposit_keeps_alpha_continuous(db_session, settings):
    """Konto rośnie o wpłatę; benchmark też ma dostać tę samą wpłatę, więc alfa
    (konto - benchmark) nie zmienia się w momencie wpłaty."""
    spy = 750.0
    _snap(db_session, settings, spy)
    state = risk_manager.get_state(db_session)
    state.benchmark_start_price = spy
    state.benchmark_start_value = 600.0  # benchmark_value teraz = 600 (bo cena=start)
    db_session.commit()

    def bench_value(s):
        return s.benchmark_start_value * (spy / s.benchmark_start_price)

    before = bench_value(risk_manager.get_state(db_session))
    risk_manager.record_deposit(db_session, settings, 120.0)
    after = bench_value(risk_manager.get_state(db_session))

    # Benchmark „dostał" wpłatę 120 po dzisiejszej cenie -> wartość +120.
    assert round(after - before, 6) == 120.0


def test_deposit_without_benchmark_is_safe(db_session, settings):
    """Brak baseline'u benchmarku (start_price=0) nie może wywalić — po prostu
    liczymy sumę wpłat i przesuwamy okna."""
    state = risk_manager.get_state(db_session)
    state.benchmark_start_price = 0.0
    state.benchmark_start_value = 0.0
    db_session.commit()
    res = risk_manager.record_deposit(db_session, settings, 50.0)
    assert res["deposits_usd_lifetime"] == 50.0


def test_withdrawal_is_symmetric(db_session, settings):
    state = risk_manager.get_state(db_session)
    state.peak_account_value = 1000.0
    db_session.commit()
    risk_manager.record_deposit(db_session, settings, 120.0)
    risk_manager.record_deposit(db_session, settings, -20.0)
    state = risk_manager.get_state(db_session)
    assert state.deposits_usd_lifetime == 100.0
