from app.services import whitelist_review


class FakeBroker:
    def __init__(self, prices, balances=None):
        self._prices = prices
        self._balances = balances or {"USD": 500.0}

    def get_price(self, symbol):
        if symbol not in self._prices:
            raise RuntimeError("no price")
        return self._prices[symbol]

    def get_account_balances(self):
        return dict(self._balances)


def test_select_keeps_affordable_cheapest_up_to_target(settings):
    s = settings.model_copy(update={"extended_max_share_price": 60.0, "extended_whitelist_target": 3})
    prices = {"XLF": 45.0, "GDX": 40.0, "SLV": 30.0, "XLE": 90.0, "TLT": 88.0}
    # 90/88 are over the $60 cap -> dropped; cheapest 3 of the rest kept.
    picked = whitelist_review.select_whitelist(prices, s)
    assert set(picked) == {"SLV", "GDX", "XLF"}
    assert "XLE" not in picked and "TLT" not in picked


def test_get_set_whitelist_roundtrip_and_seed_fallback(db_session, settings):
    # Empty DB -> falls back to the config seed.
    assert whitelist_review.get_extended_whitelist(db_session, settings) == settings.extended_whitelist_symbols
    whitelist_review.set_extended_whitelist(db_session, ["xlf", "gdx"])
    assert whitelist_review.get_extended_whitelist(db_session, settings) == ["XLF", "GDX"]


def test_run_review_updates_list_and_flags_held_removed(db_session, settings):
    s = settings.model_copy(update={
        "extended_candidate_pool": "XLF,GDX,SLV,XLE",
        "extended_max_share_price": 60.0,
        "extended_whitelist_target": 3,
    })
    whitelist_review.set_extended_whitelist(db_session, ["XLE", "GDX"])  # XLE currently held + on list
    broker = FakeBroker(
        prices={"XLF": 45.0, "GDX": 40.0, "SLV": 30.0, "XLE": 90.0},
        balances={"USD": 200.0, "XLE": 1.0},
    )
    result = whitelist_review.run_whitelist_review(db_session, s, broker, execute_push=False)

    assert set(result["whitelist"]) == {"XLF", "GDX", "SLV"}  # XLE dropped (too pricey)
    assert "XLF" in result["added"] and "SLV" in result["added"]
    assert result["removed"] == ["XLE"]
    assert result["removed_held"] == ["XLE"]  # held -> next pre-market force-closes it
    # Persisted.
    assert set(whitelist_review.get_extended_whitelist(db_session, s)) == {"XLF", "GDX", "SLV"}


def test_run_review_never_blanks_on_bad_data(db_session, settings):
    whitelist_review.set_extended_whitelist(db_session, ["XLF", "GDX"])
    broker = FakeBroker(prices={})  # every price fetch fails
    result = whitelist_review.run_whitelist_review(db_session, settings, broker, execute_push=False)
    # Empty pick -> keep the current whitelist rather than blanking it.
    assert result["whitelist"] == ["XLF", "GDX"]
