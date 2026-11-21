# Kraken — pełna analiza oferty + nasze knoby/strategia + opcje — 2026-11-21

> Zlecenie: „pełna analiza Krakena, wszystkiego co oferuje, i naszych knobów i strategii —
> przygotuj analizę i opcje." Dane: rekonesans konta przez API (saldo €23,81, wszystkie 7
> par EUR dostępne) + świeży research oferty. Konto zweryfikowane, klucz działa (Query Funds).

---

## 1. Co Kraken realnie oferuje dla Ciebie (Polska/UE)

| Produkt | Dostępność PL/UE | Dźwignia | Short? | Licencja | API | Dla nas |
|---|---|---|---|---|---|---|
| **Spot** | ✅ mamy, €23,81 | 1x | ❌ | MiCA (Irlandia) | REST/WS/FIX, ten sam klucz | **baza** |
| **Spot Margin** | ✅ eligible po ocenie | ~**5x** | ✅ **TAK** | MiCA spot | **ten sam klucz co spot** | short lekko |
| **Futures (perps)** | ✅ retail po „appropriateness" | do **10x** | ✅ **TAK** | MiFID II (CySEC) | OSOBNA platforma + klucz | short mocno |
| Staking / xStocks | ✅ | — | — | — | — | poboczne |

**Pary naszego uniwersum na Kraken (EUR), z mapowaniem nazw dla adaptera:**
BTC→`XXBTZEUR` (min 0.00006) · ETH→`XETHZEUR` (0.002) · SOL→`SOLEUR` (0.05) ·
LINK→`LINKEUR` (0.35) · AVAX→`AVAXEUR` (0.5) · LTC→`XLTCZEUR` (0.08) · DOGE→`XDGEUR` (50).
Min. zlecenia są małe — €24 wystarcza na kilka realnych mikro-trejdów.

**Opłaty (zweryfikuj na stronie, źródła się różnią):** spot Pro ~0,25% maker / 0,40% taker
(spada z wolumenem, do 0,16/0,26%). Margin: ~0,01–0,02% otwarcie + 0,02% rollover co 4h +
**2% kara przy przymusowej likwidacji**. Futures EEA: **30 dni bez opłat** dla nowych.

**Ważne zastrzeżenie regulacyjne:** ESMA sygnalizuje, że perpetual futures mogą być
zaklasyfikowane jako CFD w UE — to może zmienić dostępność/zasady futures. Margin spot jest
pod tym względem pewniejszy (pod MiCA).

---

## 2. Nasza strategia i knoby — stan na dziś (uczciwie)

**Silnik:** mechaniczny trend-following na krypto (LLM off w handlu), spot **long-only**.
**Udowodnione na 173k próbek / 930 transakcji / 2,8 roku:**
- Trend-following: −22% / 3 lata, przegrywa z trzymaniem BTC.
- Mean-reversion („łapanie dołków"): −194% / 930 trade, traci w KAŻDYM reżimie.
- **Wniosek: ZERO edge w cenie. Spot long-only NIE MOŻE zarabiać w bessie** (nie ma short).

**Aktualne knoby krypto (po zmianach z tej sesji):**
| Knob | Wartość | Po co |
|---|---|---|
| `mechanical_entries_enabled` | **True** | wejścia na potwierdzonej mechanice, nie na pewności Claude |
| `crypto_btc_core_mode` | **False** | alty odblokowane (Twoja zgoda) |
| `crypto_max_position_pct` | **10%** | anty-blowout: jedna moneta ≤10% konta |
| `crypto_max_order_vs_dollar_vol_mult` | **0.25** | anty-blowout: zlecenie ≤25% dziennego obrotu |
| `crypto_max_new_positions_per_day` | **5** | hamulec tempa |
| `crypto_regime_filter_enabled` | False | (luzowane wcześniej) |
| `crypto_entry_min_score` / `min_buy_confidence` | 2 / 0.60 | próg konfluencji / pewności |
| `crypto_event_response_enabled` | **False** (zbudowane) | tor katalizatorów (hack-exit), shadow-first |

**Zbudowane w tej sesji (Filar INFORMACJA, config-gated OFF):** rdzeń reakcji na katalizatory
(hack→de-risk, unlock→blokada, listing→alert) + parser feedu DeFiLlama. To realizacja wniosku,
że **edge jest w informacji i dyscyplinie, nie w cenie.**

---

## 3. OPCJE (do Twojej decyzji) — każda: co daje · ryzyko · co wymaga

### Opcja A — Spot-only na Kraken (zachowawcza) 🟢 ryzyko niskie
Port silnika na Kraken spot EUR, zostaje long-only + moduły info/dyscyplina.
- **Daje:** prostotę, zero dźwigni, NIE da się wysadzić konta. Ochrona kapitału + rzadkie katalizatory.
- **Nie daje:** zysku w bessie (udowodnione). W spadku siedzi w gotówce/EUR.
- **Wymaga:** adapter Kraken spot (mapowanie par, EUR, podpis API). ~główna robota inżynierska.

### Opcja B — Spot + Margin short (umiarkowana) 🟡 ryzyko średnie
Dodajemy SHORT przez margin Kraken (dostępne ~5x, ale używamy **1–2x max**).
- **Daje:** odblokowuje zysk w bessie — jedyny sposób zarobić, gdy rynek spada. Lżejsze niż futures, ten sam klucz API.
- **Ryzyko:** dźwignia = likwidacja (+2% kara), short squeeze, koszt rollover co 4h. I — brutalnie — **nie mamy udowodnionego edge ani po long, ani po short**; shortowanie trendu ma ten sam problem „brak edge w cenie", chyba że jest napędzane KATALIZATOREM/reżimem, nie predykcją.
- **Wymaga:** logika short + twarde limity (mały lewar, stop, limit ekspozycji) + WALIDACJA OOS short-strategii. Bez dowodu nie włączam.

### Opcja C — Futures (agresywna) 🔴 ryzyko wysokie
Kraken EU perps, do 10x, osobna platforma/API.
- **Daje:** najwięcej elastyczności (long/short, dźwignia, płynność, 30 dni bez opłat).
- **Ryzyko:** **NAJWYŻSZE ryzyko blowoutu — a to konto już raz się wysadziło.** Osobna integracja, niepewność ESMA (CFD), ocena „appropriateness". 10x na zmiennym krypto to droga do zera.
- **Wymaga:** osobny adapter futures + rygor ryzyka na sterydach. **Odradzam jako start.**

### Opcja D — Informacja-first, short tylko jako OBRONA (moja rekomendacja) 🟢→🟡
Niezależnie od instrumentu: udowodniony edge to INFORMACJA + DYSCYPLINA, nie kierunek ceny.
- Baza: **Opcja A (spot na Kraken)** + dokończyć moduły katalizatorów (hack-exit, unlocki), zwalidować.
- Short dodajemy **wyłącznie** jako: (a) **hedge** trzymanej pozycji napędzany katalizatorem (hack/zła wiadomość → zshort/wyjście), albo (b) jeśli ZWALIDUJEMY short-edge OOS (czego jeszcze nie mamy). Margin 1x, zero spekulacyjnej dźwigni.
- **Daje:** realną przewagę tam, gdzie jest (info/dyscyplina), bez kopiowania błędu, który wysadził konto.
- **NIE robię:** futures-dźwigni „żeby zarabiać w bessie" na niezwalidowanej predykcji.

---

## 4. Rekomendacja i kolejność

1. **Teraz:** Opcja A — adapter Kraken spot EUR (brama realnej gotówki; i tak potrzebny w każdej opcji). Równolegle: dokończyć moduły katalizatorów + panel „bot czyta 24/7".
2. **Po walidacji:** rozważyć short JAKO HEDGE (Opcja D) — margin 1x, napędzany katalizatorem, nie predykcją.
3. **Futures (C):** dopiero gdyby short-edge został TWARDO udowodniony OOS i z groszowym lewarem — na razie NIE.

**Twarda prawda, żeby decyzja była świadoma:** żaden instrument nie tworzy edge z niczego. Futures
nie sprawią, że bot zacznie przewidywać cenę — dadzą tylko większą dźwignię na strategię, która
nie ma przewagi (czyli szybszą drogę do zera). Short MA sens, ale jako narzędzie RYZYKA/hedge
napędzane informacją, nie jako maszynka do zgadywania spadków. Pieniądze zrobi (jeśli w ogóle)
dyscyplina + reakcja na katalizatory, nie dźwignia.

**Powiedz, którą opcją idziemy (A / B / C / D), a ja dobieram do tego adapter i knoby.**

---
*Źródła oferty Kraken: strony Kraken (fees/API/EU), recenzje 2026, CASP/MiCA tracker. Liczby opłat
i dźwigni różnią się między źródłami — do potwierdzenia na koncie Kraken przed realnym handlem.
Dane konta: rekonesans przez API (Balance/TradeBalance/AssetPairs).*
