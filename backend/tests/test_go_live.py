"""Quest GO-LIVE (#1/#43): 6 kryteriów -> met/pending + licznik."""
from app.services.go_live import go_live_criteria


def test_go_live_early_state_mostly_pending():
    """Dzisiejszy stan: 0 trejdów -> trades/weeks/beats/edge niespełnione lub
    pending; drawdown 0% i koszt AI ok są spełnione."""
    out = go_live_criteria(closed_trades=0, weeks=1.0, beats_btc=None, expectancy_r=None,
                           max_dd_pct=0.0, ai_spend_usd=3.0)
    by = {c["key"]: c for c in out["criteria"]}
    assert out["total"] == 6 and out["go_live"] is False
    assert by["trades"]["met"] is False and by["beats_btc"]["pending"] is True
    assert by["drawdown"]["met"] is True and by["ai_cost"]["met"] is True
    assert out["met"] == 2


def test_go_live_all_green():
    out = go_live_criteria(closed_trades=60, weeks=4.0, beats_btc=True, expectancy_r=0.4,
                           max_dd_pct=12.0, ai_spend_usd=1.0)
    assert out["met"] == 6 and out["go_live"] is True


def test_go_live_blocks_verdicts_on_small_sample():
    """Nawet gdy beats_btc=True, ale próbka < 50 -> kryterium pending, nie met."""
    out = go_live_criteria(closed_trades=10, weeks=4.0, beats_btc=True, expectancy_r=0.5,
                           max_dd_pct=5.0, ai_spend_usd=1.0)
    by = {c["key"]: c for c in out["criteria"]}
    assert by["beats_btc"]["pending"] is True and by["beats_btc"]["met"] is False
    assert by["edge"]["pending"] is True
    assert out["go_live"] is False
