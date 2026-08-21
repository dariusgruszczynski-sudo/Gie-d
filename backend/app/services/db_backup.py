"""Automatyczna kopia zapasowa bazy SQLite.

Raz dziennie robi spójną migawkę pliku bazy przez natywne SQLite Online Backup
API (bezpieczne, gdy apka jednocześnie pisze -- w przeciwieństwie do zwykłego
`cp`, który może złapać bazę w pół transakcji). Trzyma ostatnie N kopii i kasuje
starsze. Best-effort: każdy błąd jest logowany, nigdy nie wywraca apki."""

import logging
import os
import sqlite3
from datetime import UTC, datetime

from app.config import Settings

logger = logging.getLogger(__name__)


def _sqlite_path(settings: Settings) -> str | None:
    """Ścieżka pliku bazy, jeśli to SQLite (jedyny wspierany silnik backupu)."""
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        return None
    raw = url[len("sqlite:///"):]
    if raw.startswith("./"):
        raw = raw[2:]
    return raw or None


def _backups_dir(db_path: str) -> str:
    return os.path.join(os.path.dirname(db_path) or ".", "backups")


def run_backup(settings: Settings) -> str | None:
    """Wykonuje jedną kopię i przycina stare. Zwraca ścieżkę kopii albo None
    (backup wyłączony / nie-SQLite / błąd). Nie rzuca wyjątków."""
    if not settings.db_backup_enabled:
        return None
    db_path = _sqlite_path(settings)
    if not db_path or not os.path.exists(db_path):
        return None
    dest_dir = _backups_dir(db_path)
    try:
        os.makedirs(dest_dir, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(dest_dir, f"trading-{stamp}.db")
        # Online Backup API: spójna kopia nawet przy równoległym zapisie.
        src = sqlite3.connect(db_path)
        try:
            dst = sqlite3.connect(dest)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        _prune(dest_dir, keep=max(1, settings.db_backup_keep))
        logger.info("Kopia bazy zapisana: %s", dest)
        return dest
    except Exception:
        logger.exception("Kopia bazy nie powiodła się")
        return None


def _prune(dest_dir: str, keep: int) -> None:
    """Zostaw `keep` najnowszych kopii, skasuj resztę (po nazwie = po czasie)."""
    try:
        files = sorted(
            (f for f in os.listdir(dest_dir) if f.startswith("trading-") and f.endswith(".db")),
            reverse=True,
        )
        for stale in files[keep:]:
            try:
                os.remove(os.path.join(dest_dir, stale))
            except OSError:
                logger.warning("Nie udało się skasować starej kopii %s", stale)
    except Exception:
        logger.warning("Przycinanie kopii bazy nie powiodło się", exc_info=True)
