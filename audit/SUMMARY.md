# Audyt GielDarek — 2026-10-18T20:46:11Z

**Wdrożenie:** kod e9952d4 (zbud. 2026-10-18T08:16Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (27× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 4 · dni z limitem 5 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 11 · odrzuconych: 109

**Najczęstsze powody odrzucenia (top):**
- 25× — Automat (alpaca) zapauzowany ręcznie
- 9× — brak powodu
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~135 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~150 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~165 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~180 min
- 1× — Cooldown po stop-lossie: LTC/USD zablokowany do odkupu jeszcze ~136 min

**Ostatnie 20 decyzji:**
- 2026-10-18T20:31:31.258738 LTC/USD BUY conf=0.6 trig=scheduled_daily ⛔ Cooldown po stop-lossie: LTC/USD zablokowany do odkupu jeszcze ~136 min
- 2026-10-18T20:31:31.254025 ETH/USD BUY conf=0.6 trig=scheduled_daily ⛔ Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~135 min
- 2026-10-18T20:31:31.249657 SOL/USD BUY conf=0.6 trig=scheduled_daily ⛔ Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~135 min
- 2026-10-18T20:16:31.216988 LTC/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: LTC/USD zablokowany do odkupu jeszcze ~151 min
- 2026-10-18T20:16:31.212623 ETH/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~150 min
- 2026-10-18T20:16:31.207913 SOL/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~150 min
- 2026-10-18T20:01:32.129249 LTC/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: LTC/USD zablokowany do odkupu jeszcze ~166 min
- 2026-10-18T20:01:32.123827 ETH/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~165 min
- 2026-10-18T20:01:32.118934 SOL/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~165 min
- 2026-10-18T19:46:42.280905 AVAX/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-18T19:46:40.554671 DOGE/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-18T19:46:37.048047 LINK/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-18T19:46:37.043742 LTC/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: LTC/USD zablokowany do odkupu jeszcze ~180 min
- 2026-10-18T19:46:37.038641 ETH/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~180 min
- 2026-10-18T19:46:37.034231 SOL/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~180 min
- 2026-10-18T19:46:29.396108 LTC/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-18T19:46:28.361537 SOL/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-18T19:46:27.242517 ETH/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-18T08:30:03.081280 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-18T06:06:28.984572 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
