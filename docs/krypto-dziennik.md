# GielDarek krypto (paper) — kryteria wejścia na żywo + dziennik nauki

Cel: zebrać **uczciwe dowody** na papierze (sztuczny kapitał, 24/7, silnik
mechaniczny bez LLM), żeby decyzja o **realnej gotówce** była z danych, nie z emocji.
Start paper: **2026-10-04**.

## Twarde kryteria GO-LIVE (wszystkie muszą być spełnione)

Wchodzimy na żywo **tylko** gdy po oknie obserwacji **ŁĄCZNIE**:

1. **Próbka wystarczająca:** ≥ **50 zamkniętych** transakcji krypto **i** ≥ **3 tygodnie** handlu.
2. **Bije „trzymanie BTC":** skumulowany zwrot % strategii **>** buy-and-hold BTC
   w tym samym oknie. (To jest krypto-odpowiednik „bicia indeksu" — najważniejsze.)
3. **Dodatni edge:** expectancy/transakcję **> 0** (po fee) **i** trafność **powyżej
   progu opłacalności** dla osiągniętego payoffu.
4. **Obsunięcie do zniesienia:** max drawdown ≤ **25%**.
5. **Nie z 1–2 strzałów:** wynik nie jest dźwignięty przez kilka transakcji
   (sprawdzamy koncentrację — tak jak przy akcjach QQQ/SMH niosły cały tydzień).
6. **Koszt AI ≈ $0** (mechaniczny silnik — potwierdzamy, że tak zostaje).

**Nawet gdy wszystko zielone — wchodzimy MAŁO:** start na żywo ~$200–300, nie całość.
Skalujemy dopiero, gdy żywe wyniki potwierdzą paper (patrz analiza progów z 2026-10-01).

## Czerwone flagi — NIE wchodzimy (choćby reszta kusiła)
- Poniżej „trzymania BTC" w oknie. · Ujemny expectancy. · Drawdown > 30%.
- Próbka < 50 transakcji / < 3 tyg. · Wynik trzyma się na 1–2 szczęśliwych trejdach.

## Jak mierzymy (źródło prawdy)
Dane **wprost z brancha `audit-snapshots`** (zrzut co godzinę): `trades.json`
(filtr: venue=crypto / para z „/"), liczone average-cost walk — trafność, realized,
expectancy; benchmark = zwrot BTC w oknie. Niezależne od wielkości konta (paper $100k
czy realne $1k — te same %).

---

## Dziennik wniosków (tydzień po tygodniu)

> Dopisywany co tydzień przez nadzór. Najnowszy na górze.

### Wpis — 2026-10-18 (mniejsze, liczniejsze pozycje — z dala od limitu $200k)
Właściciel: „Rob" (zgoda na propozycję mniejszych pozycji). Przyczyna serii 403: na
koncie $1M pozycje po ~25% = ~$250k ocierały się o limit $200k/zlecenie Alpaki.
Zmiana (tylko krypto): `crypto_max_concurrent_positions` 4→7 (całe uniwersum — kapitał
rozkłada się drobniej, nie obraża się na żadną monetę), `crypto_max_position_pct` 40→20
(twardy sufit pary), nowy override `crypto_auto_deploy_max_position_pct=15` (cel
pojedynczego wejścia). Na $1M: ~$150k/pozycja, pułap $200k → zlecenia z buforem pod
limit; razem z pro-aktywnym clampem + reaktywnym retry (acc50be) 403 znikają u źródła.
Skala-niezależne (%): na $100k to $15k/pozycja. Akcje nietknięte. Backend 410/410, ruff ok.

### Wpis — 2026-10-18 (reaktywny guard limitu notional — koniec z 403 na wyjściach)
Mimo clampa z 88f7e2c wróciły 403 (wyjścia $203-204k > $200k). Przyczyna: pro-aktywny
clamp liczy rozmiar z `get_price`, która bywa rozjechana z wyceną Alpaki — qty wychodzi
odrobinę za duże. Fix: w `_submit_order` łapię dokładnie ten błąd (40310000), wyłuskuję
WŁASNY notional Alpaki z komunikatu i ponawiam RAZ, skalując rozmiar do min(limit, nasz
cap)×0.98. Bulletproof, bo opiera się na liczbie policzonej przez Alpakę, nie na naszej
cenie. Testy test_alpaca_notional_retry (+ nie ponawia innych 403). Backend 410/410, ruff ok.

### Wpis — 2026-10-14 (limit notional/zlecenie — Alpaca odrzuca > $200k)
Na nowym (większym) koncie % sizingu wygenerował zlecenie **$250k**, a Alpaca ma
twardy limit **$200k notional na pojedyncze zlecenie** (403 code 40310000) → zlecenie
odrzucone W CAŁOŚCI, kapitał nie wchodził. Fix: knob `max_order_notional_usd=190000`
(bufor pod limit) + clamp w `_execute_trade` na BUY **i** SELL — duże wejście/wyjście
dzieli się na kawałki ≤ limitu (auto-deploy i mechaniczne wyjścia dobijają resztę w
kolejnych cyklach; lepiej sprzedać część niż dostać 403 i nie sprzedać nic). Testy
test_order_notional_cap (BUY+SELL). Backend 405/405, ruff czysty.

### Wpis — 2026-10-14 (Podłącz konto Alpaca z panelu — bez dostępu do serwera)
Problem: reset lustra zadziałał (realized/budżet/peak=0, halt zdjęty), ale saldo
dalej ujemne (cash −$85k, equity −$64k), bo apka patrzy na STARE zdmuchnięte konto,
a Alpaca nie daje resetu konta właścicielowi. Podmiana kluczy w env wymaga serwera,
do którego nie ma dostępu. Rozwiązanie wykonalne z apki: endpoint + sekcja „Podłącz
konto Alpaca". Wklejasz klucze paper w panelu → serwer weryfikuje je u Alpaki
(odczyt salda), zapisuje jako runtime-owy override w SystemState, nakłada na
współdzielony singleton get_settings() (wszystkie AlpacaClient czytają ten obiekt →
przełączenie konta bez restartu), zdejmuje HALT i re-bazuje szczyt. Silniki zostają
w STOP (świadomy START). Override wczytywany też na starcie (przetrwa restart).
Bezpieczeństwo: konto paper; klucze NIE w repo; `serialize()` dostał listę
_SENSITIVE_COLUMNS i nie zwraca już ani override'ów, ani (naprawione) session_secret.
Backend 403/403, ruff czysty, front build OK. sw v65.

### Wpis — 2026-10-14 (bezpiecznik rozjechanego konta — halt KONTA, nie blacklista monet)
Dodany twardy guard w risk_manager.update_portfolio_value: gdy equity ≤ 0 (jak przy
blowoutcie −$61k), automat sam się HALTuje z jawnym powodem „Konto pod wodą … NIE
blacklista monet". To halt CAŁEGO konta — żadna moneta/indeks (BTC/ETH/alty) NIE jest
piętnowana; po resecie/zasileniu i ręcznym Wznów handel wraca na pełnym uniwersum.
Lepki (nie znika nowym dniem — to ubytek kapitału, nie okno kroczące). Cel: rozjechane
konto już nigdy samo nie ruszy. Auto-degradacja i auto-blacklist pozostają WYŁĄCZONE
dla krypto — uczymy się na wszystkim, nie obrażamy na żaden ticker. Test
test_underwater_account_trips_halt. Backend 399/399, ruff czysty.

### Wpis — 2026-10-14 (BLOWOUT + fix: konto na ujemnej gotówce, bezpiecznik zdusił)
Co się stało: konto zjechało na **cash −$117 597 / equity −$61 506**, bezpiecznik
dzienny strzelił (*„limit strat −174,6%"*) → `is_halted=true`, bot STANĄŁ. To NIE
były nowe straty z handlu (realized bez zmian −$13 950, day_realized=0) — to
**dźwigniowy blowout**: szybka rotacja 24/7 (force-trade, wejścia co 1-2 s;
$179k kupna/$190k sprzedaży w 2 dni na koncie ~$83k) + saldo Alpaki, które nie
nadążało księgować fillów → pętla auto-deploy czytała „gotówkę-widmo" i kupowała
ponad stan.
Fix (wybór właściciela: „napraw + wróć selekcję, potem halt"):
1. **Anty-lewar guard** w `_run_auto_deploy`: lokalny licznik NETTO wydanej gotówki
   w cyklu; po każdym zleceniu `cash = min(saldo_brokera, gotówka_startowa − netto)`.
   MINIMUM = zawsze konserwatywnie, opóźnione saldo nie pozwoli przepłacić.
   Regresja w `test_auto_deploy_clamps_spend_when_broker_cash_lags` (LaggingAlpaca).
2. **Koniec force-trade:** `crypto_entry_min_score` 0→1 — wejście wymaga ≥1 sygnału
   konfluencji, więc rotacja przestaje mielić wszystko (główny wzmacniacz blowoutu).
Backend 396/396, ruff czysty. UCZCIWIE: guard łapie wyścig WEWNĄTRZ cyklu (udowodniony
sub-sekundowymi wejściami); jeśli głębszą przyczyną jest margin/siła nabywcza paper-
konta Alpaki (fille na dźwigni mimo cienkiej gotówki), potrzebny będzie dodatkowo twardy
limit „tylko za realny cash" — do oceny, jeśli się powtórzy. Halt trzeba zdjąć ręcznie
w apce (Sterowanie), a konto na ujemnym equity najpewniej wymaga RESETU paper, bo
handel z −$61k equity nie ma sensu.

### Wpis — 2026-10-13 (mózg LLM ON na krypto — Claude co 8h czyta newsy+funding)
Diagnoza: `crypto_full_analysis_every_minutes=0` → noga krypto NIGDY nie odpalała
pełnej analizy Claude, więc krypto-newsy (CoinDesk/Cointelegraph/Decrypt…) i
funding/OI/long-short/F&G tylko SIĘ ZAPISYWAŁY, nie sterowały wejściami (silnik
czysto mechaniczny). Potwierdzone na żywo: tylko 2/107 decyzji krypto miało
news_snapshot, choć market_context 87/87. Wybór właściciela: włącz analizę co 8h,
ale ZOSTAW force-trade. Zmiana: `crypto_full_analysis_every_minutes` 0→480.
Heartbeat wymusza pełną analizę Claude (sonnet-5) ~3×/dzień — LLM realnie czyta
newsy+strukturę i decyduje wejścia; mechaniczny auto-deploy + stopy biegną 24/7
między wywołaniami. Koszt ~$5-6/mies (stawki sonnet $3/$15 za 1M tok.) — mieści się
w budżecie $9. `entry_min_score=0` i auto_deploy ZOSTAJĄ (Claude dokłada warstwę,
nie zastępuje mechaniki). Akcje nietknięte (full_analysis=0). ruff + testy profili
zielone. UCZCIWIE: brak dowodu, że warstwa LLM bije mechanikę — to eksperyment do
zmierzenia, nie pewniak; nadzór policzy, czy decyzje z analizy są lepsze niż force
mechaniczny. Reversible: ustaw 0.

### Wpis — 2026-10-12 (auto-blacklist OFF dla krypto — hamulec, który parkował kapitał)
Właściciel: „zdejmij blacklist". Auto-blacklist (3 stopy/24h → kwarantanna 48h) przy
force-trade churnie wypychał alty na 2 dni i parkował kapitał — niechciane w fazie
zbierania danych. Nowy knob `crypto_auto_blacklist_stop_count=0` + override →
auto_blacklist_stop_count. ZOSTAJĄ hamulce anty-whipsaw: 60-min cooldown po stopie
i 180-min reentry po pełnym wyjściu (ich właściciel nie zdejmował). Weryfikacja:
baza (akcje) =3 nietknięte, krypto efektywnie =0. ruff + testy profili zielone.
Reszta ochrony (stopy/cap/breaker/halt 30-40-55%) gra. Reversible: ustaw >0.

### Wpis — 2026-10-24 (WALK-FORWARD na realnych 10 latach — TWARDY WERDYKT)
Puszczony na runnerze (Yahoo, 10 lat, 7 par, 4 okna OOS). Dane dociągnięte (bez 403).

**Zbiorczo (z 14 mechanizmami, bez Claude):** zwrot +2486% vs BTC +3640% → **alfa
−1154%**, maxDD **28.6%** (BTC 83.4%), CAGR 38.5% vs BTC 43.7%, Calmar **1.35** vs BTC
0.52, lat bijących BTC **4/10**, trafność 46.7%, expectancy **0.745R**, 244 zamknięcia.
**Baseline (mechanizmy OFF):** zwrot +4066% (alfa +426%), ale maxDD 46.8%, 6374
zamknięć, expectancy 0.049R (≈0 — czysty churn/hazard).

**Walk-forward OOS (sedno #15):** pobiło BTC **1/4 okien**, mediana alfy **−21%**
(min −134%, max +226%), `edge_consistent=NIE`.
| okno | zwrot% | BTC% | alfa% | trafność% | Calmar |
|---|---|---|---|---|---|
| 2017-05→2019-09 | 145 | 279 | −134 | 55 | 1.26 |
| 2019-09→2022-02 | 638 | 412 | **+226** | 54 | 5.32 |
| 2022-02→2024-06 | 37 | 61 | −24 | 47 | 0.60 |
| 2024-06→2026-10 | 4 | 23 | −19 | **24** | 0.05 |

**WERDYKT (bez lukru):** cała przewaga zbiorcza wisi na JEDNYM oknie (altseason
2020-21, +226% alfy). W 3 z 4 okien — w tym w 2 NAJŚWIEŻSZYCH — lepiej było trzymać
BTC. Ostatnie 2.3 roku: trafność spadła do 24%, Calmar 0.05 (prawie martwy). To
DOKŁADNIE czerwona flaga GO-LIVE „nie z 1–2 strzałów" — zapalona wprost.
Co mechanizmy ROBIĄ dobrze: tną maxDD prawie o połowę (47%→29%) i podnoszą
expectancy 15× przy 26× mniej trejdów — czyli bronią kapitału i są spokojniejsze
(Calmar 1.35 > 0.52 BTC). Czego NIE robią: nie biją trzymania BTC na zwrocie i nie
robią tego spójnie. GO-LIVE = NIE. Uczciwa lekcja: mamy system OBRONNY (lepszy Calmar,
mniejsze obsunięcie), nie system z powtarzalną przewagą zwrotu nad samym BTC.
Sweep: najlepszy Calmar 1.35 @ ryzyko 3% × 6 pozycji (bez zmian — to już ustawienia).

### Wpis — 2026-10-23 (AUDYT kodu po planie — sprzątanie + efektywność)
Pełny audyt pod kątem „czy każda część służy nauce i zarabianiu". Wszystkie nowe
mechanizmy Partii 1–5 POTWIERDZONE jako podłączone do żywej nogi krypto (scheduler
`_crypto_job` → `run_cycle(effective_settings(...,'crypto'))` → skaner/wyjścia/
wejścia/sizing). Znalezione i NAPRAWIONE:
1. **Martwy knob `crypto_allocation_pct`** — `venue_allocation_room` czytał dla krypto
   stockowy `alpaca_allocation_pct` (ukryty coupling: zmiana dla akcji ruszałaby
   krypto). Dodany `_alloc_pct_for(settings, venue)` — każda noga ma SWÓJ udział.
   Oba 100% → zero zmiany zachowania dziś, usuwa pułapkę. (+ ten sam fix w dashboardzie.)
2. **Martwa funkcja `_other_venue`** (relikt 2-nogowej logiki, 0 wywołań) — usunięta.
3. **Sprzeczne komentarze „force-trade (entry_min_score=0)"** w 3 miejscach, gdy realnie
   `crypto_entry_min_score=2` (tryb jakości od wniosku #5). Zły log myli przyszłe
   decyzje = szkodzi nauce. Komentarze doprowadzone do stanu faktycznego.
4. **Skaner bez cache** — pobierał ~40 dziennych świec KAŻDY cykl (~96×/dobę) mimo że
   momentum 30-dniowe prawie się nie zmienia w 15 min. Dodany cache rankingu per
   sygnatura wejścia na `crypto_scanner_cache_min=60` min; trzymane/BTC domykane
   zawsze świeżo. Oszczędza grubo ~95% fetchy skanera i ryzyko limitów API.
5. **Stackowanie de-risku mogło zbić setup do pyłu** — mnożniki #4/5 (×0.5) × #12
   (×0.85^N) × #14 (×0.5) MNOŻĄ się; w pesymistycznym zbiegu ~6% docelowego rozmiaru
   = pozycja-śmieć (działa PRZECIW zarabianiu). Dodana PODŁOGA łącznego de-risku
   `crypto_entry_size_floor_frac=0.25` — potwierdzony setup nie schodzi poniżej 1/4 celu.
Testy: +1 (cache skanera), backend 436/436, ruff (app+tests) ok. Szczegóły i wnioski
strategiczne — w podsumowaniu sesji.

### Wpis — 2026-10-23 (Partia 5/5: PROCES — walidacja walk-forward / OOS)
Partia 5 (warstwa procesu/pomiaru), wniosek #15 — KONIEC planu 14 ulepszeń.
- **#15 Walk-forward / out-of-sample** (`app/services/walk_forward.py` +
  `run_backtest.py --walk-forward K`): tnie historię na K ROZŁĄCZNYCH okien OOS i
  puszcza przez każde TEN SAM mechaniczny silnik (te same, niestrojone pod okno
  knoby), każdy symbol z własnym rozbiegiem (warmup) przed oknem. Agreguje: w ilu
  oknach pobiliśmy BTC, mediana/min alfy, najgorsze obsunięcie, i werdykt
  `edge_consistent` (przewaga trzyma się, gdy bijemy benchmark w ≥60% okien i
  mediana alfy > 0). To bezpośrednio adresuje czerwoną flagę GO-LIVE „nie z 1–2
  szczęśliwych strzałów" i pytanie „bijemy BTC KONSEKWENTNIE, czy raz".
  Narzędzie POMIARU — nie zmienia żadnego knoba na żywo.
- Uruchomienie: `python scripts/run_backtest.py --venue crypto --years 10 --walk-forward 4`.
- UCZCIWIE: na gładkim syntetycznym teście trend-follower ze stopami ZARABIA, ale
  przegrywa z kupić-i-trzymać w monotonicznym wzroście (spodziewane — stopy tną w
  każdym cofnięciu). Realny werdykt policzymy na danych Yahoo (10 lat) w CI.
Testy: +5 (podział na okna, werdykt, odrzucenie <2 okien, za mało historii,
format raportu), backend 435/435, ruff (app+tests) ok.

**PLAN UKOŃCZONY**: 14/15 ulepszeń wdrożonych w 5 partiach (pominięte świadomie #5
„rdzeń BTC" — decyzja właściciela). Każda partia: osobny commit + testy + wpis.
Partie: 1=skaner 24/7 · 2=wyjścia (ATR/drabinka/czasowe) · 3=wejścia (multi-TF/weto
funding-F&G/teza) · 4=ryzyko (korelacja/vol-target/cool-off) · 5=proces (walk-forward).
Wszystko TYLKO noga krypto (przez `_CRYPTO_OVERRIDES`), akcje nietknięte. Następny krok
nadzoru: po deployu potwierdzić zrzutem, że skaner podstawia dynamiczne uniwersum, a
nowe wejścia niosą tezę; potem zebrać próbkę ≥50 zamknięć i policzyć kryteria GO-LIVE.

### Wpis — 2026-10-23 (Partia 4/5: RYZYKO — korelacja, vol-targeting, cool-off)
Partia 4 (warstwa sizingu/ryzyka), wnioski #12/#13/#14. Tylko noga krypto.
- **#12 Sizing wg korelacji** (`crypto_correlation_sizing_enabled`, mult 0.85): alty
  są mocno skorelowane z BTC — N longów alt to w praktyce JEDEN lewarowany zakład na
  BTC. Każda już otwarta pozycja zmniejsza rozmiar następnego wejścia (×0.85^N):
  1. pełna, 2. ×0.85, 3. ×0.72… Przycięte podłogą `volatility_min_scale`. Tłumi
  „all-in w jedną korelację" bez blokowania dywersyfikacji. Helper
  `_correlation_size_mult`, wpięty w `_buy_size_pct`.
- **#13 Volatility targeting** — POTWIERDZONE jako już obecne i otestowane:
  `volatility_adjusted_size` skaluje rozmiar ×(referencja/vol) dla nazw zmienniejszych
  od referencji (krypto ref 3%), z podłogą 0.35 — każda pozycja wnosi zbliżone ryzyko.
  To był wniosek „vol-targeting"; działa w torze sizingu BUY.
- **#14 Cool-off po stratnym dniu** (`crypto_cooloff_after_loss_day_pct=5`, mult 0.5):
  gdy WCZORAJ (UTC) zrealizowany wynik ≤ −5% konta, DZIŚ nowe wejścia idą ×0.5 —
  chłodzimy się po złym dniu zamiast odgrywać. Łagodniejsze od twardej pauzy: dane
  nadal płyną (nauka). Helpery `_yesterday_realized_usd` + `_cooloff_size_mult`,
  wpięte w `_buy_size_pct`.
Oba mnożniki (#12,#14) mnożą się z istniejącym de-riskiem zatłoczenia (#4/#5), więc
w euforii + po stratnym dniu + przy pełnym portfelu wejście jest naturalnie malutkie.
Testy: +4 (korelacja, cool-off, suma wczoraj, vol-targeting), backend 430/430, ruff ok.
Następne: 5=proces (walk-forward / shadow-validation).

### Wpis — 2026-10-23 (Partia 3/5: WEJŚCIA — multi-TF, weto funding/F&G, teza na trejd)
Partia 3 (warstwa wejść), wnioski #6/#7/#8. Tylko noga krypto, akcje nietknięte.
- **#6 Potwierdzenie wyższej ramy czasowej** (`crypto_mtf_confirm_enabled`, 4h/SMA50):
  nowe wejście wymaga, by RAMA NADRZĘDNA (4h) też była w trendzie wzrostowym (cena >
  SMA50_4h), nie tylko sygnał 1h. Odfiltrowuje łapanie spadającego noża — odbicia 1h
  wbrew trendowi 4h. Policzone raz/cykl per symbol (`_htf_trend_ok`), gate w
  `eligible_new`. Fail-open przy braku danych (nie zamraża bota).
- **#7 Twarde weto kontrariańskie funding/F&G** — POTWIERDZONE jako już obecne i
  sformalizowane: `_new_entries_blocked` przy ekstremalnej chciwości (F&G ≥ 93) LUB
  zatłoczonych longach (funding BTC ≥ 0.15%) WSTRZYMUJE nowe longi (twardziej niż
  soft de-risk ×0.5 przy 85/0.08%, który też zostaje). To kontrarianizm: nie gonimy
  euforii. Dodany test krypto (blokuje przy 95/0.2%, przepuszcza przy 55/0.01%).
- **#8 Teza na każdy trejd + weto LLM** (`_entry_thesis`): każde wejście auto-deploy
  dostaje 1-linijkowe UZASADNIENIE w reasoning (konfluencja + reasons + momentum +
  ADX + potwierdzenie 4h + reżim + F&G/funding) — ZERO kosztu LLM, log/dziennik ma
  „dlaczego", nie gołe „auto-deploy". Weto LLM i tak działa osobno: gdy
  `crypto_llm_enabled` ON, SELL Claude'a → `veto_sell` pomija wejście w ten symbol.
Testy: +3 (multi-TF gate, teza, weto kontrariańskie), backend 426/426, ruff ok.
Następne: 4=ryzyko (korelacja/vol-target/cool-off), 5=proces (walk-forward/shadow).

### Wpis — 2026-10-23 (Partia 2/5: WYJŚCIA — stopy ATR, drabinka TP, wyjście czasowe)
Partia 2 (warstwa wyjść), wnioski #9/#10/#11. Tylko noga krypto (przez
`_CRYPTO_OVERRIDES`), akcje nietknięte.
- **#9 Stopy ATR / vol-skalowane** — POTWIERDZONE, że już działają: `dynamic_stop_loss_pct`
  skaluje twardy stop zmiennością instrumentu (`stop_loss_vol_mult × vol%`, przycięte do
  min/max), więc stop siedzi POZA normalnym szumem (krypto: mult 4, 4–18%). To był wniosek
  „stopy ATR" — zrealizowany już wcześniej, teraz sformalizowany i otestowany jako intencja
  (zamiast przepisywać na true-range High/Low, co nic by nie dało przy samych closes). Brak
  vol (mało historii) → spada do stałego stopu. Test: vol rośnie → stop rośnie, clampy grają.
- **#10 Drabinka TP + runner** (`crypto_partial_take_profit_r_2=3.0`, `_frac_2=0.33`): drugi
  szczebel realizacji. Szczebel 1 przy 1.5R bierze 1/3; szczebel 2 przy 3R bierze kolejną 1/3
  z RESZTY; runner (~45% startowej) jedzie dalej pod trailingiem/ratchetem. Lockuje więcej
  zysku z mocnego trendu, zanim trailing odda część przy cofnięciu od szczytu. Każdy szczebel
  odpala RAZ (znacznik poziomu w stanie, wstecznie zgodny ze starym bool). Baza (akcje):
  frac_2=0 → jeden partial jak dotąd, zero regresji.
- **#11 Wyjście czasowe** (`crypto_time_exit_hours=72`, `_min_gain_pct=1.0`): pozycja trzymana
  > 72h, która nigdzie nie dotarła (zysk < +1%) to MARTWY KAPITAŁ — tnę, zwalniam gotówkę na
  coś, co realnie się rusza (sedno przewagi 24/7). Liczone na końcu, po wszystkich mocniejszych
  wyjściach (stop/trend/breakeven/TP/trailing/partial mają priorytet) i po min-hold. Wiek od
  początku CIĄGŁEGO trzymania (`position_opened_at`), więc dolewki nie resetują zegara. Baza:
  0h = wyłączone.
Testy: 8 nowych (drabinka jedn.+integracja, czasowe, ATR/vol dla krypto), backend 423/423,
ruff ok. Następne: 3=wejścia (multi-TF / weto funding+F&G / weto+teza LLM).

### Wpis — 2026-10-23 (Partia 1/5: SKANER rynku 24/7 — koniec sztywnej 7-tki)
Właściciel po pełnej analizie: „rdzeń BTC — nie rób (ogranicza naukę), resztę wdrażaj".
Wdrożona Partia 1 (warstwa uniwersum), wnioski #1/#2/#3/#4:
- **#1 Skaner 24/7** (`market_scanner.py` + `crypto_scanner_enabled`): co cykl skanuje
  CAŁĄ handlowalną listę par USD Alpaki (`list_crypto_symbols`), rankinguje po sile i
  oddaje TOP-K (domyślnie 8) jako DYNAMICZNE uniwersum silnika — zamiast obracać te same
  7 altów. To przewaga „ręka na pulsie 24/7": bot sam podstawia to, co realnie rośnie.
- **#2 Siła względem BTC** (`crypto_scanner_rs_vs_btc`): ranking po momentum MINUS momentum
  BTC (altseason-gate), nie po gołym zwrocie.
- **#3 Filtr płynności** (`crypto_scanner_min_dollar_vol_usd=5M`): odrzuca cienkie mikro-alty.
- **#4 Auto-degradacja WRACA z wysokim progiem** (`crypto_auto_demote_*`: enabled, 20 zamknięć)
  — paruj chronicznego przegranego po realnej próbce, nie po szumie z 5.
Separacja: skaner wybiera KANDYDATÓW; o wejściu dalej decydują bramki (reżim/konfluencja≥2/
wybicie/ADX) + cała ochrona ryzyka. Trzymane pozycje zawsze zostają w uniwersum (można wyjść).
Fail-safe: błąd/pusta lista → fallback na statyczne crypto_symbols. Akcje nietknięte.
Testy test_market_scanner (5), backend 415/415, ruff ok. Kolejne partie: 2=wyjścia (ATR/
drabinka/czasowe), 3=wejścia (multi-TF/weto funding/weto+teza LLM), 4=ryzyko (korelacja/
vol-target/cool-off), 5=proces (walk-forward/shadow).

### Wpis — 2026-10-19 (5 wniosków z Tyg.2 WDROŻONE — powrót do jakości)
Właściciel: „wdrażaj wszystko" (po 5-punktowej analizie 0W/9L). Zmiany (tylko krypto,
akcje nietknięte):
- **#1 Filtr reżimu ON** (`crypto_regime_filter_enabled=True`, BTC vs MA100/1d) — brak
  nowych longów, gdy BTC pod średnią. To była przyczyna nr 1 strat (longi w risk-off).
- **#2 Anty-whipsaw** (`crypto_reentry_cooldown_min` 180→1440 = 24h) — koniec pętli
  kup→stop→odkup ten sam alt w godziny.
- **#3 Lock zysku wcześniej** (`crypto_ratchet_trigger_pct` 15→8) — wygrany od +8%
  zaciska trailing, żeby nie zawrócił do straty (asymetria payoffu).
- **#4 Cap korelacji** (`crypto_max_total_exposure_pct` 60→50) — mniej „all-in" w 6
  skorelowanych altów, więcej gotówki.
- **#5 Selektywność** (`crypto_entry_min_score` 1→2, `breakout_entry_enabled` ON,
  `breakout_lookback` 10→20, `min_adx` 0→20) — wejście tylko na ≥2/3 konfluencji +
  realnym wybiciu + sile trendu; koniec handlu szumem. (Weto „down-tape" realizuje #1.)
Efekt: to świadome odwrócenie force-trade na JAKOŚĆ. Mniej, lepszych wejść; sits-out
w zjeździe. Reversible. Backend 410/410, ruff ok. Walidacja: backtest krypto na realnych
danych (dispatch crypto-backtest.yml) — wynik dopiszę. UWAGA: to zmiana na próbce <50,
ale wyraźny wybór właściciela po jednoznacznym wzorcu 0W/9L i pod konkretne przyczyny.

### Tydzień 2 — 2026-10-18 (nowa era: konto paper $1M od 10-14, build e9952d4)
Reset + nowe konto paper ($1M) 10-14; licznik od zera. Dane: trades.json, avg-cost walk.
- **Zamknięcia: 9 | trafność 0% (0W/9L) | realized −7,9% konta (−$79k) | total −8,6%.**
- Każde zamknięcie stratne, −1,7% do −6,7% (śr. ~−5%/trejd). vs BTC: BTC kupiony i
  **trzymany** — jedyna nie-stratna pozycja; wszystko, czym bot obracał, straciło →
  strategia głęboko PONIŻEJ „trzymania BTC".
- **Koncentracja:** strata rozłożona równo na 6 altów (SOL ~−$19k najgorszy, dalej
  ETH/DOGE/AVAX/LTC/LINK ~−$10-13k) — systematyczna, nie 1-2 pechowe trejdy.
- **Drawdown −9,6%** od szczytu (próg 25/30/55% — jeszcze nie złamany, ale rośnie).
- **Kontekst:** cały tydzień risk-off (S&P −1,95%, regime „neutral", krypto szeroko
  w dół) — więc część to rynek, nie sama strategia.
- **GO-LIVE:** złamane — poniżej BTC ✗, expectancy<0 ✗, trafność 0% ✗; drawdown 9,6%<25% ✓
  (jeszcze), próbka 9<50 i <3 tyg ✗. **Werdykt: pogarsza się.**
- **Wzorzec do obserwacji (nie dostrajam — próbka za mała):** kupno altu → stop niżej →
  odkupienie TEGO SAMEGO altu. Jeśli po ~50 trejdach trafność zostanie przy ~0, to
  twardy sygnał, by wrócić selekcję/auto-degradację z wyższym progiem. Techniczne
  bramki bezpieczeństwa działają (403 limitu Alpaki rozwiązane: clamp + retry + mniejsze
  pozycje; anty-lewar; bezpiecznik konta). Nauka: pętla zbiera dane, LLM czyta newsy co 8h.

### Tydzień 1 — 2026-10-12 (start paper 2026-10-04, snapshot build 800d3ce)
Dane: branch `audit-snapshots`, trades.json (filtr krypto), average-cost walk.
- **Zamknięcia:** 61 | **trafność 28% (17W/44L)** | **realized −$9 382** | **expectancy −$154/trejd**.
- **Payoff BRUTALNIE asymetryczny:** avg win **$3**, avg loss **−$214**. To sygnatura churnu —
  wyjścia nie bankują nic na wygranych, a biorą pełne stopy na stratnych.
- **vs BTC:** strategia głęboko PONIŻEJ trzymania BTC (BTC w oknie ~płasko, −$17 na 1 zamkn.;
  strategia −$9,4k). Kryterium „bić BTC" — **ZŁAMANE**.
- **Koncentracja:** straty rozłożone na wiele trejdów (nie 1-2), gros z churnu AVAX/LTC/SOL
  6-7.10. Każdy alt na minusie: AVAX −$2,4k, LTC −$2,3k, LINK −$1,5k, DOGE −$1,4k, SOL −$1,2k, ETH −$0,6k.
- **Drawdown:** konto $88,1k vs szczyt $99,8k = **−11,7%** (w granicy 25%, ale trend zły).
- **Silnik:** żywy (crypto_paused=false, nie zhaltowany), paper=true, koszt AI ≈$0 (mechaniczny).
  Po wyłączeniu auto-degradacji (11.10 17:10) kapitał RUSZYŁ: crypto $21,7k→$71,7k, gotówka
  $66k→$16k (81% rozmieszczone); 3 nowe wejścia AVAX/LINK/SOL — jeszcze otwarte (unreal. +$343).

**Werdykt: pogarsza się wg kryteriów GO-LIVE (poniżej BTC, ujemny expectancy).** ALE to świadoma
faza force-trade/zbierania danych wybrana przez właściciela — NIE werdykt o „docelowej" strategii.
Kryteria GO-LIVE: próbka 61 zamkn. ✓ ale <3 tyg. ✗ · bić BTC ✗ · expectancy>0 ✗ · DD≤25% ✓ ·
nie z 1-2 trejdów ✓ · koszt AI≈$0 ✓. Największa lekcja do obserwacji: **asymetria payoffu** (win $3
/ loss −$214) — jeśli po setce uczciwych trejdów się utrzyma, to sygnał że mechaniczne wyjścia
tną zyski za wcześnie, a nie że „alty są złe". Bez zmian knobów (zgodnie z regułą nadzoru).

### Wpis — 2026-10-11 (auto-degradacja OFF dla krypto — ostatnia bramka force-trade)
Diagnoza z żywych decyzji: **83/87** nowych wejść krypto odrzucała JEDNA bramka —
auto-degradacja. Na prodzie była włączona (env) i zbanowała **6/7 uniwersum**:
LTC 0W/5L (−$2 334), LINK, AVAX, DOGE, ETH 1W/4L (−$600), SOL. Jedyny dozwolony =
BTC (już trzymany) → force-trade nie miał gdzie wejść, kapitał stał, w kółko
„nowe wejście zablokowane". Wyrok zapadł na ~5 trejdach z fazy churnu — czyli
dokładnie „mała próbka", na której NIE wyciągamy wniosków. Właściciel wybrał:
„wyłącz dla krypto, force-trade naprawdę wszystko". Nowy knob
`crypto_auto_demote_enabled=False` (override → auto_demote_enabled). Noga akcji
nietknięta (baza dalej wg env). Reszta ochrony (stopy/cooldown/breaker/cap/halt)
działa. UCZCIWIE: świadomy powrót do przegranych alt-ów pod zbieranie danych, nie
pod zysk. Backend 118/118 (profile+silnik), ruff ok. Reversible jednym knobem.

### Wpis — 2026-10-11 (NAUKA — self-review widzi WARUNKI RYNKU, nie tylko „co kupił")
Właściciel: „nauka nauka nauka". Audyt pętli uczenia na żywym stanie:
- Pipeline JEST kompletny i **dzienny** (nie tygodniowy): każde wejście/wyjście —
  także mechaniczne (auto-deploy, bez LLM) — zapisuje `reasoning` **oraz**
  `market_context_snapshot`; self-review co dzień destyluje 3-5 lekcji → `lessons_json`
  (cap 30) → wraca do kontekstu KAŻDEJ decyzji. Potwierdzone: **87/87** decyzji krypto
  ma wypełniony kontekst (funding BTC, OI 24h, long/short, Fear&Greed).
- **Luka:** destylacja czytała tylko `reasoning` i IGNOROWAŁA ten kontekst → lekcje
  płytkie („unikaj DOGE") zamiast przyczynowych. Surowiec był logowany i marnowany.
- **Fix (ta zmiana):** `_market_ctx_tag()` dokleja do każdej transakcji w prompcie
  warunki rynku `[F&G 61, funding -0,002%, L/S 1,45, OI24h +0,33%]`, a instrukcja
  każe szukać ZALEŻNOŚCI (przy jakich warunkach wejścia zarabiały/się sypały).
  Efekt: lekcje przyczynowe → przyszły Sonnet startuje „naładowany", nie na zero.
- To NIE jest knob strategii (zero wpływu na handel) — czysta jakość nauki. 395/395, ruff ok.
- UCZCIWIE o paliwie: 70 trejdów/7 dni, ale gros to churn AVAX z 10-07 (krwawienie
  na rundach) + 1 BUY BTC 10-09 i ~2 dni ciszy. Force-trade wszedł na żywo dopiero
  dziś 11:06Z — dopiero on wygeneruje gęstsze dane do tej lepszej destylacji.

### Wpis — 2026-10-11 (FORCE-TRADE — próg konfluencji krypto = 0)
Właściciel: „force-trade wszystko, akceptuję churn" (rynek boczny, kapitał stał).
crypto_entry_min_score=0 → auto-deploy ZAWSZE rozmieszcza gotówkę w najlepiej-
rankowany setup, nawet słaby. Razem z reżim/wybicie/ADX OFF + ryzyko 3%×4 =
maks. aktywność. UCZCIWIE: to świadomy powrót do churnu (per-symbol: małe alty
LTC/DOGE/AVAX/LINK/SOL to krwawce) — cena za zbieranie danych/naukę, NIE pod
bicie BTC. Ochrona (stopy/trend-exit/cooldown/breaker/cap/halt 30-40-55%) gra.
Reversible. Nadzór policzy pierwsze realne zamknięcia nowej, agresywnej konfig.

### Wpis — 2026-10-11 (bramki wejścia OFF — kapitał ma pracować na 24/7)
Mimo poluzowania (10-08) kapitał dalej stał w 100% gotówce dniami — na rynku
24/7 to bez sensu, a cel paperu to ZBIERAĆ DANE. Właściciel: „krypto to 24/7,
nic się nie da handlować? luzuj". Wyłączone dwie najtwardsze bramki wejścia +
ADX (wyraźna prośba):
- `crypto_regime_filter_enabled → False` (reżim HTF był ścianą),
- `crypto_breakout_entry_enabled → False` (wymóg nowego maksimum rzadko trafiał),
- `crypto_min_adx → 0` (ADX blokował w płaskim rynku).
Wejścia napędza teraz KONFLUENCJA (RSI/MACD/SMA, entry_min_score) + auto-deploy.
CAŁA ochrona ryzyka działa dalej: stopy vol, hartowany trend-exit, cooldown,
breaker serii strat, cap ekspozycji, bezpiecznik konta 30/40/55%. UCZCIWIE:
to powrót do wyższej rotacji (bliżej baseline'u z backtestu) — więcej wejść,
niższa jakość/trejd; świadomie, pod naukę. Reversible knobami. Obserwujemy, czy
ruszył handel.

### Wpis — 2026-10-08 (poluzowanie bramek wejścia — „bot ma się uczyć")
Nadzór pokazał: od wdrożenia 10 mechanizmów bot NIE zawarł ani jednej nowej
transakcji (konto płaskie, 100% gotówki) — nowe bramki (reżim HTF + wybicie +
ADX) w płaskim rynku są zbyt restrykcyjne. Na paperze cel to ZBIERAĆ DANE do
nauki, więc właściciel kazał poluzować. Zmiany (wyraźna prośba):
- `crypto_regime_filter_ma_period 200→100` (risk-on łapie szybciej),
- `crypto_breakout_lookback 20→10` (więcej wybić się kwalifikuje),
- `crypto_min_adx 20→12` (wpuszcza słabsze trendy).
UCZCIWIE: luźniej = WIĘCEJ wejść, ale NIŻSZA jakość/trejd (bliżej churnu z
backtestu). To świadomy kompromis pod naukę, nie pod „bić BTC". Reżim/stopy/
breaker dalej działają; wszystko reversible. Obserwujemy, czy wejścia ruszyły.

### Wpis — 2026-10-08 (strojenie ekspozycji: 1,5%×5 → 3,0%×4, decyzja z backtestu)
Backtest + sweep na 8 latach realnych danych (Yahoo, z runnera GitHub) pokazał,
że przy 10 mechanizmach bramki trzymają bota w gotówce → **1,5%×5 było
niedoinwestowane i przegrywało z trzymaniem BTC** (alpha ujemna). Frontiera
ryzyko/trejd × pozycje:
- 1,5%×5 (poprzednie): ~+550%, DD ~30%, **przegrywa z BTC**.
- 3,0%×4 (**wybrane, „agresywnie"**): +2713%, CAGR 51,8%, **Calmar 1,42**,
  alpha **+1363pp** vs BTC, DD ~37% (BTC: 77%).
Zmiana knoba `crypto_risk_per_trade_pct 1.5→3.0`, `crypto_max_concurrent_positions
5→4` (wyraźna zgoda właściciela). UCZCIWIE: backtest bez prowizji/slippage,
dzienny, 8-letni; 3% ryzyka/trejd to agresywnie (większe pojedyncze straty,
grubsze wahania na żywo). Bezpiecznik account-wide (30/40/55%) dalej chroni.
Obserwujemy żywy paper — werdykt dopiero na ≥50 zamknięciach / ~3 tyg.

### Wpis — 2026-10-07 (10/10 mechanizmów — dołożone wejścia #8/#9/#10)
Na prośbę właściciela („wszystko") dołożone 3 pozostałe (strona WEJŚĆ), po
doprowadzeniu świec OHLC do ścieżki wejścia (dotąd closes-only):
8. **Wejście na WYBICIE (Donchian 20)** — kup tylko gdy cena bije szczyt poprzednich 20 świec.
9. **Filtr siły trendu (ADX14 ≥ 20)** — wchodź tylko gdy trend realnie istnieje; pomija boki.
10. **Piramidowanie** — dokładka do WYGRYWAJĄCEGO (+8%) na nowym wybiciu, sufit 25% konta,
    nigdy do straty; zwolnione z limitu równoległych pozycji (dokładka ≠ nowy slot).
Nowe wskaźniki ADX (Wilder) i Donchian w `technical_indicators`; H/L pobierane z 200-świec.
⚠️ To strona WEJŚĆ — napięcie z lekcją „nie filtruj wejść restrykcyjnie". Wdrożone
świadomie na życzenie, każdy za knobem (wyłączalny), ale WARTO zwalidować backtestem na
prodzie, zanim uznamy je za poprawę. Testy 392/392, ruff czysty. 10/10 config-gated.

### Wpis — 2026-10-07 (10 mechanizmów podnoszących P(zysk), wdrożone 6/10)
Na prośbę właściciela („wszystkie") dołożone mechanizmy podnoszące
prawdopodobieństwo zysku, każdy za osobnym knobem (można wyłączyć przez `.env`;
akcje nietknięte — knoby bazowe off). **Wdrożone teraz (6):**
1. **Filtr reżimu HTF** — longi tylko gdy BTC nad SMA200 na D1; w chopie/bessie gotówka.
2. **Re-entry cooldown** — po KAŻDYM pełnym wyjściu blokada ponownego wejścia (180 min) — anty-churn.
3. **Trailing skalowany zmiennością** — podłoga trailingu = max(bazowy, 1.5×vol%); mniej wyrzutów na szumie.
4. **Cap ekspozycji** — brak nowych wejść przy ≥60% konta w grze (krypto skorelowane → „wszystko czerwone").
5. **Breaker serii strat** — 4 straty z rzędu dziś → pauza nowych wejść do rolki doby UTC.
7. **Pauza na przegrzaniu** — F&G ≥93 lub funding ≥0.15% → wstrzymanie nowych longów (twardziej niż de-risk).

**Czeka na backtest na prodzie (3):** #8 Donchian breakout, #9 ADX-gate, #10 piramidowanie —
wymagają świec OHLC w ścieżce wejścia (dziś tylko closes) i nie wrzucamy ich na ślepo.
#6 vol-targeting sizingu ~pokryte przez `volatility_adjusted_size`.
Uczciwie: 6 mechanizmów naraz = konfundowanie (nie odróżnimy per-mechanizm na małej
próbie). Dlatego config-gated — obserwujemy, czy churn/„wszystko czerwone" znika; w razie
czego wyłączamy pojedynczo. Testy 389/389, ruff czysty.

### Wpis interwencyjny — 2026-10-07 (diagnoza + fix trend-exitu)
Dane (venue=crypto, okno 2026-10-04 → 10-07, zrzut 14:22Z): **32 zamknięcia,
realized −$9 376, trafność 12% (4/28), expectancy −$293/trade**, śr. wygrana
**+0,34%** vs strata **−1,73%** (payoff 0.03×), mediana trzymania **3,9h**,
każda para na minusie. BTC w oknie ≈ **−1%** → aktywny handel **grubo przegrywa**
z trzymaniem BTC. Silnik żył (nie-halt, nie-paused), konto $87,8k, drawdown ~12%.

**Diagnoza (read-only):** winowajca to **trend-exit (SMA50 na 1h, bez bufora i
potwierdzenia)**. Sprawdzany co 15 min, pali się na pojedynczy tick pod średnią;
w płaskim rynku cena bez przerwy przecina SMA50 → zwycięzcy ścinani przy ~0%,
straty jadą do ~−1,7%, churn 32×/3 dni. To klasyczna porażka trend-followingu na
rynku **bocznym**, wzmocniona zbyt czułym exitem (jedno z „5 ulepszeń", dec6c2e).
Mechanika „pozwól zyskom biec" (breakeven 8% / ratchet 15% / hard-TP 40%) nigdy
nie dochodziła do głosu — trend-exit zamykał wcześniej.

**Fix (za zgodą właściciela „wdrażaj daleko"):** HARTOWANIE trend-exitu, zgodnie
z udokumentowaną lekcją „nie dokładać filtrów WEJŚĆ" — ruszamy tylko WYJŚCIE:
- bufor `crypto_trend_exit_buffer_pct=3%` (wyjście dopiero 3% pod średnią, nie tick),
- potwierdzenie `crypto_trend_exit_confirm_bars=2` (2 świece zamknięte pod średnią).
Reszta strategii bez zmian; knoby bazowe neutralne (akcje nietknięte). Próbka 3 dni
jest za mała na strojenie pod wynik, ale to usunięcie strukturalnie twitchy exitu,
nie curve-fit. Obserwujemy, czy payoff i trafność wracają do sensownych wartości.

### Tydzień 0 — start (2026-10-04)
- Paper włączony, konto $100k (sztuczne), silnik mechaniczny, LLM off.
- Zero transakcji jeszcze — zbieramy próbkę. Pierwszy realny wniosek po ~7 dniach.
