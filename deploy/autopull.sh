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

LOCAL="$(git rev-parse HEAD 2>/dev/null || echo none)"
REMOTE="$(git rev-parse "origin/$BRANCH")"

if [ "$LOCAL" = "$REMOTE" ]; then
  # Brak nowych commitów -- cisza (nie spamuj logu przy każdym cyklu).
  exit 0
fi

LOG "Nowa wersja na $BRANCH: $LOCAL -> $REMOTE. Wdrażam."
# deploy.sh sam robi checkout/reset --hard + build + restart + health-check.
if ./deploy/deploy.sh; then
  LOG "Deploy OK -> $(git rev-parse --short HEAD) $(git log -1 --format=%s)"
else
  LOG "DEPLOY NIEUDANY -- zostawiam poprzednią wersję działającą. Sprawdź: docker compose logs -f app"
  exit 1
fi
