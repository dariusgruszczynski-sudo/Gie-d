import enum
from datetime import datetime


def serialize(obj) -> dict:
    """Minimal SQLAlchemy model -> JSON-safe dict converter for our read-only
    dashboard endpoints (avoids hand-writing a Pydantic schema per model)."""
    data = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, enum.Enum):
            value = value.value
        data[column.name] = value
    return data
