#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# GielDarek -- deploy "wielkiej przebudowy" (PM-mode, dynamiczne uniwersum,
# newsy Alpaca/AlphaVantage/NewsAPI/SerpAPI, blackout newsów, zdjęty kaganiec,
# popupy). Idempotentny: można puszczać wielokrotnie.
#
# Co robi:
#   1. Przełącza repo na gałąź deployową i zaciąga najnowszy kod.
#   2. Wymusza w .env (i .env.staging) wszystkie NIE-sekretne knoby tej zmiany
#      -- bo .env nadpisuje kod, więc bez tego część zmian by nie weszła.
#   3. Przebudowuje i restartuje kontenery (prod app + staging) z tego kodu.
#   4. Sprawdza health.
#
# NIE dotyka sekretów: kluczy Alpaca ani kluczy newsów. Klucze newsów muszą już
# być w .env (skrypt tylko ostrzega, jeśli ich nie ma). Klucze Alpaca zostają
# nietknięte (prod = żywe, staging = paper -- świadomie różne).
#
# Użycie (na serwerze, w katalogu repo):  ./deploy/deploy.sh
# ---------------------------------------------------------------------------
set -euo pipefail

BRANCH="claude/automated-stock-trading-app-ulacio"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "==> Repo: $ROOT"

# --- 1) Kod ----------------------------------------------------------------
echo "==> Pobieram gałąź $BRANCH"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"   # .env jest w .gitignore, więc go NIE rusza
echo "==> Kod na: $(git rev-parse --short HEAD) $(git log -1 --format=%s)"

# WAŻNE (fix jednokomitowego opóźnienia knobów): ten skrypt WŁAŚNIE sam siebie
# nadpisał przez git reset, ale bash wykonuje dalej STARĄ wersję z pamięci -- więc
# apply_knobs poniżej brałby wartości z POPRZEDNIEGO commita. Re-exec świeżej
# wersji RAZ, żeby knoby i build biegły z AKTUALNEGO kodu.
if [ -z "${GIELD_DEPLOY_REEXEC:-}" ]; then
  export GIELD_DEPLOY_REEXEC=1
  exec bash "$ROOT/deploy/deploy.sh" "$@"
fi

# --- 2) .env: wymuś nie-sekretne knoby (idempotentnie) ---------------------
setenv() { # setenv KEY VALUE FILE
  local k="$1" v="$2" f="$3"
  touch "$f"
  sed -i "/^${k}=/d" "$f"
  printf '%s=%s\n' "$k" "$v" >> "$f"
}

apply_knobs() { # apply_knobs FILE
  local f="$1"
  [ -f "$f" ] || { echo "   (pomijam $f -- brak pliku)"; return 0; }
  echo "==> Ustawiam knoby w $f"
  # --- STRATEGIA POZYCYJNA (dzienna) -- 2026-07-28 ---
  setenv SIGNAL_TIMEFRAME 1d "$f"                 # świece dzienne (jak backtest)
  setenv POLL_INTERVAL_MINUTES 30 "$f"           # co 30 min: mechaniczne wyjścia
  setenv EXTENDED_POLL_INTERVAL_MINUTES 30 "$f"
  setenv FULL_ANALYSIS_EVERY_MINUTES 0 "$f"      # bez zegarowego heartbeatu
  setenv PRICE_MOVE_TRIGGER_PCT 3.0 "$f"         # anty-churn: budzenie na >=3% (mniej reaktywnej sprzedaży)
  setenv EXTENDED_PRICE_MOVE_TRIGGER_PCT 3.0 "$f"
  setenv EXTENDED_FULL_ANALYSIS_EVERY_MINUTES 0 "$f"
  # JEDEN SILNIK: noga POZA SESJĄ (extended/after-hours) WYŁĄCZONA -- cały handel
  # prowadzi jeden zdyscyplinowany silnik pozycyjny (sesja regularna).
  setenv EXTENDED_ENABLED false "$f"
  # Trzymanie pozycyjne, ale BEZ trzymania zysków za długo (2026-08-05)
  setenv MIN_HOLD_MINUTES 2880 "$f"             # min. 2 dni na pozycje ~zero/minus (anty-churn)
  setenv MIN_HOLD_PROFIT_BYPASS_PCT 3.0 "$f"    # realny zysk (>=3%) bierzemy OD RAZU (było 4% — audyt: zyski wisiały ~2 dni)
  setenv HARD_TAKE_PROFIT_PCT 6.0 "$f"           # mocny ruch (+6%) kasujemy, nie oddajemy (było 8% — bierzemy zysk szybciej)
  setenv STOP_LOSS_MIN_PCT 3.0 "$f"
  setenv TRAILING_STOP_FRAC 0.6 "$f"
  # Progresywne wejścia: więcej pozycji, ale każda kolejna wymaga mocniejszego sygnału
  setenv MIN_BUY_CONFIDENCE 0.55 "$f"           # bazowy próg dla 1. wejścia
  setenv PROGRESSIVE_CONFIDENCE_STEP 0.03 "$f"  # +0.03 pewności za każdą trzymaną pozycję
  setenv PROGRESSIVE_CONFIDENCE_CAP 0.9 "$f"
  setenv MAX_CONCURRENT_POSITIONS 12 "$f"
  setenv MAX_NEW_POSITIONS_PER_DAY 8 "$f"
  setenv MAX_POSITION_PCT 90 "$f"
  setenv ENTRY_FILTER_ENABLED true "$f"
  setenv AUTO_DEMOTE_ENABLED false "$f"
  # Reżim: twarda gotówka w risk-off (adaptive off -> gate on)
  setenv ADAPTIVE_RISK_ENABLED false "$f"
  setenv REGIME_GATE_ENABLED true "$f"
  setenv DEFENSIVE_SYMBOLS GLD,TLT "$f"
  # Uniwersum jakości; strukturalni przegrani na czarnej liście
  setenv TRADING_WHITELIST SPY,QQQ,AAPL,MSFT,NVDA,AMZN,GOOGL,META,SMH,GLD,TLT "$f"
  setenv SYMBOL_BLACKLIST TQQQ,SQQQ,SOXL,SOXS,TNA,TZA,SPXL,SPXS,UPRO,SPXU,UDOW,SDOW,TMF,TMV,LABU,LABD,YINN,YANG,NUGT,DUST,JNUG,JDST,BOIL,KOLD,UVXY,SVXY,VIXY,UVIX,SVIX,SH,XLE,XLU,XLF,XLP,XLI,SLV "$f"
  setenv DYNAMIC_UNIVERSE_ENABLED true "$f"
  setenv UNIVERSE_MAX_SYMBOLS 24 "$f"
  # Tokeny: NIE haltujemy na brak (właściciel auto-doładowuje). Budżet to tylko
  # kotwica licznika "zostało $" na UI (pauza i tak wyłączona). Prod .env miał
  # zostawiony testowy CLAUDE_MONTHLY_BUDGET_USD=1, przez co licznik pokazywał
  # "wyczerpany" -- ustawiamy sensowną wartość wyświetlania (zmień, gdy chcesz).
  setenv CLAUDE_PAUSE_TRADING_AT_BUDGET false "$f"
  setenv CLAUDE_ESCALATION_ENABLED false "$f"
  setenv CLAUDE_MONTHLY_BUDGET_USD 150 "$f"
  # Bezpieczeństwo danych: brak newsów = stop nowych wejść + alarm.
  setenv NEWS_BLACKOUT_HALT_ENABLED true "$f"
  setenv NEWS_MIN_HEADLINES 3 "$f"
  # Read-only token dla WIDGETU iPhone (Scriptable) i linku podglądu: pozwala
  # TYLKO na GET dashboardu (status/portfel/widget/historia/audyt) — ŻADNEGO
  # handlu ani sterowania. Bez niego /api/widget?share=... zwraca 401. Chcesz
  # odciąć/zmienić? Podmień token tutaj albo ustaw pusty i redeploy.
  setenv SHARE_TOKEN gd-ro-8f3ktq29xr7v "$f"
}

apply_knobs .env
apply_knobs .env.staging

# Ostrzeżenie, jeśli brakuje kluczy newsów (skrypt ich NIE wpisuje -- to sekrety)
for K in ALPHA_VANTAGE_API_KEY NEWSAPI_API_KEY SERPAPI_API_KEY; do
  if ! grep -qE "^${K}=.+" .env 2>/dev/null; then
    echo "   UWAGA: brak $K w .env -- to źródło newsów będzie pominięte (Alpaca News i tak działa)."
  fi
done

# --- 3) Build + restart ----------------------------------------------------
# Stempel wersji do obrazu: apka pokaże ten sam SHA co niżej, więc jednym
# spojrzeniem widać, czy na serwerze działa najnowszy kod.
export GIT_SHA="$(git rev-parse --short HEAD)"
export BUILD_TIME="$(date -u +%Y-%m-%dT%H:%MZ)"
# KLUCZOWE: HTTPS obsługuje kontener Caddy z docker-compose.caddy.yml. Jeśli
# deploy uruchamia compose BEZ tego pliku, Caddy staje się "sierotą": każdy
# `up -d --build` przerabia sieć proda i ROZŁĄCZA Caddy od apki -> publiczny
# adres pada mimo działającego backendu (białe/czarne ekrany, "nie można
# połączyć"). Dlatego KAŻDA komenda compose obejmuje oba pliki, gdy Caddy jest
# obecny -- app i Caddy są zarządzane jako jeden projekt i nigdy się nie rozjadą.
COMPOSE="docker compose -f docker-compose.yml"
[ -f "$ROOT/deploy/docker-compose.caddy.yml" ] && COMPOSE="$COMPOSE -f $ROOT/deploy/docker-compose.caddy.yml"
echo "==> Przebudowuję i restartuję kontenery (prod + staging) -- wersja $GIT_SHA"
# Buildkit potrafi rzucić przejściowym "rpc error: EOF" (dwa obrazy naraz na
# ciaśniejszej maszynie). Najpierw pewny PROD (app), potem staging; każdy z
# retry, żeby jedna czkawka nie wywalała deployu i nie zostawiała starej wersji.
build_with_retry() { # build_with_retry SERVICE
  local svc="$1" ok=0 i
  for i in 1 2 3; do
    if $COMPOSE up -d --build "$svc"; then ok=1; break; fi
    echo "   build '$svc' próba $i nieudana (buildkit?) -- ponawiam za 6s..."; sleep 6
  done
  [ "$ok" = 1 ]
}
build_with_retry app || { echo "!! PROD build nieudany po 3 próbach -- zostaje poprzednia wersja"; exit 1; }
build_with_retry app-staging || echo "   UWAGA: staging build nieudany -- prod działa, staging pominięty."
# Upewnij się, że Caddy (HTTPS) stoi i jest na aktualnej sieci proda.
$COMPOSE up -d caddy 2>/dev/null || echo "   (Caddy pominięty -- brak pliku caddy albo portów 80/443)"

# --- 4) Health -------------------------------------------------------------
echo "==> Status kontenerów"
$COMPOSE ps
echo "==> Czekam na start i sprawdzam health (prod :8000)"
# "Zdrowy" = serwer ZWRACA jakikolwiek kod HTTP (200 = OK, 401 = działa, tylko za
# loginem -- bo /api/status jest chronione, a curl z serwera nie ma sesji). Tylko
# BRAK odpowiedzi (000 = nie słucha / timeout) to realny problem. Wcześniej
# curl -f traktował 401 jako błąd i fałszywie krzyczał "nie odpowiada".
health_code=000
for i in 1 2 3 4 5 6; do
  sleep 4
  health_code="$(curl -s -m 5 -o /dev/null -w "%{http_code}" localhost:8000/api/status 2>/dev/null || echo 000)"
  [ "$health_code" != "000" ] && break
done
[ "$health_code" != "000" ] && echo "   OK: serwer odpowiada (HTTP $health_code)" || echo "   UWAGA: brak odpowiedzi po ~24s -- sprawdź: docker compose logs -f app"
# Zapisz OSTATNIO UDANY commit (po udanym buildzie proda). autopull porównuje
# do tego pliku, nie do HEAD -- więc nieudany build (który i tak przesunął HEAD)
# zostanie PONOWIONY przy następnym cyklu zamiast być uznany za wdrożony.
git rev-parse HEAD > "$ROOT/.last_deployed_sha"
echo "==> Gotowe (wdrożono $(git rev-parse --short HEAD)). Dashboard: :8000 (prod), :8092 (staging)"
