"""Anty-dryf: każdy knob, który deploy.sh wpisuje do .env, MUSI istnieć jako pole
w Settings. deploy.sh wymusza ~40 parametrów ręcznie (bo .env nadpisuje kod), a
config.py ma własne domyślne — literówka albo zmiana nazwy pola po jednej stronie
znaczy, że knob po cichu NIE wchodzi (albo wchodzi jako śmieć ignorowany przez
`extra=ignore`). Ten test łapie taki rozjazd zanim trafi na żywą kasę."""

import re
from pathlib import Path

from app.config import Settings

DEPLOY_SH = Path(__file__).resolve().parents[2] / "deploy" / "deploy.sh"

# Klucze ustawiane przez deploy.sh, które celowo NIE są polami Settings
# (stemple build/proxy, nie konfiguracja aplikacji). Trzymamy jawnie, żeby nowy
# nie-Settings knob był świadomą decyzją, nie przypadkiem.
_NON_SETTINGS_KEYS: set[str] = set()


def _deploy_knob_keys() -> set[str]:
    text = DEPLOY_SH.read_text(encoding="utf-8")
    # Tylko REALNE wywołania: `setenv KEY value "$f"` na początku linii (po wcięciu).
    # Definicja funkcji `setenv() { ... }` i komentarze się nie łapią.
    keys = set()
    for m in re.finditer(r"^\s*setenv\s+([A-Z][A-Z0-9_]+)\s+\S", text, re.MULTILINE):
        keys.add(m.group(1))
    return keys


def test_deploy_sh_has_knobs():
    """Sanity: w ogóle znaleźliśmy knoby (regex/ścieżka nie zgniły)."""
    assert len(_deploy_knob_keys()) > 20


def test_every_deploy_knob_is_a_real_settings_field():
    fields = set(Settings.model_fields.keys())
    unknown = {k for k in _deploy_knob_keys() if k.lower() not in fields and k not in _NON_SETTINGS_KEYS}
    assert not unknown, (
        "deploy.sh ustawia knoby, których NIE ma w Settings (literówka / zmiana nazwy? "
        f"knob nie wejdzie w życie): {sorted(unknown)}"
    )
