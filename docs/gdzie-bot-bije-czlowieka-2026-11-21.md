# Gdzie bot bije człowieka — mapa przewag 24/7/365 (+ LLM) — 2026-11-21

> Zlecenie właściciela: „kop do końca; przeanalizuj, gdzie bot może mieć przewagę nad
> człowiekiem, nawet za cenę tokenów (LLM w grze). Bot ma działać 24/7/365 i bić człowieka
> — nieustannie dłubać, sprawdzać, słuchać i czytać." Tyle rekomendacji ile trzeba.

---

## 0. Fundament — twardy dowód z danych (przeczytaj najpierw)

Zanim powiem „gdzie bić", muszę powiedzieć „gdzie NIE da się bić", bo to przesądza resztę.
Przebadane na realnych świecach **1h z Binance, 2,8 roku (2024 hossa → 2025 mix → 2026 bessa),
7 majorów, 173 292 próbki**:

| Podejście | Wynik | Werdykt |
|---|---|---|
| Trend-following (obecny silnik) | backtest 3 lata: −22%, przegrywa z trzymaniem BTC, edge niespójny OOS | brak edge |
| Mean-reversion „łapanie dołków" | 930 transakcji, 52% trafności, **−0,21%/trade, suma −194%**, traci w KAŻDYM reżimie | brak edge |
| Forward-return najlepszego sygnału | +0,40% brutto @24h vs baza +0,06% → mikro-przewaga **zjadana przez koszty** | pod kreską netto |
| Momentum / wybicia | ≈ poziom bazy | zero |

**Wniosek, bez lukru: przewagi bota NIE ma w czytaniu wykresu.** Na poziomie samej ceny majory
są zbyt efektywne — i bot, i człowiek tak samo przegrywają z rynkiem. „+40% z 90 dni", które
mnie wcześniej uniosło, było mirażem jednego okna. Każda strategia czysto-cenowa, którą byśmy
wdrożyli, to szybsze generowanie przegranych niż robi to człowiek.

**Dlatego przewaga musi pochodzić z czegoś INNEGO niż cena.** I tu bot 24/7 + LLM faktycznie
bije człowieka — ale w trzech konkretnych obszarach, nie w „przewidywaniu kursu".

---

## 1. Trzy filary realnej przewagi bota nad człowiekiem

### Filar A — INFORMACJA (LLM + nieustanne czytanie/słuchanie)
Jedyne miejsce, gdzie „czyta i słucha non-stop" zamienia się w edge: **zanim cena wchłonie
informację.** Człowiek czyta 3 źródła i śpi 8h. Bot czyta setki feedów 24/7/365 i reaguje w
sekundy. To jest prawdziwy, strukturalny przewaga — i to tu warto palić tokeny.

### Filar B — DYSCYPLINA (brak emocji)
Człowiek przegrywa głównie psychologią: FOMO, panika, revenge-trading, trzymanie stratnych „z
nadziei". Bot nie ma emocji — przegrywa tylko złymi regułami. **To konto wysadził nie „nerwowy
bot", tylko za luźne limity.** Dyscyplina = NIE wysadzić się tam, gdzie człowiek się wysadza.
To przewaga defensywna, ale najpewniejsza ze wszystkich.

### Filar C — SZEROKOŚĆ + NIESTRUDZENIE
Monitoruje wszystko, wszędzie, zawsze — N aktywów × M sygnałów równolegle, o 3 w nocy i w
weekend. ALE: warte coś tylko sprzężone z Filarem A. Szerokie skanowanie samej CENY = szersze
generowanie szumu (udowodnione wyżej). Szerokie skanowanie INFORMACJI = realny zasięg.

---

## 2. Gdzie bot NIE ma przewagi (uczciwie, żeby nie gonić wiatraków)

- **Szybkość vs HFT / market-makerzy** — nie pobijemy ich na mikrosekundy; nie gramy w gry czysto latencyjne.
- **Insider / relacje / deep fundamental** — człowiek z siecią kontaktów i dostępem wie wcześniej.
- **Zużywanie się edge** — każda przewaga informacyjna jest arbitrażowana; trzeba ją ciągle odświeżać.
- **Backtest kłamie** — model sam siebie oszuka (patrz: mój miraż +40%). Walidacja OOS to nie formalność, to warunek.
- **„Przewidywanie" kursu** — udowodnione: nie da się z samej ceny. Nie wracamy tu.

---

## 3. REKOMENDACJE (priorytetyzowane; każda: edge · koszt · walidacja)

Oznaczenia: 🟢 silny/obroniony edge · 🟡 realny, ale sporny/cienki · 🔴 spekulacyjny (tylko po dowodzie).
Koszt: 💰 tokeny LLM · ⚙️ tylko kod · ⚠️ ryzyko handlu.

### GRUPA I — INFORMACJA / KATALIZATORY (Filar A — tu pali się tokeny z sensem)

**R1. 🟢 Instant de-risk na hack/exploit** 💰⚙️
Monitoruj feedy bezpieczeństwa (Rekt, PeckShield, protokolarne Twittery/statusy). Gdy protokół
trzymanej monety zostaje zhakowany — wyjście w sekundy. Człowiek widzi to po godzinach.
*Edge:* kontrola szkód, niemal zero fałszywych trafień kierunku (hack = zawsze zły). *Walidacja:*
historyczne przypadki (LUNA, FTX, Curve) — czy wyjście-w-sekundy ratuje X% vs wyjście-po-godzinie.
**Najmocniejsza rekomendacja w całym dokumencie — czysto defensywna, duży zwrot, małe ryzyko.**

**R2. 🟢 Kalendarz odblokowań tokenów (unlocks)** 💰⚙️
Duże odblokowania (vesting) = przewidywalna podaż → dołek. Dane z TokenUnlocks/kalendarzy.
Nie kupuj X dni przed dużym unlockiem trzymanej/kandydata; opcjonalnie redukuj.
*Edge:* unikanie przewidywalnych zrzutów. *Koszt:* niski. *Walidacja:* zwrot wokół dużych unlocków historycznie.

**R3. 🟡 Detektor listingów na dużych giełdach** 💰⚙️⚠️
Ogłoszenie listingu Binance/Coinbase pompuje monetę 20–50%. LLM monitoruje feedy ogłoszeń,
reaguje w sekundy. *Edge:* łapanie pompy listingowej. *Ryzyko:* insiderzy front-runują; edge
cienki i szybko gaśnie; łatwo kupić górkę. *Walidacja:* bezwzględna — ile z ostatnich 50 listingów
dało się złapać z zyskiem PO opóźnieniu reakcji i poślizgu.

**R4. 🟡 Monitor przepływów on-chain (whale / exchange flows)** 💰⚙️
Duże wpływy na giełdy (podaż, bearish) / wypływy (akumulacja, bullish), minty stablecoinów
(napływ płynności, bullish). API on-chain (Glassnode/Arkham/nansen-like). *Edge:* widzieć ruch
„mądrego kapitału" zanim trafi w cenę. *Ryzyko:* sygnał głośny, dużo szumu, drogie API. *Walidacja:* forward-return po dużych flow-eventach.

**R5. 🟡 Detektor kaskad likwidacji + ekstremów funding rate** ⚙️
Ekstremalny funding (przegrzane longi/shorty) i kaskady likwidacji = wymuszone ruchy. Dane z
perp-ów (Binance/Bybit funding + open interest). *Edge:* dane pozycjonowania, których człowiek
nie ogląda 24/7; kontrariańsko przy ekstremach. *Walidacja:* zwrot po skrajnym funding/likwidacjach.

**R6. 🟡 Tracker rotacji narracji** 💰
LLM czyta krypto-media + X 24/7 i wykrywa, która narracja się grzeje (AI, RWA, DePIN, memy),
rotuje ku liderom. *Edge:* rynek jest napędzany narracją; przewaga z SZEROKOŚCI czytania.
*Ryzyko:* narracje to też szum; spóźniony wjazd = kupno górki. *Walidacja:* czy „lider grzejącej narracji" bije koszyk OOS.

**R7. 🟡 Reakcja na makro/regulacje (FOMC, ETF, decyzje regulatora)** 💰
LLM parsuje kalendarz + newsy i przestawia risk-on/off szybciej/szerzej niż człowiek. *Edge:*
szybkość interpretacji zdarzeń o dużym wpływie. *Walidacja:* zachowanie wokół historycznych zdarzeń.

**R8. 🔴 Sygnał z aktywności dev/governance** 💰
GitHub commits, propozycje governance, roadmapy — wolny sygnał fundamentalny, LLM śledzi wiele
projektów naraz. *Edge:* fundamentalny, długi horyzont. *Status:* spekulacyjny — niski stosunek sygnału do szumu; tylko jako kontekst, nie wyzwalacz.

### GRUPA II — DYSCYPLINA / RYZYKO (Filar B — najpewniejszy edge, głównie już mamy)

**R9. 🟢 Twarde bezpieczniki anty-blowout** ⚙️ — ZROBIONE (10% koncentracja, 0.25× płynność, 5 wejść/dzień). To właśnie „nie wysadzić się tam, gdzie człowiek się wysadza".
**R10. 🟢 Reżimo-świadoma ekspozycja** ⚙️⚠️ — mniej/zero ekspozycji w bessie i wysokiej zmienności, więcej w POTWIERDZONEJ hossie. Bot trzyma to konsekwentnie, człowiek łamie pod emocjami.
**R11. 🟢 Mechaniczne cięcie strat, zero „trzymania z nadziei"** ⚙️ — mamy stopy; kluczowe, bo to #1 błąd człowieka.
**R12. 🟡 Dzienny budżet ryzyka w R + breaker serii strat** ⚙️ — stop po wyczerpaniu budżetu/serii.

### GRUPA III — POMIAR / SAMODOSKONALENIE (żeby edge nie zgnił po cichu)

**R13. 🟢 Atrybucja edge per-sygnał + auto-wyłączanie** ⚙️ — mierz wkład KAŻDEGO sygnału; gdy schodzi pod zero OOS, wyłącz automatycznie. Bot nie ma ego, by bronić przegranego sygnału.
**R14. 🟢 Monitor zużycia edge (edge-decay)** ⚙️ — ciągła re-walidacja OOS; alarm, gdy przewaga zanika.
**R15. 🟢 Shadow-test przed live** ⚙️ — mamy infrastrukturę (Claude-shadow); KAŻDY nowy sygnał najpierw w cieniu, dopiero po dowodzie na żywo.

### GRUPA IV — WALIDACJA (warunek wstępny każdej z powyższych)

**R16. 🟢 Bramka walk-forward OOS** ⚙️ — żaden sygnał nie idzie live bez dodatniej wartości oczekiwanej na wielu reżimach (dokładnie to, co dziś uratowało nas przed wdrożeniem mirażu +40%).

---

## 4. Twarda rekomendacja strategiczna (co bym zrobił)

1. **Przestań szukać edge w cenie.** Udowodnione na 173 tys. próbek: nie ma. Każda godzina i token
   wydane na „lepszy sygnał cenowy" to strata.
2. **Przekieruj 24/7 + LLM na INFORMACJĘ i DYSCYPLINĘ.** Tam bot realnie bije człowieka:
   - **Najpewniejsze i najpierw:** R1 (hack-exit) + R2 (unlocks) + utrzymać R9–R11 (dyscyplina).
     To przewaga DEFENSYWNA: „nie trać tam, gdzie człowiek traci". Nudne, ale to jedyne, co w danych działa.
   - **Potem, po walidacji:** R5 (likwidacje/funding), R4 (flows), R6 (narracje) — ofensywne, ale każde przez bramkę R16.
3. **Zaakceptuj uczciwą prawdę:** realna droga bota do bicia człowieka to w 70% UNIKANIE KATASTROF
   (dyscyplina + natychmiastowy de-risk na złą wiadomość) i w 30% kilka wysokopewnych katalizatorów
   (hacki, unlocki, duże flow) — a NIE generowanie alfy z wykresów.

**Pierwszy krok, który proponuję zbudować (za Twoją zgodą):** R1 — instant de-risk na hack/exploit.
Czysto defensywny, największy stosunek zwrotu do ryzyka, i dokładnie wykorzystuje „bot czyta i
słucha non-stop, człowiek śpi". Config-gated, walidowany na historycznych hackach, dopiero potem live.

---

*Metodologia: dane 1h Binance Vision 2024-01→2026-11, 7 majorów (BTC/ETH/SOL/LINK/AVAX/LTC/DOGE),
173 292 próbki forward-return; sim mean-reversion 930 transakcji po kosztach 0,15%/stronę. Wszystkie
liczby odtwarzalne. Backtest strategii: `audit/backtest-crypto.md` (gałąź audit-snapshots).*
