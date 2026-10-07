# Backtest KRYPTO — 2026-10-07T16:10:12Z

Dane: Yahoo, 8 lat, dzienne. Benchmark: trzymanie BTC. Mechaniczny rdzeń, bez Claude.

## Rdzeń BEZ mechanizmów  vs  Z 10 mechanizmami

| Metryka | Bez (baseline) | Z mechanizmami |
|---|---|---|
| Zamknięć | 6929 | 212 |
| Trafność % | 49.2 | 42.5 |
| Expectancy (R) | 0.035 | 0.825 |
| Zwrot % | 1458.74 | 869.24 |
| Benchmark BTC % | 1354.3 | 1353.85 |
| Alpha % | 104.44 | -484.61 |
| Max drawdown % | 46.26 | 27.86 |
| Wejść | 6753 | 331 |

## Pełny wynik — BEZ mechanizmów
```
Pobieram do 8 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2209 świec (2020-07-13 → 2026-10-07)
  BTC/USD: 2922 świec (2018-10-08 → 2026-10-07)
  DOGE/USD: 2922 świec (2018-10-08 → 2026-10-07)
  ETH/USD: 2922 świec (2018-10-08 → 2026-10-07)
  LINK/USD: 2922 świec (2018-10-08 → 2026-10-07)
  LTC/USD: 2922 świec (2018-10-08 → 2026-10-07)
  SOL/USD: 2372 świec (2020-04-10 → 2026-10-07)
  (pobieranie zajęło 4s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 2922
  entries                     : 6753
  closed_trades               : 6929
  wins                        : 3407
  losses                      : 3522
  win_rate_pct                : 49.2
  avg_R                       : 0.035
  expectancy_R                : 0.035
  realized_pnl_usd            : 14228.26
  total_return_pct            : 1458.74
  benchmark_return_pct        : 1354.3
  alpha_pct                   : 104.44
  max_drawdown_pct            : 46.26
  benchmark_max_drawdown_pct  : 76.63
  cagr_pct                    : 40.98
  benchmark_cagr_pct          : 39.76
  calmar                      : 0.89
  benchmark_calmar            : 0.52
  final_equity                : 15587.43
  years_beating_benchmark     : 3/8

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2018       +0.0%           —         —
    2019       +5.6%      +25.2%    -19.6%
    2020     +183.3%     +303.2%   -119.8%
    2021     +206.4%      +59.7%   +146.7%
    2022      -30.9%      -64.3%    +33.3%  <- broni kapitału w spadku
    2023      +76.9%     +155.4%    -78.5%
    2024      +58.5%     +121.0%    -62.5%
    2025      -11.6%       -6.3%     -5.3%
    2026       -0.6%       -4.5%     +3.9%

Interpretacja:
  Trafność 49.2% vs próg ~44% -> POWYŻEJ (jest edge)
  Expectancy 0.035R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: +104.44% -> BIJE indeks
  Lat z dodatnią alphą: 3/8
  Max obsunięcie: strategia 46.26% vs BTC/USD 76.63% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 40.98% vs BTC/USD 39.76%
  Calmar (zwrot na jednostkę bólu): strategia 0.89 vs BTC/USD 0.52 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Pełny wynik — Z mechanizmami
```
Pobieram do 8 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2209 świec (2020-07-13 → 2026-10-07)
  BTC/USD: 2922 świec (2018-10-08 → 2026-10-07)
  DOGE/USD: 2922 świec (2018-10-08 → 2026-10-07)
  ETH/USD: 2922 świec (2018-10-08 → 2026-10-07)
  LINK/USD: 2922 świec (2018-10-08 → 2026-10-07)
  LTC/USD: 2922 świec (2018-10-08 → 2026-10-07)
  SOL/USD: 2372 świec (2020-04-10 → 2026-10-07)
  (pobieranie zajęło 3s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 2922
  entries                     : 331
  closed_trades               : 212
  wins                        : 90
  losses                      : 122
  win_rate_pct                : 42.5
  avg_R                       : 0.825
  expectancy_R                : 0.825
  realized_pnl_usd            : 8180.02
  total_return_pct            : 869.24
  benchmark_return_pct        : 1353.85
  alpha_pct                   : -484.61
  max_drawdown_pct            : 27.86
  benchmark_max_drawdown_pct  : 76.63
  cagr_pct                    : 32.85
  benchmark_cagr_pct          : 39.75
  calmar                      : 1.18
  benchmark_calmar            : 0.52
  final_equity                : 9692.39
  years_beating_benchmark     : 3/8

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2018       +0.0%           —         —
    2019      +20.7%      +25.2%     -4.5%
    2020     +122.2%     +303.2%   -181.0%
    2021     +140.9%      +59.7%    +81.2%
    2022       +0.0%      -64.3%    +64.3%  <- broni kapitału w spadku
    2023      +46.8%     +155.4%   -108.6%
    2024      +12.7%     +121.0%   -108.3%
    2025      -14.3%       -6.3%     -8.0%
    2026       +5.8%       -4.5%    +10.3%

Interpretacja:
  Trafność 42.5% vs próg ~44% -> PONIŻEJ (brak edge)
  Expectancy 0.825R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: -484.61% -> przegrywa z indeksem
  Lat z dodatnią alphą: 3/8
  Max obsunięcie: strategia 27.86% vs BTC/USD 76.63% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 32.85% vs BTC/USD 39.75%
  Calmar (zwrot na jednostkę bólu): strategia 1.18 vs BTC/USD 0.52 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
