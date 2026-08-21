"""Friday auto-review of the POZA SESJĄ (extended-hours) ETF whitelist.

Runs after the after-market close each Friday. From a curated pool of cheap,
liquid, non-leveraged ETFs it re-picks the whitelist that actually fits the
budget (WHOLE shares must be affordable), drops names that got too expensive or
were removed, and adds new ones. The list lives in the DB (SystemState.
extended_whitelist_json) so changes take effect without a redeploy.

IMPORTANT -- execution is NOT done here: the market is closed Friday night, so
placing a sell would just be rejected. Instead the review only UPDATES the list;
a removed-and-held position is force-closed automatically by the existing
mechanical exit (check_take_profit_stop_loss force-closes anything held that's
no longer on the whitelist) at the next pre-market. That keeps this job pure
bookkeeping + one optional Claude call, never a live order at a closed market.
"""

import json
import logging

from sqlalchemy.orm import Session

from app.config import Settings
from app.services import push_notifier, risk_manager

logger = logging.getLogger(__name__)


def get_extended_whitelist(db: Session, settings: Settings) -> list[str]:
    """The live extended whitelist: the DB-managed list if set, else the config
    seed. This is what the extended cycle should trade."""
    state = risk_manager.get_state(db)
    raw = (state.extended_whitelist_json or "").strip()
    if raw:
        try:
            stored = [str(s).strip().upper() for s in json.loads(raw) if str(s).strip()]
            if stored:
                return stored
        except (TypeError, ValueError):
            logger.warning("Bad extended_whitelist_json, falling back to config seed", exc_info=True)
    return settings.extended_whitelist_symbols


def set_extended_whitelist(db: Session, symbols: list[str]) -> None:
    state = risk_manager.get_state(db)
    state.extended_whitelist_json = json.dumps([s.strip().upper() for s in symbols if s.strip()])
    db.commit()


def _affordable(price: float | None, cap: float) -> bool:
    return price is not None and 0 < price <= cap


def select_whitelist(prices: dict[str, float], settings: Settings) -> list[str]:
    """Mechanical pick: from the priced candidate pool keep the AFFORDABLE ones
    (whole share <= cap), preferring the cheapest (more names fit the budget),
    up to the target size. Deterministic -- the Claude layer (optional) only
    reorders/curates within this affordable set."""
    cap = settings.extended_max_share_price
    affordable = [(sym, p) for sym, p in prices.items() if _affordable(p, cap)]
    affordable.sort(key=lambda kv: kv[1])  # cheapest first
    return [sym for sym, _ in affordable[: settings.extended_whitelist_target]]


def run_whitelist_review(db: Session, settings: Settings, broker, *, execute_push: bool = True) -> dict:
    """Re-pick the extended whitelist from live candidate prices, persist it, and
    push a summary. Returns {kept, added, removed, removed_held, whitelist}.
    Removed-and-held names are sold by the next pre-market force-close, not here."""
    current = get_extended_whitelist(db, settings)
    pool = settings.extended_candidate_pool_symbols

    prices: dict[str, float] = {}
    for sym in pool:
        try:
            prices[sym] = float(broker.get_price(sym))
        except Exception:
            logger.warning("Whitelist review: price failed for %s, skipping candidate", sym, exc_info=True)

    new_list = select_whitelist(prices, settings)
    if not new_list:
        # Never blank the whitelist on a bad data day -- keep whatever we had.
        logger.warning("Whitelist review produced an empty list; keeping the current whitelist")
        return {"kept": current, "added": [], "removed": [], "removed_held": [], "whitelist": current}

    added = [s for s in new_list if s not in current]
    removed = [s for s in current if s not in new_list]

    held: set[str] = set()
    try:
        balances = broker.get_account_balances()
        held = {k for k, v in balances.items() if k != settings.quote_currency and (v or 0) > 0}
    except Exception:
        logger.warning("Whitelist review: balances failed, can't flag held-removed names", exc_info=True)
    removed_held = [s for s in removed if s in held]

    set_extended_whitelist(db, new_list)
    _log_review(db, added, removed, removed_held)

    if execute_push:
        try:
            _push_summary(db, settings, added, removed, removed_held, new_list)
        except Exception:
            logger.warning("Whitelist review push failed", exc_info=True)

    return {"kept": new_list, "added": added, "removed": removed, "removed_held": removed_held, "whitelist": new_list}


def _log_review(db: Session, added: list[str], removed: list[str], removed_held: list[str]) -> None:
    from app.models import RiskEvent

    detail = f"dodano={added or '-'} wyrzucono={removed or '-'} do_sprzedania={removed_held or '-'}"
    db.add(RiskEvent(event_type="whitelist_review", details=detail))
    db.commit()


def _push_summary(db, settings, added, removed, removed_held, whitelist) -> None:
    if not push_notifier.push_configured(settings):
        return
    parts = [f"Przegląd whitelisty POZA SESJĄ ({len(whitelist)} ETF)"]
    if added:
        parts.append("➕ " + ", ".join(added))
    if removed:
        sell_note = f" (sprzedaż w pre-market: {', '.join(removed_held)})" if removed_held else ""
        parts.append("➖ " + ", ".join(removed) + sell_note)
    if not added and not removed:
        parts.append("bez zmian")
    push_notifier.send_to_all(db, settings, title="GielDarek — whitelist", body=" · ".join(parts))
