"""Opus-kontroler (P1/P2): override-store z klamrami anty-bug, aplikacja knobów,
baza wiedzy, codzienny przebieg (stub modelu) i env-seed z trwałym kill-switchem."""

from app.services import opus_controller as oc
from app.services import risk_manager


def test_clamp_ranges_and_int_coercion():
    assert oc._clamp("risk_per_trade_pct", 999) == 6.0        # sufit anty-bug
    assert oc._clamp("risk_per_trade_pct", -5) == 0.5         # podłoga
    assert oc._clamp("max_new_positions_per_day", 3.7) == 4   # int
    assert oc._clamp("min_buy_confidence", "0.55") == 0.55    # string->float
    assert oc._clamp("min_buy_confidence", "abc") is None     # śmieci
    assert oc._clamp("nieistniejacy_knob", 1) is None         # nieznany knob


def test_apply_overrides_model_copy(db_session, settings):
    oc.set_overrides(db_session, {"min_buy_confidence": 0.50, "max_new_positions_per_day": 4, "bogus": 1})
    eff = oc.apply_knob_overrides(db_session, settings)
    assert eff.min_buy_confidence == 0.50
    assert eff.max_new_positions_per_day == 4
    # oryginał nietknięty (model_copy), nieznany knob pominięty
    assert not hasattr(eff, "bogus")


def test_apply_overrides_noop_when_empty(db_session, settings):
    assert oc.apply_knob_overrides(db_session, settings) is settings


def test_set_overrides_clamps_and_merges(db_session):
    a = oc.set_overrides(db_session, {"hard_take_profit_pct": 999})
    assert a["hard_take_profit_pct"] == 25.0
    oc.set_overrides(db_session, {"stop_loss_min_pct": 2.0})
    ov = oc.get_overrides(db_session)
    assert ov["hard_take_profit_pct"] == 25.0 and ov["stop_loss_min_pct"] == 2.0


def test_run_controller_disabled_is_noop(db_session, settings):
    res = oc.run_opus_controller(db_session, settings, generate=lambda s, p: "{}")
    assert res["ran"] is False and res["reason"] == "disabled"


def test_run_controller_applies_knobs_and_knowledge(db_session, settings):
    state = risk_manager.get_state(db_session)
    state.opus_controller_enabled = True
    db_session.commit()
    stub = lambda s, p: '{"knobs": {"min_buy_confidence": 0.55, "risk_per_trade_pct": 999, "bogus": 7}, "lessons": ["momentum dziala, mean-reversion nie"]}'  # noqa: E731
    res = oc.run_opus_controller(db_session, settings, generate=stub)
    assert res["ran"] is True
    assert res["applied"]["min_buy_confidence"] == 0.55
    assert res["applied"]["risk_per_trade_pct"] == 6.0   # sklamrowane
    assert "bogus" not in res["applied"]
    assert oc.get_knowledge(db_session) == ["momentum dziala, mean-reversion nie"]
    # drugi przebieg tego samego dnia — throttle
    res2 = oc.run_opus_controller(db_session, settings, generate=stub)
    assert res2["ran"] is False and res2["reason"] == "already_ran_today"


def test_seed_from_env_respects_manual_override(db_session, settings):
    env_on = settings.model_copy(update={"opus_controller_enabled": True})
    oc.seed_enabled_from_env(db_session, env_on)
    assert risk_manager.get_state(db_session).opus_controller_enabled is True
    # właściciel wyłącza ręcznie -> user_set; seed już nie włączy z powrotem
    st = risk_manager.get_state(db_session)
    st.opus_controller_enabled = False
    st.opus_controller_user_set = True
    db_session.commit()
    oc.seed_enabled_from_env(db_session, env_on)
    assert risk_manager.get_state(db_session).opus_controller_enabled is False


def test_apply_overrides_enforces_cross_knob_coherence(db_session, settings):
    # Opus ustawia sprzeczną parę: stop_min > stop_max, cap < próg, conv < risk
    oc.set_overrides(db_session, {
        "stop_loss_min_pct": 8.0, "stop_loss_max_pct": 3.0,
        "min_buy_confidence": 0.80, "progressive_confidence_cap": 0.60,
        "risk_per_trade_pct": 6.0, "conviction_max_risk_per_trade_pct": 1.0,
    })
    eff = oc.apply_knob_overrides(db_session, settings)
    # „górna" wartość podniesiona do „dolnej" — niezmienniki trzymają
    assert eff.stop_loss_max_pct >= eff.stop_loss_min_pct == 8.0
    assert eff.progressive_confidence_cap >= eff.min_buy_confidence == 0.80
    assert eff.conviction_max_risk_per_trade_pct >= eff.risk_per_trade_pct == 6.0
