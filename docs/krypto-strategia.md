# Strategia krypto — wnioski z researchu + jak dostroić silnik

Cel: **maksymalny zysk SKORYGOWANY O RYZYKO** (oczekiwana wartość × przeżycie),
nie surowy „max zysk" (ten = max ryzyko ruiny). Dokument spisany na prośbę
właściciela: „naucz się jak handluje się krypto, wyciągnij wnioski, daj znać jak
dostroić strategię". Źródła na końcu.

## Uczciwe sprostowania
- **Nie ma 20 lat historii krypto.** Bitcoin: 2009; sensowne dane giełdowe od
  ~2013 (≈12 lat). 20 lat dotyczy *akcji* — ale 20-letnie dowody na trend-following
  przenoszą się na krypto, więc z nich korzystamy.
- **Danych historycznych nie dociągniemy z tego środowiska** (sandbox blokuje
  hosty danych — Binance/Yahoo 403). Backtest na realnych danych odpala się na
  prodzie (VPS), `backend/scripts/run_backtest.py --venue crypto`.

## Co REALNIE ma przewagę w krypto (wnioski)
1. **Time-series momentum / trend-following** — najmocniejsza, udokumentowana
   przewaga (dekada walk-forward; 2020-25 ~32%/rok, Sharpe ~1.6). Podążaj za
   trendem wyższego interwału z filtrem reżimu; nie łap dołków.
2. **Tnij straty, pozwól zyskom biec** — asymetria robi wynik. Sztywny mały
   take-profit = ujemny skos (mały zysk, duży stop). Zwycięzców prowadź trailingiem,
   część lockuj na partialu, twardy TP tylko na paraboliczny blow-off.
3. **Volatility targeting (sizing pod zmienność)** — stałe $-ryzyko do stopa
   poprawia zwrot/ryzyko i spłaszcza obsunięcia. Ale vol patrzy wstecz → zawsze
   twardy stop (luka/news potrafi przebić budżet).
4. **Koszty zjadają momentum** — wiele teoretycznie zyskownych portfeli traci
   istotność po fee+spread. Wniosek: MNIEJ, dłuższych, wyższej-konwikcji pozycji.
   „Dynamiczny" = responsywny na zmianę trendu, NIE „więcej transakcji".
5. **Cross-sectional (rotacja między nazwami) słabszy niż time-series** w krypto.
   Nie przesadzaj z rotacją za relatywną siłą; trzymaj działający trend.
6. **Regime filter** — longi tylko gdy reżim risk-on / nad długą średnią; w risk-off
   gotówka. Trend-following z filtrem reżimu bije sam trend-following.

## Jak to przełożyliśmy na silnik (knoby krypto)
- `crypto_hard_take_profit_pct = 40%` (było sztywne 6%) — **koniec ścinania
  zwycięzców**; zwykłe trendy jadą na trailingu, twardy TP łapie tylko blow-off.
- `crypto_trailing_stop_frac = 0.6` (było 0.5) — szerszy trailing = dłuższa jazda.
- `crypto_partial_take_profit` 1/3 przy 1.5R — de-risk, reszta jedzie.
- Bez zmian (świadomie): stopy vol-scaled 4–18%, ryzyko 1.5%/transakcję
  (vol-targeting), timeframe 1h + poll 15 min (BEZ zwiększania częstotliwości —
  koszty), filtr reżimu ON, limity ryzyka krypto 30/40/55%.

## Jak dostrajać dalej (świadomie, z kosztem w tle)
- Chcesz MOCNIEJ trzymać trendy → podnieś `crypto_trailing_stop_frac` (0.6→0.7)
  i/lub `crypto_hard_take_profit_pct`. Ryzyko: oddajesz więcej zysku na korekcie.
- Chcesz szybciej realizować → obniż `crypto_partial_take_profit_r` (1.5→1.0) lub
  podnieś `crypto_partial_take_profit_frac`. Ryzyko: mniej jazdy w trendzie.
- NIE skracaj timeframe'u ani nie podkręcaj częstotliwości dla „dynamiki" —
  dowody mówią, że koszty zabiją edge. Dynamika ma być w JAKOŚCI wejść, nie liczbie.
- Każda zmiana = knob w `.env`/configu, potem backtest na prodzie, potem obserwacja
  ≥50 zamknięć. Nie stroimy pod kilka ostatnich transakcji (błąd z ery akcji).

## 5 ulepszeń strategii (wdrożone) — strona WYJŚĆ/RYZYKA
Świadomie NIE dokładaliśmy restrykcyjnych filtrów WEJŚĆ (6-letni backtest: nadmiar
filtrów wejścia pogarszał wynik). Przewaga trend-followingu żyje w zarządzaniu
pozycją, więc 5 ulepszeń działa na wyjściach, ryzyku i sizingu (knoby `crypto_*`):
1. **Breakeven ratchet** — gdy szczyt zysku ≥ `crypto_breakeven_trigger_pct` (8%),
   zwycięzca nie może zejść pod wejście → zamknięcie na ~zero zamiast oddania zysku.
2. **Winner ratchet** — po dużym biegu (≥ `crypto_ratchet_trigger_pct`, 15%)
   trailing się zacieśnia (× `crypto_ratchet_trail_mult`), lockując więcej trendu.
3. **Trend-invalidation exit (HARTOWANY)** — zamknięcie pod `SMA crypto_trend_exit_ma_period`
   (50) = trend złamany, wychodzimy przed szerokim stopem. Po żywym paperze (2026-10-07:
   SMA50/1h bez bufora = whipsaw na rynku bocznym, payoff 0.03×) dołożony **bufor**
   `crypto_trend_exit_buffer_pct` (3% — wyjście dopiero wyraźnie pod średnią, nie na tick)
   i **potwierdzenie** `crypto_trend_exit_confirm_bars` (2 świece zamknięte pod średnią =
   trwałe złamanie, nie knot). Hartujemy TYLKO wyjście — wejść nie filtrujemy (lekcja z akcji).
4. **De-risk na chciwość** — Fear&Greed ≥ `crypto_fng_derisk_above` (85) → NOWE
   wejścia mniejsze (× `crypto_derisk_size_mult`).
5. **De-risk na zatłoczony funding** — funding BTC ≥ `crypto_funding_derisk_above_pct`
   (0.08%) → NOWE wejścia mniejsze (longi przegrzane, ryzyko flusha).
Wszystkie gate'owane configiem; dla akcji/POZA SESJĄ neutralne (0/off).

## 10 mechanizmów P(zysk) — 2026-10-07 (wdrożone 6/10)
Wszystko config-gated, knoby bazowe off (akcje nietknięte), krypto przez `_CRYPTO_OVERRIDES`.
Strona reżimu/ryzyka/wyjść (zgodne z lekcją „nie filtruj wejść restrykcyjnie").
**Wdrożone:** (1) filtr reżimu HTF `crypto_regime_filter_*` (BTC>SMA200 D1 = risk-on);
(2) re-entry cooldown `crypto_reentry_cooldown_min` (180) po każdym pełnym wyjściu;
(3) trailing skalowany zmiennością `crypto_vol_trail_mult` (1.5×vol% jako podłoga);
(4) cap ekspozycji `crypto_max_total_exposure_pct` (60%); (5) breaker serii strat
`crypto_loss_streak_pause` (4/dzień → pauza do rolki UTC); (7) pauza na przegrzaniu
`crypto_fng_pause_above` (93) / `crypto_funding_pause_above_pct` (0.15).
**Czeka na backtest (prod):** (8) Donchian breakout, (9) ADX-gate, (10) piramidowanie
— wymagają świec OHLC w ścieżce wejścia (dziś closes-only). (6) vol-targeting ~pokryte
przez `volatility_adjusted_size`.

## Weryfikacja
- Prod: `python backend/scripts/run_backtest.py --venue crypto` (benchmark BTC/USD).
- Żywy paper: dzienny nadzór (audit-snapshots) + ten dziennik. Werdykt GO-LIVE
  dopiero, gdy aktywny handel BIJE trzymanie BTC na ≥50 zamknięciach / ~3 tyg,
  z expectancy>0 i obsunięciem w ryzach — patrz `docs/krypto-dziennik.md`.

## Źródła
- A Decade of Evidence of Trend Following in Cryptocurrencies — https://ar5iv.labs.arxiv.org/html/2009.12155
- Time Series vs Cross-Sectional Momentum in Crypto (AUT) — https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf
- Volatility targeting (sizing / risk-adjusted) — https://www.daytrading.com/volatility-targeting
- Trend following (crypto, praktyka) — https://tradingstrategy.ai/docs/learn/trend-following.html
