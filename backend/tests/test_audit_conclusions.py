"""Uczciwość auto-wniosków audytu (U6): nagłówek-prawda na górze i werdykt edge
po WIELKOŚCI — cienki dodatni edge to nie triumf „edge dodatni", tylko szum."""

from datetime import UTC, datetime, timedelta

from app.api.routes_dashboard import get_audit
from app.models import Trade, TradeMode


def _roundtrip(db, sym, buy_px, sell_px, day):
    t0 = datetime(2026, 9, 1, tzinfo=UTC) + timedelta(days=day)
    db.add(Trade(timestamp=t0, symbol=sym, side="BUY", quantity=1.0, price=buy_px,
                 usdt_value=buy_px, mode=TradeMode.LIVE, venue="alpaca"))
    db.add(Trade(timestamp=t0 + timedelta(days=1), symbol=sym, side="SELL", quantity=1.0,
                 price=sell_px, usdt_value=sell_px, mode=TradeMode.LIVE, venue="alpaca"))


def test_headline_first_and_thin_edge_not_triumphant(db_session, settings):
    # 2 mikrowygrane + 1 mikrostrata -> per_trade ~ +$0.05 (cienki, dodatni).
    _roundtrip(db_session, "AAA", 100.0, 100.10, 0)
    _roundtrip(db_session, "BBB", 100.0, 100.10, 5)
    _roundtrip(db_session, "CCC", 100.0, 99.95, 10)
    db_session.commit()

    audit = get_audit(db=db_session, settings=settings)
    concl = audit["conclusions"]
    texts = [c["t"] for c in concl]

    # Nagłówek-prawda jest PIERWSZY.
    assert texts and texts[0].startswith("Wynik zamkniętych transakcji")
    # Mikrowynik -> „drepcze w miejscu", nie „zarabia".
    assert "drepcze w miejscu" in texts[0]
    # Cienki edge NIE może być reklamowany jako pewny „edge dodatni.".
    joined = " ".join(texts)
    assert "edge dodatni." not in joined
    assert "ledwo dodatni" in joined


def test_too_few_trades_says_so(db_session, settings):
    _roundtrip(db_session, "AAA", 100.0, 101.0, 0)
    db_session.commit()
    audit = get_audit(db=db_session, settings=settings)
    assert any("Za mało zamkniętych" in c["t"] for c in audit["conclusions"])
