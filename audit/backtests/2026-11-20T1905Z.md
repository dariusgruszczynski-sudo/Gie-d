# Backtest KRYPTO — 2026-11-20T19:05:52Z

Dane: Yahoo, 3 lat, dzienne. Benchmark: trzymanie BTC. Mechaniczny rdzeń, bez Claude.

## Rdzeń BEZ mechanizmów  vs  Z 10 mechanizmami

| Metryka | Bez (baseline) | Z mechanizmami |
|---|---|---|
| Zamknięć | 1962 | 81 |
| Trafność % | 42.6 | 17.3 |
| Expectancy (R) | -0.014 | -0.199 |
| Zwrot % | -40.41 | -22.36 |
| Benchmark BTC % | -10.49 | -10.39 |
| Alpha % | -29.92 | -11.97 |
| Max drawdown % | 51.94 | 34.65 |
| Wejść | 1917 | 121 |

## Pełny wynik — BEZ mechanizmów
```
Pobieram do 3 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 1095 świec (2023-11-22 → 2026-11-20)
  BTC/USD: 1095 świec (2023-11-22 → 2026-11-20)
  DOGE/USD: 1095 świec (2023-11-22 → 2026-11-20)
  ETH/USD: 1095 świec (2023-11-22 → 2026-11-20)
  LINK/USD: 1095 świec (2023-11-22 → 2026-11-20)
  LTC/USD: 1095 świec (2023-11-22 → 2026-11-20)
  SOL/USD: 1095 świec (2023-11-22 → 2026-11-20)
  (pobieranie zajęło 3s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 1095
  entries                     : 1917
  trades_per_month            : 53.34
  pct_time_in_market          : 75.0
  ma_trend_baseline           : {'total_return_pct': -6.46, 'max_drawdown_pct': 32.42, 'trades': 17, 'pct_time_in_market': 54.4, 'ma_period': 200}
  beats_ma_trend              : False
  closed_trades               : 1962
  wins                        : 835
  losses                      : 1127
  win_rate_pct                : 42.6
  avg_R                       : -0.014
  expectancy_R                : -0.014
  realized_pnl_usd            : -403.66
  total_return_pct            : -40.41
  benchmark_return_pct        : -10.49
  alpha_pct                   : -29.92
  max_drawdown_pct            : 51.94
  benchmark_max_drawdown_pct  : 53.39
  cagr_pct                    : -15.87
  benchmark_cagr_pct          : -3.63
  calmar                      : -0.31
  benchmark_calmar            : -0.07
  final_equity                : 595.92
  years_beating_benchmark     : 1/3

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2023       +0.0%           —         —
    2024      +11.1%      +43.8%    -32.7%
    2025      -36.1%       -6.3%    -29.8%
    2026      -16.1%      -33.5%    +17.5%  <- broni kapitału w spadku

Interpretacja:
  Trafność 42.6% vs próg ~44% -> PONIŻEJ (brak edge)
  Expectancy -0.014R/transakcję -> ujemna
  Alpha (cały okres) vs BTC/USD: -29.92% -> przegrywa z indeksem
  Lat z dodatnią alphą: 1/3
  Max obsunięcie: strategia 51.94% vs BTC/USD 53.39% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia -15.87% vs BTC/USD -3.63%
  Calmar (zwrot na jednostkę bólu): strategia -0.31 vs BTC/USD -0.07 -> indeks ma lepszy Calmar
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Pełny wynik — Z mechanizmami
```
Pobieram do 3 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 1095 świec (2023-11-22 → 2026-11-20)
  BTC/USD: 1095 świec (2023-11-22 → 2026-11-20)
  DOGE/USD: 1095 świec (2023-11-22 → 2026-11-20)
  ETH/USD: 1095 świec (2023-11-22 → 2026-11-20)
  LINK/USD: 1095 świec (2023-11-22 → 2026-11-20)
  LTC/USD: 1095 świec (2023-11-22 → 2026-11-20)
  SOL/USD: 1095 świec (2023-11-22 → 2026-11-20)
  (pobieranie zajęło 4s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 1095
  entries                     : 121
  trades_per_month            : 3.37
  pct_time_in_market          : 43.4
  ma_trend_baseline           : {'total_return_pct': -6.46, 'max_drawdown_pct': 32.42, 'trades': 17, 'pct_time_in_market': 54.4, 'ma_period': 200}
  beats_ma_trend              : False
  closed_trades               : 81
  wins                        : 14
  losses                      : 67
  win_rate_pct                : 17.3
  avg_R                       : -0.199
  expectancy_R                : -0.199
  realized_pnl_usd            : -223.61
  total_return_pct            : -22.36
  benchmark_return_pct        : -10.39
  alpha_pct                   : -11.97
  max_drawdown_pct            : 34.65
  benchmark_max_drawdown_pct  : 53.34
  cagr_pct                    : -8.1
  benchmark_cagr_pct          : -3.59
  calmar                      : -0.23
  benchmark_calmar            : -0.07
  final_equity                : 776.39
  years_beating_benchmark     : 1/3

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2023       +0.0%           —         —
    2024       +5.5%      +43.8%    -38.3%
    2025      -16.7%       -6.3%    -10.4%
    2026      -11.7%      -33.5%    +21.8%  <- broni kapitału w spadku

Interpretacja:
  Trafność 17.3% vs próg ~44% -> PONIŻEJ (brak edge)
  Expectancy -0.199R/transakcję -> ujemna
  Alpha (cały okres) vs BTC/USD: -11.97% -> przegrywa z indeksem
  Lat z dodatnią alphą: 1/3
  Max obsunięcie: strategia 34.65% vs BTC/USD 53.34% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia -8.1% vs BTC/USD -3.59%
  Calmar (zwrot na jednostkę bólu): strategia -0.23 vs BTC/USD -0.07 -> indeks ma lepszy Calmar
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Walk-forward — out-of-sample (czy przewaga trzyma się w czasie)
```
Pobieram do 3 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 1095 świec (2023-11-22 → 2026-11-20)
  BTC/USD: 1095 świec (2023-11-22 → 2026-11-20)
  DOGE/USD: 1095 świec (2023-11-22 → 2026-11-20)
  ETH/USD: 1095 świec (2023-11-22 → 2026-11-20)
  LINK/USD: 1095 świec (2023-11-22 → 2026-11-20)
  LTC/USD: 1095 świec (2023-11-22 → 2026-11-20)
  SOL/USD: 1095 świec (2023-11-22 → 2026-11-20)
  (pobieranie zajęło 4s)

=== WALK-FORWARD (yahoo, 4 okien OOS, mechaniczny rdzeń) ===
## Walk-forward (out-of-sample) — czy przewaga trzyma się w czasie

- Okien przebiegło: **4**
- Pobiło BTC: **2/4** · dodatni zwrot: **1/4**
- Alfa vs BTC: mediana **1.17%** (min -55.9%, max 20.03%)
- Najgorsze obsunięcie w oknie: **22.72%**
- Przewaga spójna w czasie: **NIE**

| # | od | do | wejścia | trafność% | zwrot% | BTC% | alfa% | maxDD% | Calmar |
|---|----|----|---------|-----------|--------|------|-------|--------|--------|
| 1 | 2024-06-19 | 2025-01-25 | 40 | 25.0 | 5.3 | 61.2 | -55.9 | 14.71 | 0.3 |
| 2 | 2025-01-26 | 2025-09-03 | 37 | 20.0 | -4.03 | 8.8 | -12.84 | 14.22 | -0.24 |
| 3 | 2025-09-04 | 2026-04-12 | 23 | 0.0 | -20.93 | -36.1 | 15.17 | 22.72 | -0.8 |
| 4 | 2026-04-13 | 2026-11-20 | 22 | 27.8 | -1.72 | -21.75 | 20.03 | 8.45 | -0.17 |

Interpretacja:
  ⚠ Przewaga NIE jest spójna między oknami — wynik może pochodzić z jednego okna. Czerwona flaga GO-LIVE.
```
