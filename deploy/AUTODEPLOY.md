# Auto-deploy (pull-based) — jak włączyć, żeby serwer sam wdrażał zmiany

Cel: gdy Claude (z weba albo telefonu) wypchnie zmiany na gałąź deployową,
serwer **sam** je zaciąga i wdraża — bez SSH, bez terminala, bez otwierania
portów. Serwer co kilka minut sprawdza GitHuba (PULL) i odpala `deploy.sh`
tylko gdy pojawił się nowy commit.

To instalacja **jednorazowa** na serwerze (potrzebna raz, potem działa samo).

## Wariant A — systemd timer (zalecany)

```bash
cd /root/gie-d          # katalog repo na serwerze
chmod +x deploy/autopull.sh

# 1) Usługa: jedno wywołanie autopull.
sudo tee /etc/systemd/system/gield-autodeploy.service >/dev/null <<'UNIT'
[Unit]
Description=GielDarek auto-deploy (pull + deploy on new commit)
After=docker.service
Wants=docker.service

[Service]
Type=oneshot
WorkingDirectory=/root/gie-d
ExecStart=/root/gie-d/deploy/autopull.sh
UNIT

# 2) Timer: uruchamiaj usługę co 5 minut.
sudo tee /etc/systemd/system/gield-autodeploy.timer >/dev/null <<'UNIT'
[Unit]
Description=GielDarek auto-deploy co 5 minut

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Unit=gield-autodeploy.service

[Install]
WantedBy=timers.target
UNIT

# 3) Włącz.
sudo systemctl daemon-reload
sudo systemctl enable --now gield-autodeploy.timer

# Podgląd, że działa:
systemctl list-timers gield-autodeploy.timer
journalctl -u gield-autodeploy.service -f     # log wdrożeń
```

## Wariant B — cron (jeśli wolisz)

```bash
cd /root/gie-d && chmod +x deploy/autopull.sh
( crontab -l 2>/dev/null; \
  echo "*/5 * * * * cd /root/gie-d && ./deploy/autopull.sh >> /var/log/gield-autodeploy.log 2>&1" \
) | crontab -
```

## Jak to zmienia pracę

1. Zlecasz Claude'owi zmianę (np. z telefonowego Claude, repo podłączone).
2. Claude pisze kod, testuje, **pushuje** na gałąź `claude/automated-stock-trading-app-ulacio`.
3. W ciągu ≤5 min serwer sam zaciąga i wdraża (build + restart + health-check).
4. Jak deploy się wywali — zostaje działać poprzednia wersja, a powód jest w logu.

## Wyłączenie

```bash
sudo systemctl disable --now gield-autodeploy.timer   # wariant A
crontab -e   # usuń linię gield-autodeploy               (wariant B)
```

## Uwaga bezpieczeństwa

To PULL: serwer sięga do GitHuba i wdraża każdy commit z tej gałęzi. Deploy
biegnie z uprawnieniami użytkownika, który odpala timer/cron (u Ciebie root) —
tak samo jak gdy sam odpalasz `deploy.sh`. Nie udostępniasz nikomu SSH ani
kluczy; jedyne „zaufanie" to: co wejdzie na tę gałąź, to się wdroży. Gałąź jest
w Twoim repo, więc kontrolę masz przez to, komu pozwalasz do niej pushować.
