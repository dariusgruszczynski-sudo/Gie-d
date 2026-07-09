#!/usr/bin/env python3
"""Backtest the mechanical strategy on real historical bars.

Fetches bars for the trading whitelist (+ benchmark) from Alpaca and replays
them through the same entry filter + exit geometry the live bot uses (no Claude).
Prints win rate, expectancy (R), return, alpha vs buy-and-hold and max drawdown.

Defaults to DAILY bars: the free Alpaca feed's hourly history is too short for a
200-bar SMA, so daily gives a far longer, meaningful sample (it tests the same
LOGIC/edge, not the exact live 1h cadence).

Usage (inside the container -- files live in /app, not /app/backend):
    docker compose exec -T app python scripts/run_backtest.py --bars 1000
    docker compose exec -T app python scripts/run_backtest.py --timeframe 1h --bars 1000
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
    parser.add_argument("--bars", type=int, default=1000, help="bars per symbol to fetch (default 1000)")
    parser.add_argument("--timeframe", default="1d", help="bar timeframe: 1d (default) or 1h")
    parser.add_argument("--cash", type=float, default=1000.0, help="starting cash (default 1000)")
    args = parser.parse_args()

    settings = get_settings()
    broker = AlpacaClient(settings)
    symbols = sorted(set(settings.whitelist_symbols) | {settings.benchmark_symbol})

    print(f"Pobieram {args.bars} świec {args.timeframe} dla {len(symbols)} symboli...")
    bars_by_symbol: dict[str, list[list]] = {}
    for sym in symbols:
        try:
            rows = broker.get_klines(sym, args.timeframe, args.bars)
            if len(rows) > backtest.WARMUP:
                bars_by_symbol[sym] = rows
                print(f"  {sym}: {len(rows)} świec")
            else:
                print(f"  {sym}: POMIJAM ({len(rows)} < warmup {backtest.WARMUP})")
        except Exception as exc:  # noqa: BLE001
            print(f"  {sym}: BŁĄD ({type(exc).__name__}: {exc})")

    if not bars_by_symbol:
        print("\nBrak wystarczających danych do backtestu. Spróbuj --timeframe 1d --bars 1500.")
        return

    report = backtest.run_backtest(
        bars_by_symbol, settings, benchmark_symbol=settings.benchmark_symbol, starting_cash=args.cash
    )

    print(f"\n=== WYNIK BACKTESTU ({args.timeframe}, mechaniczny rdzeń, bez Claude) ===")
    for k, v in report.items():
        print(f"  {k:24}: {v}")

    print("\nInterpretacja:")
    wr, exp, alpha = report.get("win_rate_pct"), report.get("expectancy_R"), report.get("alpha_pct")
    if report.get("closed_trades", 0) < 10:
        print("  ⚠ Za mało zamkniętych transakcji na wiarygodny wynik — zwiększ --bars.")
    if wr is not None:
        print(f"  Trafność {wr}% vs próg ~44% -> {'POWYŻEJ (jest edge)' if wr >= 44 else 'PONIŻEJ (brak edge)'}")
    if exp is not None:
        print(f"  Expectancy {exp}R/transakcję -> {'dodatnia' if exp > 0 else 'ujemna'}")
    if alpha is not None:
        print(f"  Alpha vs {settings.benchmark_symbol}: {alpha:+}% -> {'BIJE indeks' if alpha > 0 else 'przegrywa z indeksem'}")


if __name__ == "__main__":
    main()
