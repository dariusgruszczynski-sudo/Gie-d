"""Rozdział realized nowa-era vs zaszłości (#40)."""
from app.services.realized_split import realized_split

EPOCH = "2026-11-11T00:00:00+00:00"


def _t(ts, sym, side, qty, price, pnl=None):
    d = {"timestamp": ts, "symbol": sym, "side": side, "quantity": qty, "price": price}
    if pnl is not None:
        d["pnl_usd"] = pnl
    return d


def test_split_by_epoch_uses_recorded_pnl():
    trades = [
        _t("2026-10-01T00:00:00+00:00", "HYPE/USD", "BUY", 10, 100),
        _t("2026-10-05T00:00:00+00:00", "HYPE/USD", "SELL", 10, 50, pnl=-500),   # legacy
        _t("2026-11-12T00:00:00+00:00", "BTC/USD", "BUY", 1, 60000),
        _t("2026-11-13T00:00:00+00:00", "BTC/USD", "SELL", 1, 63000, pnl=3000),  # epoch
    ]
    out = realized_split(trades, EPOCH)
    assert out["legacy_usd"] == -500.0 and out["legacy_count"] == 1
    assert out["epoch_usd"] == 3000.0 and out["epoch_count"] == 1
    assert out["all_usd"] == 2500.0


def test_split_computes_pnl_when_missing():
    # Brak pnl_usd -> liczone (cena-śr.koszt)*ilość. Kup 2@100, sprzedaj 2@150 = +100.
    trades = [
        _t("2026-11-12T00:00:00+00:00", "ETH/USD", "BUY", 2, 100),
        _t("2026-11-13T00:00:00+00:00", "ETH/USD", "SELL", 2, 150),
    ]
    out = realized_split(trades, EPOCH)
    assert out["epoch_usd"] == 100.0 and out["legacy_usd"] == 0.0


def test_none_epoch_counts_all_as_epoch():
    trades = [
        _t("2026-01-01T00:00:00+00:00", "BTC/USD", "BUY", 1, 100),
        _t("2026-01-02T00:00:00+00:00", "BTC/USD", "SELL", 1, 120, pnl=20),
    ]
    out = realized_split(trades, None)
    assert out["epoch_usd"] == 20.0 and out["legacy_usd"] == 0.0 and out["legacy_count"] == 0


def test_empty():
    out = realized_split([], EPOCH)
    assert out["all_usd"] == 0.0 and out["epoch_count"] == 0 and out["legacy_count"] == 0
