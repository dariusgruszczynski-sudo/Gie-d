# Analiza toola pod Kraken (Opcja D) + 50 propozycji zmian — 2026-11-21

> Decyzja właściciela: **Opcja D** — info-first, baza spot na Kraken, short TYLKO jako hedge
> (margin 1x, napędzany katalizatorem, nie predykcją). Tu: analiza obecnego kodu pod to, co
> daje Kraken, i 50 konkretnych propozycji (P1 krytyczny · P2 ważny · P3 porządkowy).

---

## CZĘŚĆ 1 — Analiza: gdzie jesteśmy vs co daje Kraken

**Jak jest teraz (spięcie z Alpaca):**
- Brak abstrakcji brokera — silnik woła wprost `AlpacaClient` (get_klines, get_price,
  get_account_balances, place_market_order_usdt_amount/quantity, place_order_for_session).
- Format symbolu `BASE/USD`, kwotowanie **USD**; dane rynkowe przez Alpaca v1beta3.
- Rozliczenia/scorecard w USD. Zero obsługi margin/short. Zero WS (polling REST).

**Co zmienia/daje Kraken:**
- Kwotowanie **EUR**; inne nazwy par (`XXBTZEUR`, `XDGEUR`…), inne min-ordery, inne opłaty.
- **Margin spot do ~5x przez TEN SAM klucz API** → short możliwy bez osobnej platformy (klucz do Opcji D).
- Auth: nonce + HMAC-SHA512; rate-limity „counter"; WebSocket feeds (realny czas, taniej niż polling).
- Futures jako osobna platforma (poza Opcją D — pomijamy na teraz).

**Największe luki do zamknięcia:** (1) brak adaptera/abstrakcji brokera, (2) wszystko w USD a konto
w EUR, (3) brak short/hedge, (4) tor katalizatorów zbudowany ale nie wpięty, (5) brak walidacji short-edge.

---

## CZĘŚĆ 2 — 50 propozycji

### A. Adapter Kraken / abstrakcja brokera (fundament portu)
1. **[P1]** `BrokerAdapter` — wspólny interfejs (klines/price/balances/summary/place_order/cancel), żeby silnik nie znał giełdy (#26 z backloga).
2. **[P1]** `KrakenClient` implementujący ten interfejs: REST + podpis nonce/HMAC-SHA512, odczyt klucza z env (`KRAKEN_API_KEY`/`KRAKEN_API_SECRET`), nigdy z kodu.
3. **[P1]** Warstwa mapowania symboli: uniwersum `BTC..DOGE` ↔ pary Kraken (`XXBTZEUR`…) + wsname, w jednym miejscu.
4. **[P1]** Mapa min-orderów per para (z `AssetPairs`) → odrzucaj/zaokrąglaj zlecenia poniżej minimum czysto.
5. **[P2]** Obsługa rate-limitów Kraken (API counter) z backoffem — reuż `retrying.with_retries`.
6. **[P2]** WebSocket feed cen/trade (zamiast pollingu) — świeższe dane, mniej requestów, tańsze.
7. **[P2]** `paper-on-Kraken`: tryb dry-run na realnych danych Kraken, zanim pójdą realne zlecenia.
8. **[P3]** Fallback: gdy Kraken REST padnie, degraduj do ostatniego snapshotu zamiast wywalać cykl.

### B. EUR / waluta / rozliczenia
9. **[P1]** `quote_currency = EUR` dla nogi Kraken; wszystkie notional/sizing w EUR, nie USD.
10. **[P1]** Rozdziel „waluta konta" (EUR) od benchmarku (BTC) — scorecard liczy alfę w EUR vs trzymanie BTC.
11. **[P2]** Model opłat Kraken (maker/taker + margin open/rollover/likwidacja) wpięty w sizing i P&L.
12. **[P2]** Konwersja min-order EUR ↔ ilość per para na bieżąco (cena z feedu), żeby nie odbijać zleceń.

### C. Short jako HEDGE (Opcja D — margin 1x, napędzany katalizatorem)
13. **[P1]** Margin-order w `KrakenClient` (`leverage` param) — ale twardo ograniczony configiem do **1x** (żadnej realnej dźwigni na start).
14. **[P1]** `hedge_on_catalyst`: hack/zła wiadomość na trzymanej monecie → zamiast samego wyjścia, opcjonalny short-hedge (config-gated OFF).
15. **[P1]** Bufor likwidacji: nigdy nie zbliżaj pozycji margin do ceny likwidacji; twardy margines bezpieczeństwa.
16. **[P2]** Świadomość kosztu rollover (co 4h) — zamykaj hedge, gdy koszt utrzymania > oczekiwana ochrona.
17. **[P2]** Limit łącznej ekspozycji short (cap % konta) + zakaz short bez powiązanego katalizatora (żadnych spekulacyjnych shortów).
18. **[P3]** Log każdego hedge: powód (katalizator), wejście/wyjście, uratowane/stracone — do audytu skuteczności.

### D. Katalizatory / informacja (dokończenie Filara — proven edge)
19. **[P1]** Klasyfikator LLM powagi/trafności zdarzenia („czy to zagraża monecie, którą handluję, i jak mocno") — config-gated, tani (tylko na zdarzeniach, nie co cykl).
20. **[P1]** Wpięcie toru katalizatorów w żywy cykl (najpierw `alert_only`/shadow, dopiero po dowodzie `act`).
21. **[P1]** Panel „bot czyta 24/7": lista zdarzeń + decyzje bota — **widoczny efekt dla właściciela**.
22. **[P2]** Kalendarz unlocków (DeFiLlama/emissions) → blokada wejścia przed dużym odblokowaniem (SOL/AVAX/DOGE).
23. **[P2]** Feed listingów dużych giełd (tylko alert, nigdy auto-kupno) — walidacja przed jakimkolwiek działaniem.
24. **[P2]** Feed funding-rate/likwidacji (dane perp) — reżim „przegrzania" jako kontekst ryzyka.
25. **[P3]** Pipeline newsów (RSS/API) → LLM → zdarzenie; deduplikacja i tłumienie szumu.
26. **[P3]** Tracker rotacji narracji (LLM czyta media) — jako kontekst, nie wyzwalacz.

### E. Walidacja / dowód (warunek każdej zmiany zachowania)
27. **[P1]** Bramka walk-forward OOS: żadna strategia (long/short) nie idzie live bez dodatniej EV na wielu reżimach.
28. **[P1]** Test short-edge OOS na danych 1h (Binance Vision, mamy pipeline) — czy short w ogóle ma przewagę, zanim włączymy hedge jako alfę.
29. **[P1]** Backtest na danych KRAKEN EUR (nie tylko Yahoo/Binance) — spójność z realnym venue.
30. **[P2]** Monitor zużycia edge (edge-decay): ciągła re-walidacja, alarm gdy przewaga znika.
31. **[P2]** Shadow-mode dla KAŻDEGO nowego sygnału (reuż infrastrukturę Claude-shadow) przed live.

### F. Ryzyko / dyscyplina (najpewniejszy edge)
32. **[P1]** Dzienny budżet ryzyka w R; stop po wyczerpaniu (nie % — R).
33. **[P1]** Breaker serii strat: po N stopach z rzędu — pauza i alarm.
34. **[P1]** Reconciliation Kraken (ledger vs saldo brokera) PRZED zleceniem — lekcja blowoutu, port watchdoga.
35. **[P2]** Sizing świadomy likwidacji na margin (mniejsza pozycja im bliżej bufora).
36. **[P2]** Portfelowy cap korelacji (suma pozycji skorelowanych z BTC), nie tylko liczba pozycji.
37. **[P3]** Twardy kill-switch EUR (globalny stop przy stracie > X EUR) — namacalny dla małego konta.

### G. Pomiar / scorecard (EUR, uczciwie)
38. **[P1]** Scorecard w EUR: realized/unrealized, alfa vs trzymanie BTC w EUR, po opłatach Kraken.
39. **[P2]** Rozdział wyniku: spot-long vs hedge-short — który filar realnie zarabia/chroni.
40. **[P2]** Fill-rate i poślizg mierzony na realnych fillach Kraken (nie modelowany).
41. **[P3]** Śledzenie kosztów (opłaty + rollover) jako osobna linia — ile zjada handel.

### H. UX / obserwowalność (widoczny efekt)
42. **[P1]** Chip venue „Kraken (EUR)" + poprawne formatowanie EUR w całej apce.
43. **[P1]** Panel katalizatorów (zdarzenia + decyzje) — już zaprojektowany, do wpięcia.
44. **[P2]** Panel hedge/short: otwarte hedge, powód, koszt rollover, odległość do likwidacji.
45. **[P2]** Kryteria GO-LIVE zaktualizowane pod realny EUR Kraken (próg trejdów/tygodni/DD) — jasny sygnał „gotowe na większy kapitał".
46. **[P3]** „Dlaczego (nie) wchodzi" (lejek) dopięty do nogi Kraken.

### I. Bezpieczeństwo / klucze (realna gotówka = realne ryzyko)
47. **[P1]** Klucz WYŁĄCZNIE z env serwera; zero sekretów w repo/kodzie/czacie; walidacja obecności przy starcie.
48. **[P1]** Eskalacja uprawnień klucza: start read-only (Query Funds) → „Create Orders" dopiero po paper-teście; osobne klucze per etap.
49. **[P2]** IP-allowlist na kluczu Kraken (tylko IP serwera) + API 2FA — Kraken to wspiera.
50. **[P2]** Przypomnienie o rotacji klucza + wykrywanie „klucz w logu/czacie" → alarm (ten wklejony klucz: ODWOŁAĆ).

---

## Kolejność wdrożenia (pod Opcję D)
1. **Fundament:** A1–A4 (adapter Kraken spot) + B9–B10 (EUR) + I47–I48 (klucze). To brama realnej gotówki.
2. **Proven edge równolegle:** D19–D21 (katalizatory + panel) + E27 (bramka walidacji) + F32–F34 (dyscyplina/recon).
3. **Dopiero po dowodzie:** C13–C18 (short jako hedge, margin 1x) — i tylko jeśli E28 (short-edge/hedge-wartość) się potwierdzi.
4. **Porządki:** reszta P2/P3.

**Zasada nadrzędna (Opcja D):** instrument (margin/short) to narzędzie RYZYKA napędzane INFORMACJĄ,
nie maszynka do predykcji. Żadna dźwignia nie wchodzi na strategię bez udowodnionego OOS edge.

---
*Oparte na: lekturze kodu (alpaca_client/trading_engine/risk_manager), rekonesansie konta Kraken
(API), analizie oferty (`kraken-analiza-opcje-2026-11-21.md`) i dowodzie „zero edge w cenie" (930 trade).*
