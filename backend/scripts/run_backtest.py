#!/usr/bin/env python3
"""Backtest the mechanical strategy on real historical bars.

Fetches hourly bars for the trading whitelist (+ benchmark) from Alpaca and
replays them through the same entry filter + exit geometry the live bot uses
(no Claude). Prints win rate, expectancy (R), return, alpha vs buy-and-hold and
max drawdown -- so you can see whether the mechanical core has an edge and tune
it on data, not hope.

Usage (on the server or anywhere with ALPACA_* in .env):
    cd ~/gie-d && python backend/scripts/run_backtest.py --bars 1000
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.services import backtest  # noqa: E402
from app.services.alpaca_client import AlpacaClient  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest the mechanical GielDarek strategy on Alpaca bars.")
    parser.add_argument("--bars", type=int, default=1000, help="hourly bars per symbol to fetch (default 1000)")
    parser.add_argument("--cash", type=float, default=1000.0, help="starting cash (default 1000)")
    args = parser.parse_args()

    settings = get_settings()
    broker = AlpacaClient(settings)
    symbols = sorted(set(settings.whitelist_symbols) | {settings.benchmark_symbol})

    closes: dict[str, list[float]] = {}
    for sym in symbols:
        try:
            rows = broker.get_klines(sym, "1h", args.bars)
            series = [float(r[4]) for r in rows if r]
            if len(series) > backtest.WARMUP:
                closes[sym] = series
                print(f"  {sym}: {len(series)} bars")
            else:
                print(f"  {sym}: SKIP ({len(series)} bars < warmup {backtest.WARMUP})")
        except Exception as exc:  # noqa: BLE001
            print(f"  {sym}: FAILED ({type(exc).__name__}: {exc})")

    if not closes:
        print("Brak danych do backtestu.")
        return

    report = backtest.run_backtest(closes, settings, benchmark_symbol=settings.benchmark_symbol, starting_cash=args.cash)

    print("\n=== WYNIK BACKTESTU (mechaniczny rdzeń, bez Claude) ===")
    for k, v in report.items():
        print(f"  {k:24}: {v}")
    wr = report.get("win_rate_pct")
    exp = report.get("expectancy_R")
    print("\nInterpretacja:")
    if wr is not None:
        print(f"  Trafność {wr}% vs próg rentowności ~44% -> "
              f"{'POWYŻEJ progu (jest edge)' if wr >= 44 else 'PONIŻEJ progu (brak edge)'}")
    if exp is not None:
        print(f"  Expectancy {exp}R/transakcję -> {'dodatnia' if exp > 0 else 'ujemna'}")
    alpha = report.get("alpha_pct")
    if alpha is not None:
        print(f"  Alpha vs trzymanie {settings.benchmark_symbol}: {alpha:+}% -> "
              f"{'bije indeks' if alpha > 0 else 'przegrywa z indeksem'}")


if __name__ == "__main__":
    main()
