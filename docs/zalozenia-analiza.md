# GielDarek — Założenia: analiza i rekomendacje

**Data:** 2026-08-21 · **Dane bazowe:** audyt `cb43313` (gałąź `audit-snapshots`)
**Stan konta (rząd wielkości):** ~$500–800 + wpłaty $100–300/mies. · tryb **LIVE**.

Liczby z audytu (żeby analiza stała na danych, nie na przeczuciu):

| Metryka | Życiowo | 7 dni | 30 dni |
|---|---|---|---|
| Zamknięcia | 30 | 17 | 118 |
| Trafność | 30% | 35% | 25% |
| Zrealizowany | $13.96 | $11.35 | $13.91 |

**Edge:** śr. wygrana **+$2.98** vs strata **−$0.61** → **+$0.46 na transakcję**, payoff **4.89×**.
**Trzymanie:** wygrane ~5.0 dni, straty ~1.8 dni. **Największy przeciek:** AMZN −$2.22.

> **Jedno zdanie prawdy:** bot ma **dodatnią przewagę** (zarabia mimo 30% trafności, bo wygrana jest ~5× większa od straty). Największe ryzyka to **churn** (118 zamknięć/30 dni na malutkim koncie) i **koszt AI** względem kwot, o które gramy — nie sama strategia.

---

## 1. Kapitał, wpłaty, horyzont

### 1.1. Teza małego konta — czy to ma sens vs zwykłe DCA w SPY
**Dane:** ~$13.9 zrealizowanego/30 dni na ~$600 to ~2.3%/mies. brutto. SPY robi historycznie ~0.8%/mies. Więc *brutto* bot bije DCA. **ALE** trzeba odjąć koszt Claude i uczciwie policzyć papierowy P&L.
**Rekomendacja:** teza się broni **tylko** dopóki (a) edge zostaje dodatni po odjęciu kosztu AI i (b) kapitał rośnie, bo przy $600 nawet 2.3%/mies. to ~$14 — psychologicznie mało. To **maszyna na procenty, nie na kwoty** — kwoty przyjdą z kapitału. Traktuj obecną fazę jako **walidację edge na małej próbce**, nie jako źródło dochodu.

### 1.2. Próg kapitału na sensowny $
**Model (przy utrzymaniu ~2%/mies. netto):** $50/mies. zysku wymaga ~$2.5k; $200/mies. ~$10k; $1000/mies. ~$50k. Wpłaty $100–300/mies. dominują wynik przez pierwsze ~1–2 lata (skarbonka), potem procent składany zaczyna realnie dokładać.
**Rekomendacja:** ustaw oczekiwania: **do ~$5k konto to trening**; realny „drugi strumień" zaczyna się ~$20–50k. Użyj kafla **Plan i cel** (dodany w tej sesji), żeby widzieć postęp.

### 1.3. Kiedy włączyć Opus (eskalacja AI)
**Dziś:** PM leci wyłącznie na tanim Sonnecie (`claude_escalation_enabled=false`) — świadomie, bo Opus ~5× droższy na każdym niepewnym cyklu.
**Rekomendacja:** włącz eskalację do Opusa dopiero, gdy **koszt Opusa/mies. < ~2–3% konta**. Przy poll co 30 min i bramkowaniu wyzwalaczem to realnie **~$8–12k konta**. Poniżej — Sonnet jest wystarczający (edge jest dodatni na samym Sonnecie). Do tego czasu **nie zmieniać**.

### 1.4. Realny horyzont 1,5–3 lata
**Warianty (wpłata × edge, konserwatywnie ~1.5%/mies. netto po kosztach):**
- $100/mies., start $600: po 1,5 roku ≈ **$2.5–3k** (z tego ~$1.8k to wpłaty).
- $300/mies., start $600: po 1,5 roku ≈ **$6–7k**; po 3 latach ≈ **$14–17k**.
- Cel $20k: realny przy **$300/mies. + ~3 lata** albo szybciej z wyższą wpłatą.

**Uczciwie:** w tym horyzoncie **wpłaty > zysk bota**. Zysk bota to „turbo" na wpłaty, nie zamiennik. Nie ma tu ścieżki „$600 → $20k z samego handlu" w 1,5 roku bez ryzyka ruiny.

---

## 2. Rdzeń strategii

### 2.1. Audyt Scenariusza A (sizing przekonania) — ⏳ za wcześnie
**Fakt:** conviction sizing wdrożony `2026-08-21 18:31Z` — trades po tej dacie dopiero się zbierają. Audyt z tej gałęzi to jeszcze głównie STARA epoka.
**Rekomendacja:** **audyt umówiony na wtorek 1 września** (napisz „audyt"). Kryterium sukcesu: czy większe pozycje przy wysokiej pewności podniosły **$/transakcję** i **payoff**, nie ruszając max-drawdown. Jeśli edge/trade spadnie albo drawdown urośnie → cofnąć do 1.0× lub obniżyć `conviction_size_max_mult` do 1.5.

### 2.2. Czy min-hold 2 dni pomaga
**Dane:** wygrane trzymane ~5d, straty ~1.8d — asymetria we **właściwą** stronę (tnij straty, pozwól zyskom rosnąć), i to ona daje payoff 4.89×. Mimo min-hold 2 dni churn dalej wysoki (118/30d).
**Rekomendacja:** min-hold 2 dni **działa** (wygrane realnie trzymane dłużej). Uwaga heurystyki „zwleka z zyskiem" jest **myląca** — dłuższe trzymanie wygranych to źródło przewagi, nie wada. **Nie skracać.** Churn bierze się z *liczby wejść*, nie z min-hold (patrz 2.3).

### 2.3. Próg wejścia / progresywna pewność
**Dane:** najczęstszy powód pominięcia: „pewność 0.60 < próg 0.70 (baza 0.55 + 5 poz. × 0.03)" — **26×/300 decyzji**. Limit wejść osiągany w 5 dniach (hamuje). Max prób w dniu ~57.
**Rekomendacja:** progresywny próg **działa jak zaprojektowano** — dusi 6.+ wejście, wymuszając jakość. To **dobrze** przy churnie. Rozważ delikatne **zaostrzenie** (`progressive_confidence_step` 0.03→0.04) zamiast luzowania — mniej, ale lepszych wejść. Decyzja Twoja (zmiana na żywej kasie).

### 2.4. Teza „AI-tool zamiast kalkulatora"
**Dane:** dodatni edge (payoff 4.89×) sugeruje, że dobór Claude łapie asymetrię, której sztywne sito by nie złapało. Ale nie mamy czystego porównania „Claude vs mechanika" na tej samej próbce.
**Rekomendacja:** włącz/oglądaj **shadow-analysis** (jest w kodzie) jako pomiar „co zrobiłaby sama mechanika" i porównuj co miesiąc. Dopóki Claude bije mechanikę na edge — teza się broni. To jedyny uczciwy test.

---

## 3. Uniwersum i rynki

### 3.1. Whitelista vs dynamiczne uniwersum
**Dane:** przecieki na nazwach spoza rdzenia (AMZN −$2.22, NDSN, LITE, DIS, UGI, TGT…) — dużo pojedynczych zamknięć 0% na „egzotyce" z newsów. Rdzeń (SPY/QQQ/mega-cap) wygląda zdrowiej.
**Rekomendacja:** dynamiczne uniwersum **dokłada przecieki** z płytkich, jednorazowych nazw. Rozważ **zawężenie**: albo wyłącz `dynamic_universe_enabled`, albo podnieś próg jakości nazwy z newsów. Najtańszy ruch: **wyrzuć powtarzalnych przegranych** (AMZN kandydat) do `symbol_blacklist`. Decyzja Twoja.

### 3.2. Wrócić do krypto / poza sesją?
**Fakt:** noga POZA SESJĄ (extended/24-7) świadomie **wyłączona** — jeden zdyscyplinowany silnik.
**Rekomendacja:** **nie wracać** przy tym kapitale. Poza sesją: cieńsza płynność, szersze spready, całe akcje (ułamek < 1 akcji nie wejdzie), więcej szumu i kosztu AI. Krypto 24/7 = jeszcze więcej cykli = jeszcze wyższy koszt tokenów względem kwot. Wróć do tematu dopiero > ~$10k, jeśli w ogóle.

### 3.3. Wybór benchmarku (SPY vs inne)
**Fakt:** whitelista jest **tech-heavy** (AAPL/MSFT/NVDA/META/GOOGL/AMZN/SMH), a benchmark to SPY.
**Rekomendacja:** SPY jest OK jako „czy bijesz zwykłe DCA", ale przy tech-tilt uczciwszym *drugim* odniesieniem jest **QQQ** (bardziej przypomina to, co bot faktycznie trzyma). Sugestia: pokazać **obie** krzywe (SPY już jest; QQQ jako opcja). Nie zmienia strategii, tylko rzetelność oceny alfy. (Krzywa vs SPY w czasie dodana w tej sesji — ekran Analiza.)

### 3.4. Lista defensywna w risk-off
**Fakt:** w risk-off silnik pozwala kupić tylko `GLD,TLT`.
**Rekomendacja:** GLD (złoto) + TLT (długie obligacje) to sensowny, klasyczny duet defensywny. Przy małym koncie **nie komplikować**. Ewentualny dodatek: nic — mniej znaczy lepiej. Zostaw.

---

## 4. Ryzyko, koszty, walidacja

### 4.1. Próg halt (obsunięcie 45%)
**Kontekst:** `max_drawdown_halt_pct=45` — podniesiony z 20 na bazie 20-letniego backtestu (naturalne obsunięcie tej agresji ~44%, więc 20% ucinałby handel w każdym normalnym zjeździe).
**Rekomendacja:** 45% jest **spójne z backtestem**, ale to **duża strata realnej kasy** psychologicznie. To ostateczny bezpiecznik na katastrofę, nie zarządzanie ryzykiem (to robią stopy per-trade). Jeśli Twoja tolerancja jest niższa niż „mogę zobaczyć −40% konta", obniż do **35%** świadomie akceptując więcej fałszywych haltów. Decyzja Twoja — to preferencja, nie błąd.

### 4.2. Ryzyko na transakcję (sufit 6%)
**Kontekst:** `conviction_max_risk_per_trade_pct=6.0` — twardy sufit: pojedyncza transakcja nie ryzykuje >6% konta na stopie, nawet przy sizingu przekonania 2×.
**Rekomendacja:** 6% na jedną transakcję to **agresywnie** (klasyka to 1–2%). Chroni przed blow-upem *jednej* pozycji, ale seria stopów boli. Skoro edge jest dodatni, rozważ **obniżenie do 4%** po audycie 1 września — mniej wariancji, wolniejszy, ale bezpieczniejszy wzrost. Nie zmieniać przed audytem (nie mieszać dwóch zmiennych naraz).

### 4.3. Budżet i koszt modelu AI
**Kontekst:** poll co 30 min, pełna analiza bramkowana wyzwalaczem, Sonnet. Budżet-kotwica $150/mies. (halt wyłączony — auto-doładowujesz).
**Ryzyko:** przy $600 koncie nawet **$15–30/mies. kosztu Claude to 2.5–5% konta/mies.** — to potrafi zjeść cały edge. To najcichszy przeciek.
**Rekomendacja:** **zmierz realny koszt** (licznik jest w apce) i policz jako % konta. Jeśli > ~3%/mies. → **wydłuż poll** (30→45–60 min) albo mocniej bramkuj wyzwalacz. Koszt AI to Twój największy „podatek" przy tym kapitale — pilnuj go jak stopa.

### 4.4. Walidacja paper przed live
**Fakt:** staging (paper) istnieje obok proda (deploy.sh buduje `app-staging`).
**Rekomendacja:** przyjmij **zasadę**: każda większa zmiana założeń (sizing, progi, uniwersum) najpierw **N dni na paper/staging**, potem live. Wyjątek świadomie zrobiłeś dla Scenariusza A („na moją odpowiedzialność") — ale to powinien być wyjątek, nie reguła. Tanie ubezpieczenie: nie testujesz hipotez realną kasą.

---

## Podsumowanie — co zrobić, w kolejności

1. **1 września: audyt Scenariusza A** (kryterium: $/trade i payoff w górę, drawdown nie w górę). ← kamień milowy
2. **Zmierz koszt Claude jako % konta** (4.3) — jeśli > 3%/mies., wydłuż poll. ← najcichszy przeciek
3. **Wyrzuć powtarzalnych przegranych** z uniwersum (AMZN i spółka, 3.1) — najtańsza poprawa edge.
4. **Po audycie** rozważ: risk/trade 6%→4% (4.2), progresywny krok 0.03→0.04 (2.3) — pojedynczo, nie naraz.
5. **Nie ruszaj:** min-hold 2 dni (działa, 2.2), defensywna GLD/TLT (3.4), krypto/poza-sesją OFF (3.2), Opus OFF do ~$8k (1.3).
6. **Zasada na przyszłość:** większe zmiany → najpierw paper (4.4).

**Nadrzędna prawda:** strategia ma dodatni edge; główne zagrożenia to **koszt AI** i **churn/egzotyka w uniwersum**, nie sam pomysł. Kapitał i dyscyplina kosztowa zrobią więcej niż kręcenie parametrami.
