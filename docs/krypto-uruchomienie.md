# Uruchomienie krypto na papierze — runbook (30 sekund Twojej roboty)

Kod jest gotowy i wdrożony (Fazy 1–5). Zostało TYLKO to, czego fizycznie nie mogę
zrobić za Ciebie: **klucze paper** (sekret, generujesz w Alpaca) i wpisanie ich do
`.env` na VPS. Gdybym sam przełączył `ALPACA_PAPER=true` bez tych kluczy, bot
straciłby połączenie z Alpacą i stanął — dlatego ten jeden krok jest po Twojej stronie.

## Krok 1 — wygeneruj klucze PAPER w Alpaca
Alpaca → przełącz konto na **Paper Trading** → **API Keys** → *Generate*. Skopiuj
Key ID i Secret (to inne klucze niż live).

## Krok 2 — wpisz do `.env` na VPS
W katalogu repo na serwerze, w pliku `.env`:
```
ALPACA_PAPER=true
ALPACA_API_KEY=<PAPER Key ID>
ALPACA_API_SECRET=<PAPER Secret>
CRYPTO_ENABLED=true
```
(Realne klucze live możesz zostawić w komentarzu/na boku — paper je nadpisuje.)

## Krok 3 — redeploy i START
```
./deploy/deploy.sh
```
Potem w aplikacji (zakładka **Sterowanie**) naciśnij **START** na silniku krypto.
Od tej chwili bot handluje **sztucznym kapitałem** 24/7 na BTC/ETH/SOL/… —
mechanicznie, bez LLM (koszt ≈ $0).

## Jak poznasz, że działa
- Na **Pulpicie** plakietka **PAPER** (nie LIVE).
- Pasek rynku: **„Rynek krypto 24/7 otwarty / Handel bez przerwy"**.
- Silnik: **„gra"** (zielony), nie STOP.
- Po kilku cyklach pierwsze pozycje krypto w zakładce **Pozycje**.

## Zanim pójdzie na żywo (zalecane) — backtest na VPS
Najpierw zobacz, czy mechanika ma sens na historii krypto (benchmark: trzymanie BTC):
```
docker compose exec -T app python scripts/run_backtest.py --venue crypto --years 10
```
Jeśli strategia nie bije „trzymania BTC" — to cenna informacja PRZED włączeniem
(dokładnie tak jak przy akcjach, tyle że tu za darmo, na papierze).

## Bezpiecznik
`CRYPTO_ENABLED` domyślnie false i `crypto_paused` domyślnie true — bez powyższych
kroków nic się nie dzieje. Noga akcji pozostaje nietknięta.
