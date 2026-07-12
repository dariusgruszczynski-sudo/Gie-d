#!/usr/bin/env python3
"""Generuje parę kluczy VAPID do powiadomień Web Push (telefon / Apple Watch).

Odpal RAZ i wklej wypisane linie do ~/gie-d/.env na serwerze (nigdy do repo!),
potem zrestartuj apkę. Klucz publiczny trafia też do przeglądarki przy zapisie
subskrypcji -- ten sam, którego używa serwer do podpisywania wysyłek.

    docker compose exec -T app python scripts/gen_vapid.py

Format: base64url raw (P-256) -- to samo, czego oczekuje pywebpush po stronie
serwera i `applicationServerKey` po stronie przeglądarki.
"""

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def main() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())

    # Publiczny: nieskompresowany punkt EC (65 bajtów) -> applicationServerKey.
    pub_raw = private_key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    # Prywatny: surowy skalar 32-bajtowy, base64url -- akceptowany przez py_vapid.
    priv_raw = private_key.private_numbers().private_value.to_bytes(32, "big")

    print("# --- Wklej do .env (i zrestartuj apkę) ---")
    print(f"VAPID_PUBLIC_KEY={_b64url(pub_raw)}")
    print(f"VAPID_PRIVATE_KEY={_b64url(priv_raw)}")
    print("# VAPID_SUBJECT=mailto:twoj@email  # opcjonalnie, domyślnie już ustawiony")


if __name__ == "__main__":
    main()
