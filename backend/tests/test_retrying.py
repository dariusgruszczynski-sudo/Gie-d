"""Ponawianie z backoffem (#28)."""
import pytest

from app.services.retrying import with_retries


def test_retries_then_succeeds():
    calls = {"n": 0}
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"
    assert with_retries(flaky, attempts=4, base_delay=0.01, sleep=lambda _: None) == "ok"
    assert calls["n"] == 3


def test_should_retry_false_raises_immediately():
    calls = {"n": 0}
    def bad():
        calls["n"] += 1
        raise ValueError("insufficient balance")
    with pytest.raises(ValueError):
        with_retries(bad, attempts=5, should_retry=lambda e: "insufficient" not in str(e), sleep=lambda _: None)
    assert calls["n"] == 1  # nie ponawiane


def test_exhausts_and_raises_last():
    def always():
        raise RuntimeError("down")
    with pytest.raises(RuntimeError):
        with_retries(always, attempts=3, base_delay=0.0, sleep=lambda _: None)
