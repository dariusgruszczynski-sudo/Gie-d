#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# GielDarek -- AUTO-DEPLOY (pull-based). Uruchamiany cyklicznie (systemd timer
# albo cron) NA SERWERZE. Sprawdza, czy na gałęzi deployowej pojawiły się nowe
# commity; jeśli tak -- odpala ./deploy/deploy.sh i nic więcej. Jeśli nie ma
# zmian, kończy w ~sekundę bez ruszania kontenerów.
#
# DZIĘKI TEMU: gdy Claude (z web/telefonu) wypycha zmiany na gałąź, serwer sam
# je zaciąga i wdraża w ciągu kilku minut -- bez SSH, bez terminala, bez
# udostępniania kluczy. To PULL (serwer sięga do GitHuba), więc nie wymaga
# żadnego otwartego portu ani dostępu z zewnątrz.
#
# Instalacja jednorazowa -- patrz deploy/AUTODEPLOY.md.
# ---------------------------------------------------------------------------
set -euo pipefail

BRANCH="claude/automated-stock-trading-app-ulacio"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Zaciągnij referencje bez zmiany plików.
git fetch --quiet origin "$BRANCH" || { LOG "fetch nieudany -- pomijam ten cykl"; exit 0; }

REMOTE="$(git rev-parse "origin/$BRANCH")"
# Porównujemy do OSTATNIO UDANIE WDROŻONEGO commita (plik pisany przez deploy.sh
# dopiero po udanym buildzie), a NIE do HEAD. Bo deploy.sh robi git reset --hard
# ZANIM zbuduje -- gdyby build padł, HEAD i tak by się przesunął i porównanie do
# HEAD uznałoby wdrożenie za zrobione (i nigdy by nie ponowiło). Plik = prawda.
DEPLOYED="$(cat "$ROOT/.last_deployed_sha" 2>/dev/null || echo none)"

if [ "$DEPLOYED" = "$REMOTE" ]; then
  # Najnowsze już wdrożone -- cisza (nie spamuj logu przy każdym cyklu).
  exit 0
fi

LOG "Nowa/niewdrożona wersja na $BRANCH: wdrożone=${DEPLOYED:0:7} -> zdalne=${REMOTE:0:7}. Wdrażam."
# deploy.sh sam robi checkout/reset --hard + build + restart + health-check.
if ./deploy/deploy.sh; then
  LOG "Deploy OK -> $(git rev-parse --short HEAD) $(git log -1 --format=%s)"
else
  LOG "DEPLOY NIEUDANY -- zostawiam poprzednią wersję działającą. Sprawdź: docker compose logs -f app"
  exit 1
fi
