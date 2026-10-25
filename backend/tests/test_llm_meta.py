"""#11 Meta-uczeń LLM: guardy (próbka/budżet), zapis wniosku, zero mutacji knobów.
Fake advisor — ZERO realnych wywołań API (sandbox nie ma sieci; nie palimy budżetu)."""
import json
from datetime import UTC, datetime

from app.models import Decision, Trade, TradeAction, TradeMode
from app.services import llm_meta, risk_manager


class FakeMetaAdvisor:
    def __init__(self): self.called = 0
    def review_learning(self, summary):
        self.called += 1
        self.last_summary = summary
        return ({"working": "trend above", "bleeding": "rsi>=70", "proposed_change": "x",
                 "rationale": "dane", "confidence": 0.3}, 0.002, 1000, 200)


def _close(db, sym, buy, sell, dopen, dsell):
    d = Decision(timestamp=dopen, symbol=sym, action=TradeAction.BUY, size_pct=10.0, confidence=1.0,
                 reasoning="x", market_data_snapshot=json.dumps({sym: {"technical": {"sma50_vs_sma200_1h": "above", "rsi_14": 55}}}),
                 venue="crypto", executed=True)
    db.add(d); db.commit(); db.refresh(d)
    db.add(Trade(timestamp=dopen, symbol=sym, side="BUY", quantity=1.0, price=float(buy), usdt_value=float(buy), mode=TradeMode.LIVE, venue="crypto", decision_id=d.id))
    db.add(Trade(timestamp=dsell, symbol=sym, side="SELL", quantity=1.0, price=float(sell), usdt_value=float(sell), mode=TradeMode.LIVE, venue="crypto"))
    db.commit()


def test_meta_review_skips_small_sample(db_session, settings):
    adv = FakeMetaAdvisor()
    res = llm_meta.run_meta_review(db_session, settings, adv, venue="crypto", min_closes=20)
    assert "skipped" in res and adv.called == 0  # za mała próbka -> nie płacimy za LLM


def test_meta_review_runs_and_stores_insight(db_session, settings):
    s = settings.model_copy(update={"crypto_stats_epoch_default": "2026-10-16T00:00:00+00:00"})
    for i in range(6):
        _close(db_session, f"C{i}/USD", 100, 100 + i, datetime(2026, 10, 20 + i % 5, tzinfo=UTC), datetime(2026, 10, 20 + i % 5, 12, tzinfo=UTC))
    adv = FakeMetaAdvisor()
    res = llm_meta.run_meta_review(db_session, s, adv, venue="crypto", min_closes=5)
    assert adv.called == 1
    assert res["proposed_change"] == "x" and res["based_on_closes"] == 6
    # Zapisane w stanie -> widoczne dla UI/nadzoru.
    stored = llm_meta.latest_insight(db_session)
    assert stored and stored["proposed_change"] == "x"
    # Meta-uczeń NIE zmienia knobów (tylko proponuje) — stan handlu nietknięty.
    assert risk_manager.get_state(db_session).is_halted is False
