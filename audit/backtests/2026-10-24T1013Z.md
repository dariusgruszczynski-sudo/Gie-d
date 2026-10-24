# Backtest KRYPTO — 2026-10-24T10:13:01Z

Dane: Yahoo, 10 lat, dzienne. Benchmark: trzymanie BTC. Mechaniczny rdzeń, bez Claude.

## Rdzeń BEZ mechanizmów  vs  Z 10 mechanizmami

| Metryka | Bez (baseline) | Z mechanizmami |
|---|---|---|
| Zamknięć | 6377 | 244 |
| Trafność % | 48.9 | 46.7 |
| Expectancy (R) | 0.049 | 0.745 |
| Zwrot % | 4025.28 | 2486.41 |
| Benchmark BTC % | 3603.87 | 3603.49 |
| Alpha % | 421.4 | -1117.08 |
| Max drawdown % | 46.75 | 28.57 |
| Wejść | 6064 | 334 |

## Pełny wynik — BEZ mechanizmów
```
Pobieram do 10 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2226 świec (2020-07-13 → 2026-10-24)
  BTC/USD: 3653 świec (2016-10-24 → 2026-10-24)
  DOGE/USD: 3272 świec (2017-11-09 → 2026-10-24)
  ETH/USD: 3272 świec (2017-11-09 → 2026-10-24)
  LINK/USD: 3272 świec (2017-11-09 → 2026-10-24)
  LTC/USD: 3653 świec (2016-10-24 → 2026-10-24)
  SOL/USD: 2389 świec (2020-04-10 → 2026-10-24)
  (pobieranie zajęło 3s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 3653
  entries                     : 6064
  closed_trades               : 6377
  wins                        : 3117
  losses                      : 3260
  win_rate_pct                : 48.9
  avg_R                       : 0.049
  expectancy_R                : 0.049
  realized_pnl_usd            : 40252.76
  total_return_pct            : 4025.28
  benchmark_return_pct        : 3603.87
  alpha_pct                   : 421.4
  max_drawdown_pct            : 46.75
  benchmark_max_drawdown_pct  : 83.4
  cagr_pct                    : 45.07
  benchmark_cagr_pct          : 43.51
  calmar                      : 0.96
  benchmark_calmar            : 0.52
  final_equity                : 41252.76
  years_beating_benchmark     : 4/10

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2016       +0.0%           —         —
    2017     +113.0%     +551.4%   -438.4%
    2018      -21.8%      -73.6%    +51.8%  <- broni kapitału w spadku
    2019      +57.9%      +92.2%    -34.3%
    2020     +159.3%     +303.2%   -143.8%
    2021     +379.5%      +59.7%   +319.8%
    2022      -39.3%      -64.3%    +25.0%  <- broni kapitału w spadku
    2023      +86.3%     +155.4%    -69.1%
    2024      +49.5%     +121.0%    -71.6%
    2025      -30.4%       -6.3%    -24.1%
    2026       +7.1%       -8.0%    +15.1%

Interpretacja:
  Trafność 48.9% vs próg ~44% -> POWYŻEJ (jest edge)
  Expectancy 0.049R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: +421.4% -> BIJE indeks
  Lat z dodatnią alphą: 4/10
  Max obsunięcie: strategia 46.75% vs BTC/USD 83.4% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 45.07% vs BTC/USD 43.51%
  Calmar (zwrot na jednostkę bólu): strategia 0.96 vs BTC/USD 0.52 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Pełny wynik — Z mechanizmami
```
Pobieram do 10 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2226 świec (2020-07-13 → 2026-10-24)
  BTC/USD: 3653 świec (2016-10-24 → 2026-10-24)
  DOGE/USD: 3272 świec (2017-11-09 → 2026-10-24)
  ETH/USD: 3272 świec (2017-11-09 → 2026-10-24)
  LINK/USD: 3272 świec (2017-11-09 → 2026-10-24)
  LTC/USD: 3653 świec (2016-10-24 → 2026-10-24)
  SOL/USD: 2389 świec (2020-04-10 → 2026-10-24)
  (pobieranie zajęło 3s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 3653
  entries                     : 334
  closed_trades               : 244
  wins                        : 114
  losses                      : 130
  win_rate_pct                : 46.7
  avg_R                       : 0.745
  expectancy_R                : 0.745
  realized_pnl_usd            : 24864.1
  total_return_pct            : 2486.41
  benchmark_return_pct        : 3603.49
  alpha_pct                   : -1117.08
  max_drawdown_pct            : 28.57
  benchmark_max_drawdown_pct  : 83.4
  cagr_pct                    : 38.45
  benchmark_cagr_pct          : 43.51
  calmar                      : 1.35
  benchmark_calmar            : 0.52
  final_equity                : 25864.1
  years_beating_benchmark     : 4/10

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2016       +0.0%           —         —
    2017      +73.6%     +551.4%   -477.7%
    2018      -11.4%      -73.6%    +62.1%  <- broni kapitału w spadku
    2019      +59.6%      +92.2%    -32.6%
    2020     +171.7%     +303.2%   -131.4%
    2021     +171.5%      +59.7%   +111.9%
    2022      -15.3%      -64.3%    +48.9%  <- broni kapitału w spadku
    2023      +52.7%     +155.4%   -102.7%
    2024      +27.0%     +121.0%    -94.0%
    2025       -8.8%       -6.3%     -2.5%
    2026       -4.6%       -8.0%     +3.4%

Interpretacja:
  Trafność 46.7% vs próg ~44% -> POWYŻEJ (jest edge)
  Expectancy 0.745R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: -1117.08% -> przegrywa z indeksem
  Lat z dodatnią alphą: 4/10
  Max obsunięcie: strategia 28.57% vs BTC/USD 83.4% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 38.45% vs BTC/USD 43.51%
  Calmar (zwrot na jednostkę bólu): strategia 1.35 vs BTC/USD 0.52 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Tor 2 — altseason-gate vs bez (czy edge jest tylko w altseasonie)
```
Pobieram do 10 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2226 świec (2020-07-13 → 2026-10-24)
  BTC/USD: 3653 świec (2016-10-24 → 2026-10-24)
  DOGE/USD: 3272 świec (2017-11-09 → 2026-10-24)
  ETH/USD: 3272 świec (2017-11-09 → 2026-10-24)
  LINK/USD: 3272 świec (2017-11-09 → 2026-10-24)
  LTC/USD: 3653 świec (2016-10-24 → 2026-10-24)
  SOL/USD: 2389 świec (2020-04-10 → 2026-10-24)
  (pobieranie zajęło 3s)

=== TOR 2: ALTSEASON-GATE vs BEZ (walk-forward 4 okien, benchmark=trzymanie BTC/USD) ===

## WARIANT A — obecne mechanizmy (BEZ altseason-gate)
## Walk-forward (out-of-sample) — czy przewaga trzyma się w czasie

- Okien przebiegło: **4**
- Pobiło BTC: **1/4** · dodatni zwrot: **4/4**
- Alfa vs BTC: mediana **-20.86%** (min -133.98%, max 225.81%)
- Najgorsze obsunięcie w oknie: **28.57%**
- Przewaga spójna w czasie: **NIE**

| # | od | do | wejścia | trafność% | zwrot% | BTC% | alfa% | maxDD% | Calmar |
|---|----|----|---------|-----------|--------|------|-------|--------|--------|
| 1 | 2017-05-22 | 2019-09-28 | 61 | 55.1 | 145.42 | 279.4 | -133.98 | 28.57 | 1.26 |
| 2 | 2019-09-29 | 2022-02-04 | 136 | 53.9 | 637.91 | 412.09 | 225.81 | 18.42 | 5.32 |
| 3 | 2022-02-05 | 2024-06-13 | 76 | 47.4 | 37.29 | 61.09 | -23.79 | 19.22 | 0.6 |
| 4 | 2024-06-14 | 2026-10-24 | 61 | 24.5 | 4.03 | 21.95 | -17.92 | 26.31 | 0.05 |

## WARIANT B — Z altseason-gate (alty tylko gdy koszyk bije BTC)
## Walk-forward (out-of-sample) — czy przewaga trzyma się w czasie

- Okien przebiegło: **4**
- Pobiło BTC: **1/4** · dodatni zwrot: **2/4**
- Alfa vs BTC: mediana **-57.89%** (min -178.42%, max 16.94%)
- Najgorsze obsunięcie w oknie: **28.95%**
- Przewaga spójna w czasie: **NIE**

| # | od | do | wejścia | trafność% | zwrot% | BTC% | alfa% | maxDD% | Calmar |
|---|----|----|---------|-----------|--------|------|-------|--------|--------|
| 1 | 2017-05-22 | 2019-09-28 | 56 | 52.4 | 100.98 | 279.4 | -178.42 | 28.95 | 0.93 |
| 2 | 2019-09-29 | 2022-02-04 | 113 | 56.1 | 429.03 | 412.09 | 16.94 | 26.41 | 2.9 |
| 3 | 2022-02-05 | 2024-06-13 | 53 | 27.5 | -14.44 | 61.09 | -75.53 | 20.71 | -0.25 |
| 4 | 2024-06-14 | 2026-10-24 | 49 | 23.3 | -18.31 | 21.95 | -40.26 | 23.99 | -0.28 |

## WERDYKT (bez lukru)
  Pobiło BTC: BEZ 1/4 · Z 1/4
  Mediana alfy: BEZ -20.86% · Z -57.89%
  Najgorsze obsunięcie: BEZ 28.57% · Z 28.95%
  ⚠ Altseason-gate NIE pomaga (nie podnosi mediany alfy). Hipoteza 'edge tylko w altseasonie' niepotwierdzona — nie wpinać.
```
