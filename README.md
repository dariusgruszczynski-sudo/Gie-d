# GielDarek — automatyczny bot inwestycyjny (akcje/ETF)

Aplikacja do automatycznego inwestowania w akcje i ETF-y bez prowizji
(domyślnie SPY, QQQ, AAPL, NVDA — lista jest w pełni konfigurowalna) na
Alpaca (rynek US), w której decyzje inwestycyjne (co / kiedy / ile) podejmuje
Claude -- Sonnet analizuje każdy cykl, a Opus podejmuje ostateczną decyzję
tylko gdy Sonnet sam zgłasza niepewność co do BUY/SELL -- na podstawie danych
rynkowych i newsów z kilkunastu źródeł. System ma dashboard z wynikami, pełny
log decyzji i transakcji, oraz przełącznik start/stop i panel do ręcznej
transakcji z pominięciem automatu.

## ⚠️ Ważne zastrzeżenia

- To jest **prywatne narzędzie na własny użytek i własny kapitał** — nie jest
  to licencjonowana usługa zarządzania aktywami ani porada inwestycyjna.
- Decyzje generowane przez modele językowe (Claude) **mogą być błędne**.
  Handel automatyczny wiąże się z ryzykiem szybkiej i istotnej utraty kapitału.
- Alpaca ma prawdziwe środowisko **paper-trading** (`ALPACA_PAPER=true`) z
  identycznym API co konto live -- warto przetestować bota tam, zanim
  przełączysz się na `ALPACA_PAPER=false` i prawdziwe pieniądze. Zanim
  podepniesz klucz API, przeczytaj sekcję "Konfiguracja Alpaca" niżej.
- Nigdy nie commituj prawdziwych kluczy API do repozytorium — używaj `.env`
  (jest w `.gitignore`).
- Autor/asystent AI, który zbudował ten kod, nie ponosi odpowiedzialności za
  straty finansowe wynikające z jego użycia. Używasz na własne ryzyko.

## Architektura

```
backend/   FastAPI + SQLite + APScheduler — silnik tradingowy, API, logika ryzyka
frontend/  React + Vite — dashboard (wyniki, log decyzji, panel kontroli)
```

Przepływ decyzyjny:

1. Scheduler co `POLL_INTERVAL_MINUTES` sprawdza ceny wszystkich tickerów z
   `TRADING_WHITELIST` na Alpaca -- tylko gdy rynek US jest otwarty; poza
   sesją giełdową cykl automatyczny nic nie robi (zlecenie i tak by odpadło).
2. Jeśli cena zmieniła się o więcej niż `PRICE_MOVE_TRIGGER_PCT` od ostatniego
   sprawdzenia (albo minął dzień od ostatniej pełnej analizy — fallback),
   system uznaje to za "zdarzenie" i woła Claude.
3. Claude dostaje: aktualne dane cenowe/świece, newsy i kontekst rynkowy z
   kilkunastu źródeł (RSS największych portali finansowych, Reddit, Fear &
   Greed Index i inne), stan portfela i pozostały dzienny budżet ryzyka.
   Najpierw odpowiada szybszy/tańszy model (Sonnet); jeśli sam zgłosi niską
   pewność co do BUY/SELL, o ostateczną decyzję pytany jest Opus. Wynik to
   zawsze jedna ustrukturyzowana decyzja (BUY/SELL/HOLD, symbol, wielkość,
   uzasadnienie).
4. Risk manager sprawdza whitelistę tickerów, limit wielkości pojedynczej
   pozycji i dzienny/tygodniowy limit strat. Jeśli wszystko OK i automat nie
   jest zapauzowany/zatrzymany — zlecenie idzie na Alpaca.
5. Wszystko (decyzje, transakcje, zmiany wartości portfela, zdarzenia ryzyka)
   jest logowane do bazy i widoczne w dashboardzie.

## Wymagane klucze API

Skopiuj `.env.example` do `.env` i uzupełnij:

| Zmienna | Wymagane | Opis |
|---|---|---|
| `ANTHROPIC_API_KEY` | tak | Klucz do Claude API (Sonnet analizuje, Opus decyduje w niepewnych przypadkach) |
| `ALPACA_API_KEY` / `ALPACA_API_SECRET` | tak | Klucz do Alpaca — patrz sekcja "Konfiguracja Alpaca" niżej |

## Konfiguracja Alpaca

Alpaca ma prawdziwe środowisko **paper-trading** z identycznym API co konto
live — w odróżnieniu od Kraken/krypto da się tu bezpiecznie "przetestować na
sucho" przed przełączeniem na prawdziwe pieniądze.

1. Załóż/zaloguj się na konto Alpaca (https://alpaca.markets).
2. Do testów: wygeneruj klucz API na
   https://app.alpaca.markets/paper/dashboard/overview (środowisko paper,
   symulowane $100k). Na produkcję (prawdziwe pieniądze): wygeneruj osobny
   klucz na https://app.alpaca.markets/live/dashboard/overview.
3. W `.env` wklej `ALPACA_API_KEY` / `ALPACA_API_SECRET` i ustaw
   `ALPACA_PAPER=true` (paper) albo `false` (live) zgodnie z tym, który klucz
   wkleiłeś — **klucze paper i live nie są wymienne**, każdy działa tylko w
   swoim środowisku.
4. Whitelist (`TRADING_WHITELIST`) używa zwykłych tickerów giełdowych, bez
   sufiksu waluty (np. `SPY`, nie `SPYUSD`).
5. Pamiętaj, że akcje/ETF-y handlują się tylko w godzinach sesji giełdy US
   (ok. 9:30–16:00 czasu New York, dni robocze) — poza sesją automat
   pomija cykl (Claude nadal odpowiada na "Wymuś analizę" ręcznie, ale
   wynikowe zlecenie nie może się wykonać, dopóki rynek się nie otworzy).
6. Zanim przełączysz się na `ALPACA_PAPER=false`, rozważ start z niskim
   `MAX_POSITION_PCT` i niskim `DAILY_LOSS_LIMIT_PCT`, i obserwuj pierwsze
   cykle ręcznie z poziomu dashboardu.

## Konfiguracja ryzyka (`.env`)

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `DAILY_LOSS_LIMIT_PCT` | `20` | Przy spadku wartości portfela o tyle % w ciągu dnia — automat zatrzymuje handel automatyczny (wymaga ręcznego wznowienia w dashboardzie) |
| `MAX_POSITION_PCT` | `25` | Maks. % dostępnego kapitału, jaki automat może zaangażować w jedną transakcję |
| `STOP_LOSS_PCT` | `2` | Twarda podłoga: automat sprzedaje całą pozycję, gdy straci tyle % od średniej ceny wejścia. `0` = wyłączone |
| `STOP_LOSS_COOLDOWN_MINUTES` | `60` | Po stop-lossie ta sama para jest zablokowana do odkupu na tyle minut (ochrona przed piłowaniem konta prowizjami). `0` = wyłączone |
| `TAKE_PROFIT_PCT` | `3` | Zysk, po którym uzbraja się trailing-stop (lub — przy wyłączonym trailingu — natychmiastowa sprzedaż) |
| `TRAILING_STOP_ENABLED` | `true` | `true` = po zysku `TAKE_PROFIT_PCT` pozwól zyskom rosnąć i sprzedaj dopiero po spadku `TRAILING_STOP_PCT` od szczytu. `false` = sztywny take-profit przy `TAKE_PROFIT_PCT` |
| `TRAILING_STOP_PCT` | `1.5` | O ile % cena musi spaść od szczytu, żeby trailing-stop sprzedał (gdy uzbrojony) |
| `TRADE_ALERTS_ENABLED` | `true` | Mail natychmiast po każdej transakcji (BUY/SELL, w tym wyjścia TP/SL). Wymaga SMTP; `false` = tylko raport dzienny |
| `TRADING_WHITELIST` | `SPY,QQQ,AAPL,NVDA` | Lista tickerów, którymi automat może handlować — w pełni generyczna, dowolna liczba tickerów obsługiwanych przez Alpaca (przecinek jako separator) |
| `POLL_INTERVAL_MINUTES` | `15` | Co ile minut sprawdzać ceny/newsy |
| `PRICE_MOVE_TRIGGER_PCT` | `2` | Próg zmiany ceny traktowany jako "zdarzenie" wywołujące analizę Claude |

Zatrzymanie po przekroczeniu limitu strat **nie resetuje się automatycznie**
następnego dnia — wymaga świadomego kliknięcia "START" w dashboardzie, żebyś
zawsze wiedział, że coś się wydarzyło i mógł ocenić sytuację.

## Budżet Claude (alert o koszcie API)

Anthropic **nie udostępnia w API prawdziwego salda konta** — nie ma sposobu,
żeby aplikacja odczytała ile realnie zostało Ci środków na
console.anthropic.com. Dashboard pokazuje więc **szacunek**: sumuje rzeczywiste
tokeny z każdej odpowiedzi (osobno wycenione wg modelu, który faktycznie
odpowiedział — Sonnet $3 / 1M wejściowych, $15 / 1M wyjściowych; Opus $5 / 1M
wejściowych, $25 / 1M wyjściowych), resetując licznik co miesiąc. Większość
cykli kosztuje tyle co Sonnet — Opus włącza się tylko przy niepewnym BUY/SELL.

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `CLAUDE_MONTHLY_BUDGET_USD` | `20` | Ustaw na kwotę, którą realnie doładowałeś na konto Anthropic |
| `CLAUDE_BUDGET_ALERT_THRESHOLD_PCT` | `80` | Przy jakim % wykorzystania budżetu dashboard pokaże ostrzeżenie |

Gdy szacowane zużycie przekroczy próg, na dashboardzie pojawi się alert z
przypomnieniem o doładowaniu konta na **console.anthropic.com**. To przybliżenie
(nie chroni przed realnym zatrzymaniem API, gdy saldo faktycznie się wyczerpie) —
warto dodatkowo włączyć auto-reload w ustawieniach billingu Anthropica.

## Codzienny raport mailowy

Codziennie o **6:00 (czasu Europe/Warsaw)** system wysyła mail z wykresem
wartości portfela, statusem, budżetem Claude, perspektywą rynkową z ostatniej
analizy Claude oraz ostatnimi decyzjami/transakcjami.

Wysyłka idzie przez SMTP — najprościej użyć własnego konta Gmail z
**hasłem aplikacji** (App Password, nie zwykłe hasło):

1. Włącz weryfikację dwuetapową na koncie Google (jeśli jeszcze nie jest włączona): https://myaccount.google.com/security
2. Wygeneruj hasło aplikacji: https://myaccount.google.com/apppasswords → wybierz "Mail", nazwij np. "GielDarek" → skopiuj 16-znakowe hasło
3. W `.env` uzupełnij:
   - `SMTP_USERNAME` = Twój adres Gmail (nadawca)
   - `SMTP_PASSWORD` = wygenerowane hasło aplikacji (bez spacji)
   - `SMTP_FROM_EMAIL` = ten sam adres Gmail
   - `REPORT_RECIPIENT_EMAIL` = adres odbiorcy (domyślnie `0grucha0@gmail.com`)

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `SMTP_HOST` / `SMTP_PORT` | `smtp.gmail.com` / `587` | Zmień jeśli używasz innego dostawcy SMTP |
| `REPORT_HOUR` / `REPORT_MINUTE` | `6` / `0` | O której godzinie wysyłać raport |
| `REPORT_TIMEZONE` | `Europe/Warsaw` | Strefa czasowa dla harmonogramu (niezależnie od strefy serwera) |

Po uzupełnieniu i restarcie (`docker compose up -d --build`) możesz kliknąć
**"Wyślij raport testowy"** w panelu kontroli na dashboardzie, żeby sprawdzić
konfigurację SMTP bez czekania do 6:00.

## Uruchomienie lokalne (development)

Backend:

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # uzupełnij klucze
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173 (proxy do API na :8000)

## Uruchomienie produkcyjne (Docker, VPS)

```bash
cp .env.example .env   # uzupełnij klucze i limity ryzyka
docker compose up -d --build
```

Aplikacja (API + zbudowany dashboard) będzie dostępna pod `http://<adres-vps>:8000`.
Baza danych (SQLite) trzyma się w wolumenie `./data` — rób jej kopie zapasowe.

Rekomendowany hosting: tani VPS (np. Hetzner CX22, DigitalOcean Basic Droplet)
z Dockerem. Jeśli VPS ma publiczny adres IP, koniecznie ustaw `DASHBOARD_USERS`
(patrz niżej) — bez tego każdy, kto zna adres, ma pełną kontrolę nad automatem.

## Logowanie do dashboardu

Domyślnie dashboard **nie wymaga logowania** (`DASHBOARD_USERS` puste w `.env`) —
zachowanie zgodne z poprzednimi wersjami. Żeby włączyć logowanie (własny ekran
logowania w aplikacji, nie systemowe okienko przeglądarki), ustaw w `.env`:

```
DASHBOARD_USERS=uzytkownik1:haslo1,uzytkownik2:haslo2
```

Każde konto ma pełny dostęp (podgląd + pauza/wznów/ręczna transakcja/restart) —
to narzędzie prywatne bez rozróżnienia ról. Logowanie działa przez podpisane
ciasteczko sesji (httpOnly, ważne 7 dni) ustawiane po poprawnym zalogowaniu —
nie przez HTTP Basic Auth, żeby uniknąć natywnego okienka logowania
przeglądarki. Dla dodatkowego bezpieczeństwa na publicznym IP rozważ też
reverse proxy (np. Caddy/Nginx) z HTTPS, żeby hasła nie szły przez sieć w
czystym tekście.

## Testy

```bash
cd backend
pytest
```
