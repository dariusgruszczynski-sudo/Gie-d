# Backtest KRYPTO — 2026-10-23T20:42:12Z

Dane: Yahoo, 10 lat, dzienne. Benchmark: trzymanie BTC. Mechaniczny rdzeń, bez Claude.

## Rdzeń BEZ mechanizmów  vs  Z 10 mechanizmami

| Metryka | Bez (baseline) | Z mechanizmami |
|---|---|---|
| Zamknięć | 6374 | 244 |
| Trafność % | 48.9 | 46.7 |
| Expectancy (R) | 0.049 | 0.745 |
| Zwrot % | 4065.68 | 2486.41 |
| Benchmark BTC % | 3640.07 | 3640.42 |
| Alpha % | 425.61 | -1154.01 |
| Max drawdown % | 46.75 | 28.57 |
| Wejść | 6060 | 334 |

## Pełny wynik — BEZ mechanizmów
```
Pobieram do 10 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2225 świec (2020-07-13 → 2026-10-23)
  BTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  DOGE/USD: 3271 świec (2017-11-09 → 2026-10-23)
  ETH/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LINK/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  SOL/USD: 2388 świec (2020-04-10 → 2026-10-23)
  (pobieranie zajęło 3s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 3652
  entries                     : 6060
  closed_trades               : 6374
  wins                        : 3117
  losses                      : 3257
  win_rate_pct                : 48.9
  avg_R                       : 0.049
  expectancy_R                : 0.049
  realized_pnl_usd            : 40656.8
  total_return_pct            : 4065.68
  benchmark_return_pct        : 3640.07
  alpha_pct                   : 425.61
  max_drawdown_pct            : 46.75
  benchmark_max_drawdown_pct  : 83.4
  cagr_pct                    : 45.22
  benchmark_cagr_pct          : 43.67
  calmar                      : 0.97
  benchmark_calmar            : 0.52
  final_equity                : 41656.8
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
    2026       +8.2%       -7.1%    +15.3%

Interpretacja:
  Trafność 48.9% vs próg ~44% -> POWYŻEJ (jest edge)
  Expectancy 0.049R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: +425.61% -> BIJE indeks
  Lat z dodatnią alphą: 4/10
  Max obsunięcie: strategia 46.75% vs BTC/USD 83.4% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 45.22% vs BTC/USD 43.67%
  Calmar (zwrot na jednostkę bólu): strategia 0.97 vs BTC/USD 0.52 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Pełny wynik — Z mechanizmami
```
Pobieram do 10 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2225 świec (2020-07-13 → 2026-10-23)
  BTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  DOGE/USD: 3271 świec (2017-11-09 → 2026-10-23)
  ETH/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LINK/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  SOL/USD: 2388 świec (2020-04-10 → 2026-10-23)
  (pobieranie zajęło 3s)

=== WYNIK BACKTESTU (yahoo, mechaniczny rdzeń, bez Claude) ===
  steps                       : 3652
  entries                     : 334
  closed_trades               : 244
  wins                        : 114
  losses                      : 130
  win_rate_pct                : 46.7
  avg_R                       : 0.745
  expectancy_R                : 0.745
  realized_pnl_usd            : 24864.1
  total_return_pct            : 2486.41
  benchmark_return_pct        : 3640.42
  alpha_pct                   : -1154.01
  max_drawdown_pct            : 28.57
  benchmark_max_drawdown_pct  : 83.4
  cagr_pct                    : 38.46
  benchmark_cagr_pct          : 43.67
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
    2026       -4.6%       -7.1%     +2.5%

Interpretacja:
  Trafność 46.7% vs próg ~44% -> POWYŻEJ (jest edge)
  Expectancy 0.745R/transakcję -> dodatnia
  Alpha (cały okres) vs BTC/USD: -1154.01% -> przegrywa z indeksem
  Lat z dodatnią alphą: 4/10
  Max obsunięcie: strategia 28.57% vs BTC/USD 83.4% -> strategia broni kapitału lepiej
  CAGR (roczny zwrot składany): strategia 38.46% vs BTC/USD 43.67%
  Calmar (zwrot na jednostkę bólu): strategia 1.35 vs BTC/USD 0.52 -> strategia zarabia SPOKOJNIEJ (lepszy stosunek zysk/obsunięcie)
  Uruchom --sweep, by zobaczyć, ile zwrotu odblokowuje większa ekspozycja i jakim kosztem obsunięcia.
```
## Walk-forward — out-of-sample (czy przewaga trzyma się w czasie)
```
Pobieram do 10 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2225 świec (2020-07-13 → 2026-10-23)
  BTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  DOGE/USD: 3271 świec (2017-11-09 → 2026-10-23)
  ETH/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LINK/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  SOL/USD: 2388 świec (2020-04-10 → 2026-10-23)
  (pobieranie zajęło 3s)

=== WALK-FORWARD (yahoo, 4 okien OOS, mechaniczny rdzeń) ===
## Walk-forward (out-of-sample) — czy przewaga trzyma się w czasie

- Okien przebiegło: **4**
- Pobiło BTC: **1/4** · dodatni zwrot: **4/4**
- Alfa vs BTC: mediana **-21.45%** (min -133.98%, max 225.81%)
- Najgorsze obsunięcie w oknie: **28.57%**
- Przewaga spójna w czasie: **NIE**

| # | od | do | wejścia | trafność% | zwrot% | BTC% | alfa% | maxDD% | Calmar |
|---|----|----|---------|-----------|--------|------|-------|--------|--------|
| 1 | 2017-05-22 | 2019-09-28 | 61 | 55.1 | 145.42 | 279.4 | -133.98 | 28.57 | 1.26 |
| 2 | 2019-09-29 | 2022-02-04 | 136 | 53.9 | 637.91 | 412.09 | 225.81 | 18.42 | 5.32 |
| 3 | 2022-02-05 | 2024-06-13 | 76 | 47.4 | 37.29 | 61.09 | -23.79 | 19.22 | 0.6 |
| 4 | 2024-06-14 | 2026-10-23 | 61 | 24.5 | 4.03 | 23.15 | -19.12 | 26.31 | 0.05 |

Interpretacja:
  ⚠ Przewaga NIE jest spójna między oknami — wynik może pochodzić z jednego okna. Czerwona flaga GO-LIVE.
```
## Sweep — frontiera ryzyko/trade × równoczesne pozycje (z mechanizmami)
```
Pobieram do 10 lat świec dziennych dla 7 symboli (Yahoo)...
  AVAX/USD: 2225 świec (2020-07-13 → 2026-10-23)
  BTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  DOGE/USD: 3271 świec (2017-11-09 → 2026-10-23)
  ETH/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LINK/USD: 3271 świec (2017-11-09 → 2026-10-23)
  LTC/USD: 3652 świec (2016-10-24 → 2026-10-23)
  SOL/USD: 2388 świec (2020-04-10 → 2026-10-23)
  (pobieranie zajęło 3s)

=== PRZEMIATANIE EKSPOZYCJI (ryzyko/transakcję × liczba pozycji), 20 lat ===
  Strategia jest niedoinwestowana — ten test pokazuje granicę zysk↔obsunięcie.
   ryzyko%  pozycje     zwrot%    CAGR%   maxDD%   Calmar  trafność%    alpha%
  ----------------------------------------------------------------------------
       0.5        4     +299.1    +14.8    +12.4     +1.2      +43.5   -3342.1
       0.5        6     +395.6    +17.4    +22.3     +0.8      +35.9   -3245.5
       0.5        8     +422.4    +18.0    +24.8     +0.7      +35.0   -3218.7
       1.0        4     +577.3    +21.1    +22.5     +0.9      +43.6   -3063.8
       1.0        6     +633.9    +22.1    +28.5     +0.8      +37.6   -3007.2
       1.0        8     +499.0    +19.6    +29.7     +0.7      +36.4   -3142.1
       1.5        4    +1020.9    +27.4    +27.6     +1.0      +45.8   -2620.3
       1.5        6    +1261.2    +29.9    +30.1     +1.0      +43.9   -2380.0
       1.5        8    +1261.2    +29.9    +30.1     +1.0      +43.9   -2380.0
       2.0        4    +1276.0    +30.0    +29.4     +1.0      +45.0   -2365.1
       2.0        6    +1267.5    +29.9    +30.8     +1.0      +43.8   -2373.6
       2.0        8    +1267.5    +29.9    +30.8     +1.0      +43.8   -2373.6
       2.5        4    +1099.8    +28.2    +31.3     +0.9      +46.5   -2541.3
       2.5        6    +1041.5    +27.6    +31.3     +0.9      +44.4   -2599.6
       2.5        8    +1041.5    +27.6    +31.3     +0.9      +44.4   -2599.6
       3.0        4    +2520.9    +38.6    +28.8     +1.3      +49.0   -1120.2
       3.0        6    +2486.4    +38.5    +28.6     +1.4      +46.7   -1154.7
       3.0        8    +2486.4    +38.5    +28.6     +1.4      +46.7   -1154.7

  Benchmark (BTC/USD): zwrot 3641.13%, CAGR 43.67%, maxDD 83.4%, Calmar 0.52

Rekomendacja (na danych, nie na wyczucie):
  • Najlepszy Calmar (zysk/ból): ryzyko 3.0% × 6 pozycji → Calmar 1.35, zwrot 2486.41%, maxDD 28.57%
  • Najwyższy zwrot: ryzyko 3.0% × 4 pozycji → zwrot 2520.88%, maxDD 28.83%, Calmar 1.34
  Wybierz swój punkt: wyższy Calmar = spokojniejsza jazda, wyższy zwrot = większe obsunięcia.
  Ustaw wybrane na serwerze przez RISK_PER_TRADE_PCT i MAX_CONCURRENT_POSITIONS w .env, potem restart.
```
