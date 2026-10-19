# Backtest KRYPTO — 2026-10-19T19:41:02Z

Dane: Yahoo, 8 lat, dzienne. Benchmark: trzymanie BTC. Mechaniczny rdzeń, bez Claude.

## Rdzeń BEZ mechanizmów  vs  Z 10 mechanizmami

| Metryka | Bez (baseline) | Z mechanizmami |
|---|---|---|
| Zamknięć | 5553 | 194 |
| Trafność % | 48.3 | 43.8 |
| Expectancy (R) | 0.046 | 0.725 |
| Zwrot % | 1456.39 | 1026.8 |
| Benchmark BTC % | 1026.09 | 1025.97 |
| Alpha % | 430.29 | 0.83 |
| Max drawdown % | 46.75 | 28.17 |
| Wejść | 5347 | 281 |

## Pełny wynik — BEZ mechanizmów
```
Pobieram do 8 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2221 świec (2020-07-13 → 2026-10-19)
  BTC/USD: 2922 świec (2018-10-20 → 2026-10-19)
  DOGE/USD: 2922 świec (2018-10-20 → 2026-10-19)
  ETH/USD: 2922 świec (2018-10-20 → 2026-10-19)
  LINK/USD: 2922 świec (2018-10-20 → 2026-10-19)
  LTC/USD: 2922 świec (2018-10-20 → 2026-10-19)
  SOL/USD: 2384 świec (2020-04-10 → 2026-10-19)
  (pobieranie zajęło 4s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 2922
  entries                     : 5347
  closed_trades               : 5553
  wins                        : 2681
  losses                      : 2872
  win_rate_pct                : 48.3
  avg_R                       : 0.046
  expectancy_R                : 0.046
  realized_pnl_usd            : 14633.71
  total_return_pct            : 1456.39
  benchmark_return_pct        : 1026.09
  alpha_pct                   : 430.29
  max_drawdown_pct            : 46.75
  benchmark_max_drawdown_pct  : 76.63
  cagr_pct                    : 40.95
  benchmark_cagr_pct          : 35.36
  calmar                      : 0.88
  benchmark_calmar            : 0.46
  final_equity                : 15563.86
  years_beating_benchmark     : 3/8

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2018       +0.0%           —         —
    2019       -2.8%       -1.1%     -1.7%
    2020     +160.1%     +303.2%   -143.1%
    2021     +379.5%      +59.7%   +319.8%
    2022      -39.3%      -64.3%    +25.0%  <- broni kapitału w spadku
    2023      +87.5%     +155.4%    -67.9%
    2024      +49.0%     +121.0%    -72.1%
    2025      -30.4%       -6.3%    -24.1%
    2026       +8.7%       -6.4%    +15.2%

Interpretacja:
  Trafność 48.3% vs próg ~44% -> POWYŻEJ (jest edge)
  Expectancy 0.046R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: +430.29% -> BIJE indeks
  Lat z dodatnią alphą: 3/8
  Max obsunięcie: strategia 46.75% vs BTC/USD 76.63% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 40.95% vs BTC/USD 35.36%
  Calmar (zwrot na jednostkę bólu): strategia 0.88 vs BTC/USD 0.46 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Pełny wynik — Z mechanizmami
```
Pobieram do 8 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2221 świec (2020-07-13 → 2026-10-19)
  BTC/USD: 2922 świec (2018-10-20 → 2026-10-19)
  DOGE/USD: 2922 świec (2018-10-20 → 2026-10-19)
  ETH/USD: 2922 świec (2018-10-20 → 2026-10-19)
  LINK/USD: 2922 świec (2018-10-20 → 2026-10-19)
  LTC/USD: 2922 świec (2018-10-20 → 2026-10-19)
  SOL/USD: 2384 świec (2020-04-10 → 2026-10-19)
  (pobieranie zajęło 4s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 2922
  entries                     : 281
  closed_trades               : 194
  wins                        : 85
  losses                      : 109
  win_rate_pct                : 43.8
  avg_R                       : 0.725
  expectancy_R                : 0.725
  realized_pnl_usd            : 10152.12
  total_return_pct            : 1026.8
  benchmark_return_pct        : 1025.97
  alpha_pct                   : 0.83
  max_drawdown_pct            : 28.17
  benchmark_max_drawdown_pct  : 76.63
  cagr_pct                    : 35.37
  benchmark_cagr_pct          : 35.36
  calmar                      : 1.26
  benchmark_calmar            : 0.46
  final_equity                : 11268.03
  years_beating_benchmark     : 4/8

=== ROK PO ROKU: strategia vs BTC/USD (analiza zachowań w różnych reżimach) ===
     rok   strategia   benchmark     alpha
    2018       +0.0%           —         —
    2019      +10.3%       -1.1%    +11.4%
    2020     +171.7%     +303.2%   -131.4%
    2021     +171.5%      +59.7%   +111.9%
    2022      -15.3%      -64.3%    +48.9%  <- broni kapitału w spadku
    2023      +52.7%     +155.4%   -102.7%
    2024      +21.8%     +121.0%    -99.2%
    2025       -8.8%       -6.3%     -2.5%
    2026       -3.6%       -6.4%     +2.9%

Interpretacja:
  Trafność 43.8% vs próg ~44% -> PONIŻEJ (brak edge)
  Expectancy 0.725R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: +0.83% -> BIJE indeks
  Lat z dodatnią alphą: 4/8
  Max obsunięcie: strategia 28.17% vs BTC/USD 76.63% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 35.37% vs BTC/USD 35.36%
  Calmar (zwrot na jednostkę bólu): strategia 1.26 vs BTC/USD 0.46 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Sweep — frontiera ryzyko/trade × równoczesne pozycje (z mechanizmami)
```
Pobieram do 8 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2221 świec (2020-07-13 → 2026-10-19)
  BTC/USD: 2922 świec (2018-10-20 → 2026-10-19)
  DOGE/USD: 2922 świec (2018-10-20 → 2026-10-19)
  ETH/USD: 2922 świec (2018-10-20 → 2026-10-19)
  LINK/USD: 2922 świec (2018-10-20 → 2026-10-19)
  LTC/USD: 2922 świec (2018-10-20 → 2026-10-19)
  SOL/USD: 2384 świec (2020-04-10 → 2026-10-19)
  (pobieranie zajęło 4s)

=== PRZEMIATANIE EKSPOZYCJI (ryzyko/transakcję × liczba pozycji), 20 lat ===
  Strategia jest niedoinwestowana — ten test pokazuje granicę zysk↔obsunięcie.
   ryzyko%  pozycje     zwrot%    CAGR%   maxDD%   Calmar  trafność%    alpha%
  ----------------------------------------------------------------------------
       0.5        4     +183.6    +13.9    +12.2     +1.1      +41.6    -842.1
       0.5        6     +225.9    +15.9    +22.3     +0.7      +33.3    -799.8
       0.5        8     +243.6    +16.7    +24.8     +0.7      +32.3    -782.1
       1.0        4     +379.7    +21.7    +22.1     +1.0      +41.9    -646.0
       1.0        6     +328.9    +20.0    +28.5     +0.7      +34.1    -696.8
       1.0        8     +250.1    +17.0    +29.7     +0.6      +32.5    -775.6
       1.5        4     +382.0    +21.7    +27.9     +0.8      +41.7    -643.7
       1.5        6     +488.9    +24.8    +30.1     +0.8      +39.3    -536.8
       1.5        8     +488.9    +24.8    +30.1     +0.8      +39.3    -536.8
       2.0        4     +565.9    +26.8    +29.1     +0.9      +40.7    -459.8
       2.0        6     +483.2    +24.7    +30.4     +0.8      +39.2    -542.5
       2.0        8     +483.2    +24.7    +30.4     +0.8      +39.2    -542.5
       2.5        4     +483.2    +24.7    +31.1     +0.8      +42.1    -542.5
       2.5        6     +453.3    +23.9    +31.1     +0.8      +39.4    -572.4
       2.5        8     +453.3    +23.9    +31.1     +0.8      +39.4    -572.4
       3.0        4    +1061.9    +35.9    +28.3     +1.3      +46.1     +36.2
       3.0        6    +1026.7    +35.4    +28.2     +1.3      +43.8      +1.0
       3.0        8    +1026.7    +35.4    +28.2     +1.3      +43.8      +1.0

  Benchmark (BTC/USD): zwrot 1025.69%, CAGR 35.35%, maxDD 76.63%, Calmar 0.46

Rekomendacja (na danych, nie na wyczucie):
  • Najlepszy Calmar (zysk/ból): ryzyko 3.0% × 4 pozycji → Calmar 1.27, zwrot 1061.92%, maxDD 28.28%
  • Najwyższy zwrot: ryzyko 3.0% × 4 pozycji → zwrot 1061.92%, maxDD 28.28%, Calmar 1.27
  Wybierz swój punkt: wyższy Calmar = spokojniejsza jazda, wyższy zwrot = większe obsunięcia.
  Ustaw wybrane na serwerze przez RISK_PER_TRADE_PCT i MAX_CONCURRENT_POSITIONS w .env, potem restart.
```
