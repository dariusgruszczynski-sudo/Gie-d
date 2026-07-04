# Gie-d — automatyczny bot inwestycyjny (crypto)

Aplikacja do automatycznego inwestowania w kryptowaluty (domyślnie BTC, ETH,
SOL, BNB — lista jest w pełni konfigurowalna) na Binance,
w której decyzje inwestycyjne (co / kiedy / ile) podejmuje Claude Opus na
podstawie danych rynkowych i newsów. System ma dashboard z wynikami,
pełny log decyzji i transakcji, oraz przełącznik pauzy/wznowienia i panel do
ręcznej transakcji z pominięciem automatu.

## ⚠️ Ważne zastrzeżenia

- To jest **prywatne narzędzie na własny użytek i własny kapitał** — nie jest
  to licencjonowana usługa zarządzania aktywami ani porada inwestycyjna.
- Decyzje generowane przez model językowy (Claude Opus) **mogą być błędne**.
  Handel automatyczny wiąże się z ryzykiem szybkiej i istotnej utraty kapitału.
- Zanim podepniesz prawdziwe środki, **przetestuj system na Binance Testnet**
  (patrz sekcja "Tryb testnet vs. produkcja" niżej).
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

1. Scheduler co `POLL_INTERVAL_MINUTES` sprawdza ceny wszystkich par z `TRADING_WHITELIST`.
2. Jeśli cena zmieniła się o więcej niż `PRICE_MOVE_TRIGGER_PCT` od ostatniego
   sprawdzenia (albo minął dzień od ostatniej pełnej analizy — fallback),
   system uznaje to za "zdarzenie" i woła Claude Opus.
3. Opus dostaje: aktualne dane cenowe/świece, ostatnie newsy (jeśli skonfigurowany
   klucz CryptoPanic), stan portfela i pozostały dzienny budżet ryzyka —
   i zwraca ustrukturyzowaną decyzję (BUY/SELL/HOLD, symbol, wielkość, uzasadnienie).
4. Risk manager sprawdza whitelistę coinów, limit wielkości pojedynczej pozycji
   i dzienny/tygodniowy limit strat. Jeśli wszystko OK i automat nie jest
   zapauzowany/zatrzymany — zlecenie idzie na Binance.
5. Wszystko (decyzje, transakcje, zmiany wartości portfela, zdarzenia ryzyka)
   jest logowane do bazy i widoczne w dashboardzie.

## Wymagane klucze API

Skopiuj `.env.example` do `.env` i uzupełnij:

| Zmienna | Wymagane | Opis |
|---|---|---|
| `ANTHROPIC_API_KEY` | tak | Klucz do Claude API (Opus podejmuje decyzje) |
| `BINANCE_API_KEY` / `BINANCE_API_SECRET` | tak | Klucz do Binance (testnet lub produkcja — patrz niżej) |
| `BINANCE_TESTNET` | tak | `true` / `false` — przełącznik testnet vs. produkcja |
| `CRYPTOPANIC_API_KEY` | nie | Opcjonalny — jeśli brak, system pomija newsy i decyduje na podstawie samych danych cenowych |

## Tryb testnet vs. produkcja

Zgodnie z ustaleniami: **start na Binance Testnet**, dopiero potem przełączenie
na produkcję jednym ustawieniem w `.env`:

1. Załóż konto na https://testnet.binance.vision/ i wygeneruj testnetowe klucze API.
2. W `.env` ustaw `BINANCE_TESTNET=true` i wklej testnetowe klucze.
3. Uruchom system, obserwuj dashboard przez kilka dni (rekomendowane: 2-3 dni),
   sprawdź czy decyzje, limity ryzyka i transakcje działają zgodnie z oczekiwaniami.
4. Dopiero gdy jesteś zadowolony z działania — wygeneruj **prawdziwe** klucze API
   na Binance (z uprawnieniami tylko do spot trading, **bez** uprawnień do
   wypłat/withdraw), ustaw `BINANCE_TESTNET=false`, zrestartuj system.

## Konfiguracja ryzyka (`.env`)

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `DAILY_LOSS_LIMIT_PCT` | `50` | Przy spadku wartości portfela o tyle % w ciągu dnia — automat zatrzymuje handel automatyczny (wymaga ręcznego wznowienia w dashboardzie) |
| `MAX_POSITION_PCT` | `25` | Maks. % dostępnego kapitału, jaki automat może zaangażować w jedną transakcję |
| `TRADING_WHITELIST` | `BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT` | Lista par, którymi automat może handlować — w pełni generyczna, dowolna liczba par obsługiwanych przez Binance (format `<COIN>USDT`, przecinek jako separator) |
| `POLL_INTERVAL_MINUTES` | `15` | Co ile minut sprawdzać ceny/newsy |
| `PRICE_MOVE_TRIGGER_PCT` | `2` | Próg zmiany ceny traktowany jako "zdarzenie" wywołujące analizę Opus |

Zatrzymanie po przekroczeniu limitu strat **nie resetuje się automatycznie**
następnego dnia — wymaga świadomego kliknięcia "Wznów" w dashboardzie, żebyś
zawsze wiedział, że coś się wydarzyło i mógł ocenić sytuację.

## Budżet Claude (alert o koszcie API)

Anthropic **nie udostępnia w API prawdziwego salda konta** — nie ma sposobu,
żeby aplikacja odczytała ile realnie zostało Ci środków na
console.anthropic.com. Dashboard pokazuje więc **szacunek**: sumuje rzeczywiste
tokeny z każdej odpowiedzi Opusa i przelicza je po znanym cenniku
($5 / 1M tokenów wejściowych, $25 / 1M wyjściowych), resetując licznik co
miesiąc.

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
analizy Opusa oraz ostatnimi decyzjami/transakcjami.

Wysyłka idzie przez SMTP — najprościej użyć własnego konta Gmail z
**hasłem aplikacji** (App Password, nie zwykłe hasło):

1. Włącz weryfikację dwuetapową na koncie Google (jeśli jeszcze nie jest włączona): https://myaccount.google.com/security
2. Wygeneruj hasło aplikacji: https://myaccount.google.com/apppasswords → wybierz "Mail", nazwij np. "Gie-d" → skopiuj 16-znakowe hasło
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
zachowanie zgodne z poprzednimi wersjami. Żeby włączyć logowanie (przeglądarka
poprosi o login/hasło standardowym oknem HTTP Basic Auth), ustaw w `.env`:

```
DASHBOARD_USERS=uzytkownik1:haslo1,uzytkownik2:haslo2
```

Każde konto ma pełny dostęp (podgląd + pauza/wznów/ręczna transakcja/restart) —
to narzędzie prywatne bez rozróżnienia ról. Dla dodatkowego bezpieczeństwa na
publicznym IP rozważ też reverse proxy (np. Caddy/Nginx) z HTTPS, żeby hasła
nie szły przez sieć w czystym tekście.

## Testy

```bash
cd backend
pytest
```
