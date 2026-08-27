# Audyt GielDarek — 2026-08-27T17:09:20Z

**Wdrożenie:** kod f514c50 (zbud. 2026-08-24T17:06Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 36 zamknięć · trafność 30.6% · zrealizowany $9.9
**7 dni:** 10 zamknięć · 30.0% · $-1.13   |   **30 dni:** 64 · 28.1% · $12.2
**Edge:** śr. wygrana +$2.88 vs strata $-0.87 → na transakcję $0.27 (payoff 3.31×)
**Trzymanie:** zyski ~4.9 dni · straty ~2.0 dni

## Wnioski
- (neu) Trafność 7 dni 30% vs 30 dni 28% — stabilna.
- (bad) Ostatnie 7 dni: -1.13 $ z 10 zamknięć.
- (good) Średnia wygrana +$2.88 vs strata −$0.87 (wygrana 3.31× większa) → na transakcję +$0.27. Zarabia mimo <50% trafności — edge dodatni.
- (bad) ⚠ Zyski trzymane dłużej (~5 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: JAZZ (-4.31 $, 1 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.60 < próg 0.70 (baza 0.55 + 5 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (22× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- JAZZ: $-4.31 (1 zamk., 0%)
- META: $-2.97 (1 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- NDSN: $-1.08 (1 zamk., 0%)
- ROST: $-1.0 (1 zamk., 0%)
- LITE: $-0.8 (2 zamk., 0%)
- DIS: $-0.76 (2 zamk., 0%)
- UGI: $-0.75 (1 zamk., 0%)
- TGT: $-0.68 (1 zamk., 0%)
- MSFT: $-0.59 (2 zamk., 0%)

## Wejścia vs limit
- cap 8/dzień · max w dniu 57 · dni z limitem 5 · hamuje: true
