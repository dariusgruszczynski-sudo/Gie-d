import enum
from datetime import datetime

# Kolumny, które NIGDY nie wychodzą przez API (sekrety). serialize() jest używany
# m.in. przez /api/control/* (np. /pause zwraca cały SystemState), więc gołe
# wypisanie wszystkich kolumn wyciekłoby klucz podpisujący cookie i klucze Alpaki.
_SENSITIVE_COLUMNS = frozenset({
    "session_secret",
    "alpaca_api_key_override",
    "alpaca_api_secret_override",
})


def serialize(obj) -> dict:
    """Minimal SQLAlchemy model -> JSON-safe dict converter for our read-only
    dashboard endpoints (avoids hand-writing a Pydantic schema per model).
    Wrażliwe kolumny (sekrety) są POMIJANE -- nigdy nie trafiają do odpowiedzi."""
    data = {}
    for column in obj.__table__.columns:
        if column.name in _SENSITIVE_COLUMNS:
            continue
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, enum.Enum):
            value = value.value
        data[column.name] = value
    return data
