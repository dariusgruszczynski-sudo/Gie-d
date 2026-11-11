"""SHADOW-LLM: ocena zalogowanych rekomendacji Claude (bez handlu) — czy BUY-e
wyprzedzają HOLD-y na zwrocie forward. Czysto odczytowe."""
from datetime import UTC, datetime, timedelta

from app.models import LlmShadowRec
from app.services import llm_shadow


def _rec(db, sym, when, action, price):
    db.add(LlmShadowRec(timestamp=when, venue="crypto", symbol=sym, action=action,
                        confidence=0.7, size_pct=10.0, price_at=price, reasoning="x"))


def test_shadow_report_empty_disabled(db_session, settings):
    out = llm_shadow.shadow_report(db_session, settings, venue="crypto")
    assert out["status"] == "disabled" and out["total_recs"] == 0 and out["scored_buys"] == 0
    assert out["enabled"] is False


def test_shadow_report_buys_beat_holds(db_session, settings):
    """5 BUY-ów, których cena rośnie +10% w horyzoncie, vs 5 HOLD-ów, które spadają
    −10% -> buy_beats_hold=True, trafność BUY 100%. Każdy drugi wpis (punkt
    forward) sam nie ma już późniejszego punktu, więc nie zakłóca liczenia."""
    t0 = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)
    fut = t0 + timedelta(hours=25)  # > horizon 24h
    for i in range(5):
        _rec(db_session, f"B{i}/USD", t0, "BUY", 100.0)
        _rec(db_session, f"B{i}/USD", fut, "HOLD", 110.0)   # +10% forward dla BUY
        _rec(db_session, f"H{i}/USD", t0, "HOLD", 100.0)
        _rec(db_session, f"H{i}/USD", fut, "BUY", 90.0)     # −10% forward dla HOLD
    db_session.commit()

    out = llm_shadow.shadow_report(db_session, settings, venue="crypto", horizon_hours=24, min_scored=5)
    assert out["status"] == "ok"
    assert out["scored_buys"] == 5 and out["scored_holds"] == 5
    assert out["buy_avg_fwd_pct"] == 10.0 and out["hold_avg_fwd_pct"] == -10.0
    assert out["buy_win_rate"] == 100.0
    assert out["buy_beats_hold"] is True


def test_shadow_report_insufficient_sample(db_session, settings):
    """Za mało ocenionych BUY-ów -> insufficient_data (nie orzekamy na garści)."""
    t0 = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)
    fut = t0 + timedelta(hours=25)
    _rec(db_session, "B0/USD", t0, "BUY", 100.0)
    _rec(db_session, "B0/USD", fut, "HOLD", 105.0)
    db_session.commit()
    out = llm_shadow.shadow_report(db_session, settings, venue="crypto", horizon_hours=24, min_scored=5)
    assert out["status"] == "insufficient_data" and out["scored_buys"] == 1
