#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Domyka SUROWE porty apek (8001 fit-tracker, 8002 Nauka IT, 8090 Spiewnik),
# tak by dalo sie do nich dostac WYLACZNIE przez HTTPS (Caddy), a nie przez
# gole http://IP:port. Bezpieczne dla Caddy: przepuszcza ruch z sieci Dockera
# (Caddy siega apek przez host.docker.internal = 172.16/12), a blokuje resztę.
#
# Po kazdym porcie TESTUJE, czy jego subdomena HTTPS dalej dziala; jesli front
# padnie (502) -- AUTO-COFA regule dla tego portu, zeby nic nie zostalo zepsute.
#
# Uzycie (na serwerze, jako root):  bash deploy/harden-ports.sh
#   podglad bez zmian:              bash deploy/harden-ports.sh --dry-run
#   cofniecie wszystkiego:          bash deploy/harden-ports.sh --undo
# ---------------------------------------------------------------------------
set -uo pipefail

IP="46.225.229.113"
# port  -> subdomena HTTPS do testu
declare -A SUB=( [8001]="zdrowie" [8002]="it" [8090]="spiewnik" )
PORTS=(8001 8002 8090)
DOCKER_NET="172.16.0.0/12"

DRY=0; UNDO=0
for a in "$@"; do
  [ "$a" = "--dry-run" ] && DRY=1
  [ "$a" = "--undo" ] && UNDO=1
done

if [ "$(id -u)" != "0" ]; then echo "!! Uruchom jako root (sudo)."; exit 1; fi
command -v iptables >/dev/null || { echo "!! Brak iptables."; exit 1; }

rule() { # rule ACTION PORT  (ACTION: -I dodaj / -D usun)
  iptables "$1" DOCKER-USER -p tcp --dport "$2" ! -s "$DOCKER_NET" -j DROP 2>/dev/null
}
has_rule() { iptables -C DOCKER-USER -p tcp --dport "$1" ! -s "$DOCKER_NET" -j DROP 2>/dev/null; }
https_code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "https://${SUB[$1]}.${IP}.sslip.io/" 2>/dev/null || echo 000; }
raw_code()   { curl -s -o /dev/null -m 5 -w '%{http_code}' "http://${IP}:${1}/" 2>/dev/null || echo 000; }

if [ "$UNDO" = 1 ]; then
  echo "== COFAM reguly =="
  for p in "${PORTS[@]}"; do
    while has_rule "$p"; do rule -D "$p"; done
    echo "  $p: reguly usuniete"
  done
  echo "Gotowe. (Jesli zapisywales netfilter-persistent, zapisz ponownie.)"
  exit 0
fi

echo "== Stan PRZED =="
for p in "${PORTS[@]}"; do echo "  raw $p: $(raw_code "$p")   https ${SUB[$p]}: $(https_code "$p")"; done

if [ "$DRY" = 1 ]; then echo; echo "(--dry-run: nic nie zmieniam)"; exit 0; fi

echo; echo "== Nakladam reguly (blokuj z zewnatrz, przepuszczaj Caddy) =="
for p in "${PORTS[@]}"; do
  if has_rule "$p"; then echo "  $p: regula juz jest, pomijam"; continue; fi
  rule -I "$p"
  sleep 2
  hc="$(https_code "$p")"
  if [ "$hc" = "502" ] || [ "$hc" = "000" ]; then
    echo "  $p: !! HTTPS padl ($hc) -> COFAM regule (ta apka to zapewne proces hosta, nie Docker)"
    rule -D "$p"
  else
    echo "  $p: OK -> raw $(raw_code "$p") (z serwera moze byc mylace), https $hc"
  fi
done

echo; echo "== Stan PO =="
for p in "${PORTS[@]}"; do echo "  raw $p: $(raw_code "$p")   https ${SUB[$p]}: $(https_code "$p")"; done

cat <<'EOF'

WAZNE:
- Miarodajny test "czy raw zamkniety" zrob Z INNEJ SIECI (np. z telefonu na LTE),
  bo z samego serwera ruch potrafi ominac reguly FORWARD i pokazywac port jako
  otwarty, mimo ze z zewnatrz jest juz zamkniety.
- Utrwal reguly na restart:
    apt install -y iptables-persistent && netfilter-persistent save
- Cofniecie wszystkiego:  bash deploy/harden-ports.sh --undo
EOF
