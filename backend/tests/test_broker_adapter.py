"""Kontrakt brokera — zgodność KrakenClient + selektor venue."""
from app.services.broker_adapter import (
    BrokerAdapter,
    conforms,
    make_broker,
    missing_methods,
)
from app.services.kraken_client import KrakenClient


def test_kraken_client_conforms_to_contract():
    c = KrakenClient(transport=lambda *a: {"result": {}})
    assert conforms(c) is True
    assert missing_methods(c) == []
    assert isinstance(c, BrokerAdapter)   # runtime_checkable Protocol


def test_conforms_detects_missing():
    class Partial:
        def get_price(self, s): return 0.0
    assert conforms(Partial()) is False
    assert "place_market_order_quantity" in missing_methods(Partial())


def test_make_broker_kraken_returns_client():
    b = make_broker("kraken", transport=lambda *a: {"result": {}})
    assert isinstance(b, KrakenClient)


def test_make_broker_other_returns_none():
    # Noga Alpaca celowo NIE jest tu przepinana — zwracamy None.
    assert make_broker("alpaca") is None
    assert make_broker("") is None
