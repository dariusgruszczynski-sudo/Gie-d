"""Runtime-owe klucze Alpaca z panelu (override) + ochrona sekretów w serializacji."""

from app.config import Settings
from app.serialization import serialize
from app.services import broker_credentials, risk_manager


def test_apply_override_sets_keys_and_forces_paper(db_session):
    state = risk_manager.get_state(db_session)
    state.alpaca_api_key_override = "PKTESTKEY"
    state.alpaca_api_secret_override = "secretvalue"
    db_session.commit()

    s = Settings(alpaca_api_key="old", alpaca_api_secret="old", alpaca_paper=False)
    applied = broker_credentials.apply_override(db_session, s)

    assert applied is True
    assert s.alpaca_api_key == "PKTESTKEY"
    assert s.alpaca_api_secret == "secretvalue"
    assert s.alpaca_paper is True


def test_apply_override_noop_when_unset(db_session):
    s = Settings(alpaca_api_key="envkey", alpaca_api_secret="envsecret")
    assert broker_credentials.apply_override(db_session, s) is False
    assert s.alpaca_api_key == "envkey"  # env nietknięte


def test_set_override_persists(db_session):
    s = Settings()
    broker_credentials.set_override(db_session, " PKNEW ", " sek ")  # spacje przycinane
    state = risk_manager.get_state(db_session)
    assert state.alpaca_api_key_override == "PKNEW"
    assert state.alpaca_api_secret_override == "sek"
    assert broker_credentials.apply_override(db_session, s) is True
    assert s.alpaca_api_key == "PKNEW"


def test_serialize_hides_secrets(db_session):
    state = risk_manager.get_state(db_session)
    state.session_secret = "topsecretcookiekey"
    state.alpaca_api_key_override = "PKLEAK"
    state.alpaca_api_secret_override = "SEKLEAK"
    db_session.commit()
    blob = serialize(state)
    assert "session_secret" not in blob
    assert "alpaca_api_key_override" not in blob
    assert "alpaca_api_secret_override" not in blob
    assert "PKLEAK" not in blob.values() and "SEKLEAK" not in blob.values()
