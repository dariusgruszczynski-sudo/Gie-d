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
  # Trzymanie pozycyjne + szerokie stopy (koniec whipsawu)
  setenv MIN_HOLD_MINUTES 2880 "$f"             # min. 2 dni -- koniec churnu (stop-loss i tak działa)
  setenv HARD_TAKE_PROFIT_PCT 0 "$f"             # brak twardego TP -- zwycięzcy biegną
  setenv STOP_LOSS_MIN_PCT 3.0 "$f"
  setenv TRAILING_STOP_FRAC 0.6 "$f"
  # Selektywność + koncentracja (dane 2026-08-04: 14% trafności -> mniej, lepiej)
  setenv MIN_BUY_CONFIDENCE 0.6 "$f"
  setenv MAX_CONCURRENT_POSITIONS 8 "$f"
  setenv MAX_NEW_POSITIONS_PER_DAY 5 "$f"
  setenv MAX_POSITION_PCT 90 "$f"
  setenv ENTRY_FILTER_ENABLED true "$f"
  setenv AUTO_DEMOTE_ENABLED false "$f"
  # Reżim: twarda gotówka w risk-off (adaptive off -> gate on)
  setenv ADAPTIVE_RISK_ENABLED false "$f"
  setenv REGIME_GATE_ENABLED true "$f"
  setenv DEFENSIVE_SYMBOLS GLD,TLT "$f"
  # Uniwersum jakości; strukturalni przegrani na czarnej liście
  setenv TRADING_WHITELIST SPY,QQQ,AAPL,MSFT,NVDA,AMZN,GOOGL,META,SMH,GLD,TLT "$f"
  setenv SYMBOL_BLACKLIST TQQQ,SQQQ,SOXL,SOXS,TNA,TZA,SPXL,SPXS,UPRO,SPXU,UDOW,SDOW,TMF,TMV,LABU,LABD,YINN,YANG,NUGT,DUST,JNUG,JDST,BOIL,KOLD,UVXY,SVXY,VIXY,UVIX,SVIX,SH,XLE,XLU,XLF,XLP,XLI "$f"
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
echo "==> Przebudowuję i restartuję kontenery (prod + staging) -- wersja $GIT_SHA"
# Buildkit potrafi rzucić przejściowym "rpc error: EOF" (dwa obrazy naraz na
# ciaśniejszej maszynie). Najpierw pewny PROD (app), potem staging; każdy z
# retry, żeby jedna czkawka nie wywalała deployu i nie zostawiała starej wersji.
build_with_retry() { # build_with_retry SERVICE
  local svc="$1" ok=0 i
  for i in 1 2 3; do
    if docker compose up -d --build "$svc"; then ok=1; break; fi
    echo "   build '$svc' próba $i nieudana (buildkit?) -- ponawiam za 6s..."; sleep 6
  done
  [ "$ok" = 1 ]
}
build_with_retry app || { echo "!! PROD build nieudany po 3 próbach -- zostaje poprzednia wersja"; exit 1; }
build_with_retry app-staging || echo "   UWAGA: staging build nieudany -- prod działa, staging pominięty."

# --- 4) Health -------------------------------------------------------------
echo "==> Status kontenerów"
docker compose ps
echo "==> Czekam na start i sprawdzam health (prod :8000)"
health_ok=0
for i in 1 2 3 4 5 6; do
  sleep 4
  if curl -fsS localhost:8000/api/status >/dev/null 2>&1; then health_ok=1; break; fi
done
[ "$health_ok" = 1 ] && echo "   OK: /api/status odpowiada" || echo "   UWAGA: /api/status nie odpowiada po ~24s -- sprawdź: docker compose logs -f app"
# Zapisz OSTATNIO UDANY commit (po udanym buildzie proda). autopull porównuje
# do tego pliku, nie do HEAD -- więc nieudany build (który i tak przesunął HEAD)
# zostanie PONOWIONY przy następnym cyklu zamiast być uznany za wdrożony.
git rev-parse HEAD > "$ROOT/.last_deployed_sha"
echo "==> Gotowe (wdrożono $(git rev-parse --short HEAD)). Dashboard: :8000 (prod), :8092 (staging)"
