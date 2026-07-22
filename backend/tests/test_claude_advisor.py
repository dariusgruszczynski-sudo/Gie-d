from app.services.claude_advisor import ClaudeAdvisor


def _advisor(settings) -> ClaudeAdvisor:
    return ClaudeAdvisor(settings)


def _decide_kwargs():
    return dict(
        whitelist=["SPY"],
        market_data={"SPY": {"price": 500.0}},
        news=[],
        portfolio={"total_value_usdt": 1000.0},
        risk_context={},
        market_context={},
        trigger_reason="scheduled_daily",
    )


def test_hold_from_fast_model_never_escalates(settings, monkeypatch):
    advisor = _advisor(settings)
    calls = []

    def fake_call_model(model, tool, user_content, system):
        calls.append(model)
        return {"action": "HOLD", "symbol": None, "size_pct": 0, "confidence": 0.9, "reasoning": "spokój"}, 0.01, 100, 50

    monkeypatch.setattr(advisor, "_call_model", fake_call_model)

    decision = advisor.decide(**_decide_kwargs())

    assert calls == [settings.claude_model_fast]  # never escalated
    assert decision.action == "HOLD"
    assert decision.model_used == settings.claude_model_fast
    assert decision.cost_usd == 0.01


def test_confident_buy_from_fast_model_is_trusted_without_escalation(settings, monkeypatch):
    advisor = _advisor(settings)
    calls = []

    def fake_call_model(model, tool, user_content, system):
        calls.append(model)
        return {"action": "BUY", "symbol": "SPY", "size_pct": 10, "confidence": 0.9, "reasoning": "silny sygnał"}, 0.02, 200, 80

    monkeypatch.setattr(advisor, "_call_model", fake_call_model)

    decision = advisor.decide(**_decide_kwargs())

    assert calls == [settings.claude_model_fast]
    assert decision.action == "BUY"
    assert decision.model_used == settings.claude_model_fast
    assert decision.cost_usd == 0.02


def test_uncertain_buy_from_fast_model_escalates_to_opus(settings, monkeypatch):
    """This is the literal ask: "w przypadku wątpliwości zlecaj Opusowi
    decyzję" -- a low-confidence BUY/SELL from the fast model must trigger a
    second, final call to the (slower/pricier) escalation model, whose
    decision -- not the fast model's -- is what actually gets returned.
    Escalation is opt-in (lean-AI defaults it off), so enable it here."""
    advisor = _advisor(settings.model_copy(update={"claude_escalation_enabled": True}))
    calls = []

    def fake_call_model(model, tool, user_content, system):
        calls.append(model)
        if model == settings.claude_model_fast:
            return {"action": "BUY", "symbol": "SPY", "size_pct": 10, "confidence": 0.4, "reasoning": "niepewne"}, 0.02, 200, 80
        return {"action": "HOLD", "symbol": None, "size_pct": 0, "confidence": 0.85, "reasoning": "Opus mówi czekać"}, 0.05, 300, 100

    monkeypatch.setattr(advisor, "_call_model", fake_call_model)

    decision = advisor.decide(**_decide_kwargs())

    assert calls == [settings.claude_model_fast, settings.claude_model]
    assert decision.action == "HOLD"  # Opus's call wins, not the fast model's tentative BUY
    assert decision.model_used == settings.claude_model
    assert decision.cost_usd == 0.07  # both calls' cost summed
    assert decision.input_tokens == 500
    assert decision.output_tokens == 180


def test_uncertain_hold_never_escalates(settings, monkeypatch):
    """Only BUY/SELL uncertainty is worth Opus's cost -- a low-confidence HOLD
    has no action to second-guess, so escalating it would just burn budget."""
    advisor = _advisor(settings)
    calls = []

    def fake_call_model(model, tool, user_content, system):
        calls.append(model)
        return {"action": "HOLD", "symbol": None, "size_pct": 0, "confidence": 0.2, "reasoning": "brak przekonania"}, 0.01, 100, 50

    monkeypatch.setattr(advisor, "_call_model", fake_call_model)

    advisor.decide(**_decide_kwargs())

    assert calls == [settings.claude_model_fast]


def test_two_brains_pick_venue_specific_persona(settings, monkeypatch):
    """The extended venue must get the aggressive extended persona, the equities
    venue the medium-aggressive equities persona -- that's the whole "2 mózgi"
    split. We capture the system prompt handed to _call_model."""
    from app.services import claude_advisor

    advisor = _advisor(settings)
    captured = {}

    def fake_call_model(model, tool, user_content, system):
        captured["system"] = system
        return {"action": "HOLD", "symbol": None, "size_pct": 0, "confidence": 0.9, "reasoning": "ok"}, 0.01, 10, 5

    monkeypatch.setattr(advisor, "_call_model", fake_call_model)

    advisor.decide(**_decide_kwargs(), venue="extended")
    assert captured["system"] == claude_advisor.EXTENDED_PERSONA

    advisor.decide(**_decide_kwargs(), venue="alpaca")
    assert captured["system"] == claude_advisor.EQUITIES_PERSONA


def _pf_kwargs():
    return dict(
        whitelist=["SPY", "QQQ"],
        market_data={"SPY": {"price": 500.0}, "QQQ": {"price": 400.0}},
        news=[],
        portfolio={"total_value_usdt": 1000.0},
        risk_context={},
        market_context={},
        trigger_reason="scheduled_daily",
    )


def test_decide_portfolio_returns_multiple_actions(settings, monkeypatch):
    """Tryb PM: jedno wywołanie zwraca ZESTAW akcji na całej whiteliście.
    Koszt/tokeny całego (jednego) wywołania siedzą TYLKO na pierwszym elemencie,
    a teza całościowa jest doklejona do pierwszego uzasadnienia."""
    advisor = _advisor(settings)

    def fake_call_model(model, tool, user_content, system, max_tokens=1024):
        assert tool["name"] == "portfolio_decisions"
        return (
            {
                "actions": [
                    {"action": "BUY", "symbol": "SPY", "size_pct": 30, "confidence": 0.8, "reasoning": "trend"},
                    {"action": "BUY", "symbol": "QQQ", "size_pct": 20, "confidence": 0.7, "reasoning": "momentum"},
                ],
                "portfolio_thesis": "Rynek risk-on, dokładam ekspozycję.",
            },
            0.03,
            300,
            120,
        )

    monkeypatch.setattr(advisor, "_call_model", fake_call_model)
    out = advisor.decide_portfolio(**_pf_kwargs())

    assert [d.action for d in out] == ["BUY", "BUY"]
    assert [d.symbol for d in out] == ["SPY", "QQQ"]
    assert out[0].cost_usd == 0.03 and out[1].cost_usd == 0.0
    assert out[0].input_tokens == 300 and out[1].input_tokens == 0
    assert "Teza:" in out[0].reasoning  # thesis folded into the first action


def test_decide_portfolio_empty_actions_collapses_to_hold(settings, monkeypatch):
    """Pusta lista akcji (Claude świadomie nic nie robi) zwija się do jednej
    decyzji HOLD niosącej koszt wywołania -- żeby był wiersz do zaksięgowania
    kosztu i do powiadomienia 'czeka'."""
    advisor = _advisor(settings)

    def fake_call_model(model, tool, user_content, system, max_tokens=1024):
        return ({"actions": [], "portfolio_thesis": "Czekam na wyraźny sygnał."}, 0.01, 100, 40)

    monkeypatch.setattr(advisor, "_call_model", fake_call_model)
    out = advisor.decide_portfolio(**_pf_kwargs())

    assert len(out) == 1 and out[0].action == "HOLD"
    assert out[0].cost_usd == 0.01
    assert "Czekam" in out[0].reasoning
