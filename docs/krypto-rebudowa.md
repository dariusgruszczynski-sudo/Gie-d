# GielDarek → Krypto (papier) — plan przebudowy i strategia

**Decyzja właściciela (2026-10-01):** wycofać realną gotówkę, przejść na **krypto na
sztucznym kapitale (Alpaca paper)**, uczyć się na fejkowym koncie. Powód: po 4 mies.
akcje wyszły ~na zero, a największym kosztem był LLM (~$196). Krypto-paper = zero ryzyka
kapitału, rynek 24/7 (więcej danych, polskie godziny), tani silnik.

Wybory: **Alpaca paper crypto** · **przebudowa na sprawdzonym rdzeniu** (nie od zera) ·
**mechanika najpierw, LLM rzadko**.

## Szczera prawda o handlu krypto

- Krypto jest **bardziej zmienne i nie mniej efektywne** niż akcje — retailowe boty
  krypto też w większości tracą. Nie budujemy maszynki do kasy; budujemy **sandbox do
  nauki** bez ryzyka (papier).
- Co realnie ma jakąkolwiek historyczną przewagę w krypto (a co nie):
  - **Trend/momentum** (podążanie za trendem, przełamania) — najlepiej udokumentowane,
    bo krypto bywa silnie trendujące. Niski obrót, szerokie stopy.
  - **Mean-reversion** na krótkim horyzoncie — działa w konsolidacji, zabójcze w trendzie.
  - **Sentyment z newsów/LLM** — brak powtarzalnej przewagi; news jest w cenie w sekundy.
    Dlatego LLM schodzi na rolę rzadkiego „weta/eskalacji", nie głównego sygnału.
- **Koszty w krypto są wyższe**: szersze spready, fee ~0.1-0.25%/stronę. Przy częstym
  handlu to zjada wynik — dlatego mniej, większych, dłużej trzymanych pozycji.

## Strategia (mechanika najpierw)

1. **Uniwersum:** ciasna, płynna lista par USD: BTC, ETH, SOL, LINK, AVAX, LTC, DOGE.
   Płynność > egzotyka (unikamy śmieciowych altów — to był największy przeciek na akcjach).
2. **Sygnał wejścia (bez LLM):** konfluencja wskaźników na 1h — trend (EMA), momentum
   (RSI/MACD), przełamanie zakresu + filtr zmienności. Wejście tylko gdy kilka się zgadza.
3. **LLM tylko rzadko:** przy granicznej/dużej decyzji (np. duży setup, sprzeczne sygnały)
   — jako weto/potwierdzenie, nie na każdym cyklu. Cel kosztu: **~$5/mc zamiast ~$70**.
4. **Ryzyko:** `crypto_risk_per_trade_pct=1.5%`, stop pod zmienność (min 4%, max 18%),
   reward/risk 2.0, częściowa realizacja przy 1.5R, trailing na resztę. Max 5 pozycji,
   max 40% konta na parę.
5. **24/7:** poll co 15 min, brak sesji/holidays, brak limitu wejść dziennych (reguluje
   gotówka + ryzyko + płynność).

## Architektura — co zostaje, co się zmienia

**Zostaje (sprawdzony rdzeń):** auth, risk_manager, stopy/wyjścia mechaniczne, scorecard/
metryki, audyt, PWA, deploy, scheduler. Wszystko jest venue-agnostyczne.

**Zmienia się / dochodzi:**
- `venue="crypto"` obok „alpaca"/„extended" — profil 24/7, szersze stopy (Faza 1 ✅).
- Egzekucja par „BTC/USD" (fractional/notional, 24/7 book) w `alpaca_client` + routing w
  `trading_engine` + cykl 24/7 w `scheduler` + kolumny stanu per-venue w `models` (Faza 2).
- Tani silnik sygnałów na wskaźnikach; LLM okazjonalnie (Faza 3).
- Backtest na historii krypto, nauka parametrów przed paper-live (Faza 4).
- Przebudowa zakładek pod krypto 24/7, bez sesji US (Faza 5).

## Fazy (patrz lista zadań)

- **Faza 0 — bezpieczeństwo:** `ALPACA_PAPER=true` + **klucze paper (generuje właściciel)**,
  wyłączyć live. ⚠ Twarda zależność: bez kluczy paper bot nie połączy się z paper-API.
- **Faza 1 — fundament venue krypto:** config + 24/7 + profil + ten dokument. ✅
- **Faza 2 — egzekucja krypto.**
- **Faza 3 — tani silnik decyzyjny.**
- **Faza 4 — backtest/nauka na danych historycznych.**
- **Faza 5 — przebudowa UX/zakładek.**

## Czego potrzebuję od właściciela

1. **Klucze API paper z Alpaca** (Alpaca → Paper Trading → API Keys). To sekret — ja ich
   nie ustawię; wpisz w `.env` na VPS: `ALPACA_PAPER=true`, `ALPACA_API_KEY=...`,
   `ALPACA_API_SECRET=...` (klucze paper, nie live).
2. Potwierdzenie, że realna gotówka wyjęta z konta live (żeby nic realnego nie zostało).
