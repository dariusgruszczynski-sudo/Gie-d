# Audyt „czy wszystko pod Kraken" + 30 propozycji usprawnień

**Data:** 2026-11-22 · noga krypto: Kraken spot EUR, tryb **LIVE** (€120)

---

## CZĘŚĆ 1 — AUDYT: czy wszystko jest pod Kraken?

### ✅ Zrobione w tej sesji (rdzeń działa pod Kraken)
| Obszar | Stan |
|---|---|
| Venue + klucz | Kraken, klucz z panelu, przeżywa restart |
| Waluta | EUR wszędzie (pulpit, sizing, benchmark) |
| Benchmark | BTC/EUR (było BTC/USD) |
| Widok konta | liczony WYŁĄCZNIE z Kraken (koniec €594k z Alpaki) |
| Rekoncyliacja | Kraken-only + samo-leczenie halt |
| Uniwersum | 484 pary EUR, skan 40 najpłynniejszych, TOP-20 |
| Egzekucja | live, minima zleceń zweryfikowane vs €12 |
| Fallback Alpaca | usunięty (był źródłem fantomów/haltów) |

### ⚠️ Zaszłości USD — działają, ale „myślą w dolarach" (do czyszczenia)
- `crypto_scanner_min_dollar_vol_usd = 2000` — próg płynności w USD, stosowany do obrotu EUR (€≈$, więc działa, ale mylące).
- `crypto_reconciliation_halt_floor_usd = 2000` — próg rozjazdu w USD.
- `auto_deploy_min_cash_usd = 25` — min. gotówka do wejścia w USD.
- `crypto_max_order_vs_dollar_vol_mult` + mapa `dollar_vol` — nazewnictwo USD.
- Pulpit w kilku miejscach pokazuje „$" i „kill-switch dźwigni −$1000".

### ❌ Zaszłości Alpaca — nie dotyczą Kraken spot (do usunięcia z nogi krypto)
- **Kill-switch dźwigni (−$1000)** — Kraken spot nie ma dźwigni, więc ten bezpiecznik jest bez sensu dla krypto.
- **Odniesienia do „blowoutu HYPE pod dźwignią"** w kodzie/UI — era Alpaca.
- **Brak modelu prowizji Kraken** (~0,25–0,40% taker) — sizing i P&L nie odejmują realnej prowizji; przy udowodnionym „koszty zjadają przewagę" to istotne.
- Panel „Podłącz konto Alpaca (paper)" wciąż w STER — zbędny, myli.

**Werdykt audytu:** rdzeń handlu jest w 100% pod Kraken i działa na żywo. Zostały
kosmetyczne/nazewnicze zaszłości USD i kilka martwych pojęć z Alpaki — nic nie blokuje
handlu, ale warto wyczyścić (patrz propozycje).

---

## CZĘŚĆ 2 — 15 PROPOZYCJI: MECHANIKI

> Legenda: **[DODAJ]** nowa funkcja · **[WYCZYŚĆ]** usuń/zastąp zaszłość · **[POPRAW]** napraw/ulepsz. Priorytet: 🔴 wysoki, 🟡 średni, ⚪ niski.

1. **[POPRAW] 🔴 Model prowizji Kraken w sizingu i P&L.** Odejmuj realną prowizję (~0,26% taker) przy wejściu/wyjściu i w „zysku bota". Bez tego przewaga jest przeszacowana — a wiemy, że koszty zjadają edge.
2. **[DODAJ] 🔴 Zlecenia limit/post-only zamiast market.** Market płaci taker (0,26%) + poślizg. Limit maker (0,16%) na płynnych parach obniża koszt ~2× — przy €120 i częstej rotacji to realne pieniądze.
3. **[WYCZYŚĆ] 🔴 Usuń kill-switch dźwigni (−$1000) z nogi krypto.** Kraken spot nie ma dźwigni; ten bezpiecznik jest martwy i myli na pulpicie.
4. **[POPRAW] 🟡 Przewalutuj progi USD→EUR.** `min_dollar_vol`, `reconciliation_floor`, `auto_deploy_min_cash`, `max_order_notional` — nazwij i licz w EUR (nowe knoby `*_eur`), żeby „myślenie w dolarach" zniknęło.
5. **[DODAJ] 🟡 Filtr spreadu bid/ask na wejściu.** Na 484 parach część ma szeroki spread; dodaj bramkę „spread ≤ X%" (z Ticker a/b), żeby nie wchodzić w parę, gdzie sam spread zjada zysk.
6. **[DODAJ] 🔴 Katalizatory jako realny sygnał (Filar INFORMACJA).** Dziś katalizatory (hacki/odblokowania) są w trybie „alert". Wepnij je w decyzję: twardy blok wejścia / de-risk przy świeżym haku na trzymanej monecie. To obiecana przewaga „bot czyta 24/7".
7. **[DODAJ] 🟡 Kalendarz odblokowań (unlock) z innego źródła.** DeFiLlama emissions = płatne; podłącz darmowe (np. Tokenomist/CoinMarketCal scrape), żeby blokować wejścia przed dużym unlockiem.
8. **[POPRAW] 🟡 Dostroić bramki wejścia do krypto 24/7.** Bramki (4h>SMA50, ADX≥20, konfluencja≥2) są z ery akcji. Na 20 płynnych krypto przez kilka h 0 wejść — rozważ okno obserwacji z luźniejszym progiem ALBO potwierdź, że to pożądana dyscyplina (dziś nie wiadomo, bo brak logu „ocen").
9. **[DODAJ] 🔴 Log „oceniłem, nic nie przeszło".** Silnik ocenia co cykl, ale nie loguje HOLD-ów gdy nic nie kupił → pulpit wygląda na martwy. Zapisuj lekki wpis „cykl: 40 par, 0 przeszło, najbliżej X (score 2/3)”. Widoczność = zaufanie.
10. **[DODAJ] 🟡 Trailing-stop % zamiast/obok twardego stopu.** Na trendowym krypto trailing łapie większość ruchu; dziś mamy głównie twardy stop. Opcja per-venue.
11. **[DODAJ] ⚪ Shadow-LLM włączony do zbierania materiału.** `crypto_llm_shadow_enabled=False` → nie zbieramy dowodu, czy LLM dołożyłby edge. Włącz log-only (zero kosztu handlu, realny koszt tokenów mały), żeby za miesiąc była decyzja go/no-go na danych.
11b. **[WYCZYŚĆ] 🟡 Usuń martwe ścieżki Alpaca-crypto z cyklu.** Po usunięciu fallbacku zostały gałęzie `if venue=="alpaca"` w nodze krypto — przejrzyj i wytnij, co nieosiągalne.
12. **[DODAJ] 🟡 Twardy dzienny budżet prowizji.** Limit „max X% konta/dzień na prowizje" — anty-churn kosztowy na małym koncie (€120 łatwo przehandlować w prowizjach).
13. **[DODAJ] ⚪ Korelacyjny cap ekspozycji.** Na 20 monetach łatwo mieć 10 pozycji skorelowanych z BTC = 1 zakład. Cap „suma skorelowanych ≤ X%”.
14. **[POPRAW] 🟡 Rekoncyliacja: dopasuj próg do €120.** Floor €2000 przy koncie €120 to w praktyce „nigdy” — ustaw sensownie (np. max(€5, 3% konta)), żeby watchdog realnie łapał rozjazdy, nie spał.
15. **[DODAJ] ⚪ Half-kelly / sizing od świeżej skuteczności.** Gdy przyjdą pierwsze zamknięcia, skaluj wielkość pozycji od realnego payoffu (ostrożnie gdy edge słaby) — masz już `edge_payoff`, dołóż pętlę.

---

## CZĘŚĆ 3 — 15 PROPOZYCJI: UX

> Priorytet jak wyżej.

1. **[POPRAW] 🔴 Spójny wskaźnik LIVE/paper wszędzie.** (Zrobione częściowo: STER + pasek.) Dołóż czerwony pasek „🔴 HANDEL NA ŻYWO — €120” na Kokpicie, gdy live — żeby nigdy nie było wątpliwości (dziś to był realny problem).
2. **[WYCZYŚĆ] 🔴 Usuń panel „Podłącz konto Alpaca" ze STER.** Zbędny i mylący — jesteśmy na Kraken. Zostaw „Podłącz Kraken".
3. **[POPRAW] 🔴 „Bezczynny" → mów, co robi.** Zamiast samego „BEZCZYNNY — nie handluje" pokaż „Skanuję 40 par, czekam na setup (najbliżej: X)” — żeby „bezczynny” nie straszył, że bot stoi.
4. **[WYCZYŚĆ] 🟡 Zamień wszystkie „$" na „€" i usuń „kill-switch dźwigni −$1000".** Resztki dolarów/dźwigni na Kokpicie i w Werdykcie.
5. **[DODAJ] 🟡 Panel „Pierwszy fill na żywo”.** Po pierwszej realnej transakcji pokaż kartę: cena, prowizja, poślizg vs oczekiwana cena — dowód, że egzekucja działa czysto.
6. **[POPRAW] 🟡 Monety: pokaż 40 skanowanych, nie tylko 20 trzymanych w uniwersum.** Rozdziel „w aktywnym uniwersum (20)” od „skanowane szerzej (40)” i „cały rynek (484)”.
7. **[DODAJ] 🟡 Mini-wykres ceny przy monecie (sparkline).** Na liście Monet dołóż 24h sparkline — jednym rzutem oka widać, co się rusza.
8. **[POPRAW] ⚪ Werdykt: usuń resztki „backtest 10 lat / blowout".** (Częściowo zrobione.) Dokończ — to era Alpaca, myli na Kraken.
9. **[DODAJ] 🟡 Przełącznik LIVE↔paper w STER (bez deployu).** Dziś zmiana trybu wymaga deployu; zrób bezpieczny toggle w panelu (z potwierdzeniem), żebyś mógł cofnąć na paper od ręki.
10. **[DODAJ] 🔴 Widoczny licznik prowizji.** „Prowizje zapłacone dziś / łącznie" — na małym koncie to kluczowy koszt, musi być na wierzchu obok „zysku bota".
11. **[POPRAW] 🟡 Katalizatory wyżej na Kokpicie.** Filar INFORMACJA to przewaga — daj mu mocniejsze miejsce (nie zwijaną sekcję), gdy są świeże zdarzenia.
12. **[DODAJ] ⚪ Powiadomienie push przy pierwszym realnym wejściu/wyjściu.** Na żywej kasie chcesz wiedzieć od razu, nie po fakcie na pulpicie.
13. **[POPRAW] 🟡 Pasek statusu: dodaj „prowizja” i „ekspozycja €".** Zamiast 3 liczb — 4 kluczowe pod Kraken: Konto, Dziś, Zysk (po prowizji), Prowizje.
14. **[DODAJ] ⚪ „Co bot widzi teraz" — top 3 najbliższe wejścia.** Na Kokpicie mini-lista „najbliżej setupu: X (2/3), Y (2/3)” — pokazuje, że silnik pracuje i czego szuka.
15. **[WYCZYŚĆ] ⚪ Przejrzyj teksty pomocy/hinty pod Kraken.** Część hintów mówi o Alpace/akcjach/sesji US — zaktualizuj pod krypto 24/7 EUR.

---

## Rekomendowana kolejność (gdybym miał wybrać 5 najpilniejszych)
1. Model prowizji + licznik prowizji (mechanika #1 + UX #10) — na żywej kasie koszt to priorytet.
2. Usuń kill-switch dźwigni + panel Alpaca + „$” (mechanika #3, UX #2, #4) — czystka zaszłości.
3. Log „oceniłem, nic nie przeszło” + „bezczynny → co robi” (mechanika #9, UX #3) — widoczność pracy silnika.
4. Katalizatory jako sygnał (mechanika #6) — realizacja obiecanej przewagi INFORMACJA.
5. Limit/post-only zlecenia (mechanika #2) — tańsza egzekucja.
