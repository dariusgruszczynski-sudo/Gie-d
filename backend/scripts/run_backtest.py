#!/usr/bin/env python3
"""Backtest the mechanical strategy on real historical bars.

Replays historical bars through the same entry filter + exit geometry the
live bot uses (no Claude -- that's non-deterministic and paid). Prints win
rate, expectancy (R), return, alpha vs buy-and-hold, max drawdown, AND a
year-by-year breakdown -- the single aggregate number can hide a strategy
that lags in a bull run but actually PROTECTS capital in a crash year
(2008/2020/2022), which is arguably the whole point of mechanical stops.

Two data sources:
  --source alpaca (default when --years is 0): free Alpaca/IEX feed, only
    reaches back a few years even for daily bars.
  --source yahoo (default whenever --years > 0): free, keyless, goes back
    decades for most tickers -- use this for real regime testing.

Usage (inside the container -- files live in /app, not /app/backend):
    # Quick check on recent Alpaca history:
    docker compose exec -T app python scripts/run_backtest.py --bars 1500

    # Full 20-year regime test (2008 GFC, 2020 COVID crash, 2022 bear, ...):
    docker compose exec -T app python scripts/run_backtest.py --years 20

    # Compare with the entry filter off:
    docker compose exec -T -e ENTRY_FILTER_ENABLED=false app python scripts/run_backtest.py --years 20
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.services import backtest, historical_data  # noqa: E402
from app.services.alpaca_client import AlpacaClient  # noqa: E402


def _fmt_date(ms: float) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def _fetch_alpaca(symbols: list[str], timeframe: str, bars: int) -> dict[str, list[list]]:
    settings = get_settings()
    broker = AlpacaClient(settings)
    print(f"Pobieram {bars} świec {timeframe} dla {len(symbols)} symboli (Alpaca)...")
    out: dict[str, list[list]] = {}
    for sym in symbols:
        try:
            rows = broker.get_klines(sym, timeframe, bars)
            if len(rows) > backtest.WARMUP:
                out[sym] = rows
                print(f"  {sym}: {len(rows)} świec")
            else:
                print(f"  {sym}: POMIJAM ({len(rows)} < warmup {backtest.WARMUP})")
        except Exception as exc:  # noqa: BLE001
            print(f"  {sym}: BŁĄD ({type(exc).__name__}: {exc})")
    return out


def _fetch_yahoo(symbols: list[str], years: int) -> dict[str, list[list]]:
    print(f"Pobieram do {years} lat świec dziennych dla {len(symbols)} symboli (Yahoo)...")
    out: dict[str, list[list]] = {}
    t0 = time.time()
    for i, sym in enumerate(symbols):
        if i > 0:
            time.sleep(historical_data.BATCH_DELAY_SECONDS)
        rows = historical_data.get_daily_history(sym, years=years)
        if len(rows) > backtest.WARMUP:
            out[sym] = rows
            print(f"  {sym}: {len(rows)} świec ({_fmt_date(rows[0][0])} → {_fmt_date(rows[-1][0])})")
        else:
            print(f"  {sym}: POMIJAM ({len(rows)} świec < warmup {backtest.WARMUP})")
    print(f"  (pobieranie zajęło {time.time() - t0:.0f}s)")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest the mechanical GielDarek strategy on historical bars.")
    parser.add_argument("--source", choices=["alpaca", "yahoo"], default=None,
                         help="Źródło danych. Domyślnie: yahoo gdy --years>0, inaczej alpaca.")
    parser.add_argument("--years", type=int, default=0,
                         help="Lata historii dziennej z Yahoo (np. 20 = pełny test reżimów 2008/2020/2022). 0 = użyj --bars z Alpaca.")
    parser.add_argument("--bars", type=int, default=1500, help="Alpaca: liczba świec (gdy --source alpaca / --years=0)")
    parser.add_argument("--timeframe", default="1d", help="Alpaca: 1d (domyślnie) lub 1h")
    parser.add_argument("--cash", type=float, default=1000.0, help="startowy kapitał (domyślnie 1000)")
    args = parser.parse_args()

    settings = get_settings()
    symbols = sorted(set(settings.whitelist_symbols) | {settings.benchmark_symbol})
    source = args.source or ("yahoo" if args.years > 0 else "alpaca")

    if source == "yahoo":
        bars_by_symbol = _fetch_yahoo(symbols, args.years or 20)
    else:
        bars_by_symbol = _fetch_alpaca(symbols, args.timeframe, args.bars)

    if not bars_by_symbol:
        print("\nBrak wystarczających danych do backtestu. Spróbuj --source yahoo --years 20.")
        return

    report = backtest.run_backtest(
        bars_by_symbol, settings, benchmark_symbol=settings.benchmark_symbol, starting_cash=args.cash
    )

    print(f"\n=== WYNIK BACKTESTU ({source}, mechaniczny rdzeń, bez Claude) ===")
    for k, v in report.items():
        if k == "yearly_breakdown":
            continue
        print(f"  {k:28}: {v}")

    yearly = report.get("yearly_breakdown") or []
    if yearly:
        print(f"\n=== ROK PO ROKU: strategia vs {settings.benchmark_symbol} (analiza zachowań w różnych reżimach) ===")
        print(f"  {'rok':>6} {'strategia':>11} {'benchmark':>11} {'alpha':>9}")
        for row in yearly:
            sr = f"{row['strategy_return_pct']:+.1f}%" if row["strategy_return_pct"] is not None else "—"
            br = f"{row['benchmark_return_pct']:+.1f}%" if row["benchmark_return_pct"] is not None else "—"
            ar = f"{row['alpha_pct']:+.1f}%" if row["alpha_pct"] is not None else "—"
            flag = ""
            if row["alpha_pct"] is not None and row["benchmark_return_pct"] is not None:
                if row["benchmark_return_pct"] < -10 and row["alpha_pct"] > 5:
                    flag = "  <- broni kapitału w spadku"
                elif row["benchmark_return_pct"] < -10 and row["alpha_pct"] < 0:
                    flag = "  <- traci WIĘCEJ niż indeks w spadku"
            print(f"  {row['year']:>6} {sr:>11} {br:>11} {ar:>9}{flag}")

    print("\nInterpretacja:")
    wr, exp, alpha = report.get("win_rate_pct"), report.get("expectancy_R"), report.get("alpha_pct")
    if report.get("closed_trades", 0) < 10:
        print("  ⚠ Za mało zamkniętych transakcji na wiarygodny wynik — zwiększ --bars/--years.")
    if wr is not None:
        print(f"  Trafność {wr}% vs próg ~44% -> {'POWYŻEJ (jest edge)' if wr >= 44 else 'PONIŻEJ (brak edge)'}")
    if exp is not None:
        print(f"  Expectancy {exp}R/transakcję -> {'dodatnia' if exp > 0 else 'ujemna'}")
    if alpha is not None:
        print(f"  Alpha (cały okres) vs {settings.benchmark_symbol}: {alpha:+}% -> "
              f"{'BIJE indeks' if alpha > 0 else 'przegrywa z indeksem'}")
    ybb = report.get("years_beating_benchmark")
    if ybb:
        print(f"  Lat z dodatnią alphą: {ybb}")
    bench_dd = report.get("benchmark_max_drawdown_pct")
    strat_dd = report.get("max_drawdown_pct")
    if bench_dd is not None and strat_dd is not None:
        print(f"  Max obsunięcie: strategia {strat_dd}% vs {settings.benchmark_symbol} {bench_dd}% -> "
              f"{'strategia broni kapitału lepiej' if strat_dd < bench_dd else 'strategia obsuwa się MOCNIEJ niż indeks'}")


if __name__ == "__main__":
    main()
