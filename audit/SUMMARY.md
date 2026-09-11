# Audyt GielDarek — 2026-09-11T14:46:16Z

**Wdrożenie:** kod 9c01376 (zbud. 2026-09-11T14:40Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 51 zamknięć · trafność 27.5% · zrealizowany $-5.3
**7 dni:** 6 zamknięć · 33.3% · $-5.34   |   **30 dni:** 48 · 27.1% · $-6.21
**Edge:** śr. wygrana +$2.8 vs strata $-1.2 → na transakcję $-0.1 (payoff 2.33×)
**Trzymanie:** zyski ~4.6 dni · straty ~2.8 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 51 zamknięć, trafność 27% — pod kreską (−$5.30).
- (good) Trafność 7 dni 33% vs 30 dni 27% — rośnie.
- (bad) Ostatnie 7 dni: -5.34 $ z 6 zamknięć.
- (bad) Średnia wygrana +$2.80 vs strata −$1.20 (wygrana 2.33× większa) → na transakcję −$0.10. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~5 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.33 $, 3 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-5.33 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- NVDA: $-2.4 (5 zamk., 20%)
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- V: $-1.54 (1 zamk., 0%)
- AAPL: $-1.24 (1 zamk., 0%)

## Wejścia vs limit
- cap 8/dzień · max w dniu 57 · dni z limitem 5 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: true · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów Opusa: min_buy_confidence=0.72, max_new_positions_per_day=2, max_concurrent_positions=4, min_hold_minutes=1440, hard_take_profit_pct=7.0, stop_loss_min_pct=2.5, stop_loss_max_pct=7.0, trailing_stop_frac=0.5, risk_per_trade_pct=1.5, conviction_max_risk_per_trade_pct=3.0, price_move_trigger_pct=2.5, reward_risk_ratio=2.5, min_hold_profit_bypass_pct=2.5, entry_min_score=3, conviction_size_max_mult=1.3
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9
