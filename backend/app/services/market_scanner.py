"""Skaner rynku krypto 24/7 (wniosek #1/#2/#3).

Zamiast sztywnej 7-tki par: co cykl skanuje CAŁĄ handlowalną listę par USD Alpaki,
rankinguje po SILE (momentum + siła względem BTC), odfiltrowuje niską płynność i
zwraca TOP-K jako dynamiczne uniwersum handlowe. To przewaga „ręka na pulsie 24/7":
bot sam podstawia to, co realnie rośnie, zamiast obracać tych samych przegranych altów.

Separacja odpowiedzialności: skaner wybiera KTÓRE pary są kandydatami. O faktycznym
WEJŚCIU dalej decydują bramki silnika (reżim HTF, konfluencja ≥2/3, wybicie, ADX) i
cała ochrona ryzyka. Skaner nie składa zleceń.

Fail-safe: każdy błąd (brak listy, brak danych) -> fallback na statyczną
settings.crypto_symbols, żeby cykl nigdy nie został bez uniwersum."""

import logging

from app.config import Settings

logger = logging.getLogger(__name__)


def _daily_closes_vols(broker, symbol: str, bars: int) -> tuple[list[float], list[float]]:
    try:
        rows = broker.get_klines(symbol, interval="1d", limit=bars)
    except Exception:
        return [], []
    closes, vols = [], []
    for r in rows or []:
        try:
            closes.append(float(r[4]))
            vols.append(float(r[5]))
        except (IndexError, TypeError, ValueError):
            continue
    return closes, vols


def _momentum_pct(closes: list[float], days: int) -> float | None:
    if len(closes) < 2:
        return None
    ref = closes[-days] if len(closes) >= days else closes[0]
    last = closes[-1]
    if ref <= 0 or last <= 0:
        return None
    return (last - ref) / ref * 100.0


def _held_crypto(broker) -> set[str]:
    """Symbole krypto aktualnie trzymane (z salda brokera) — zawsze zostają w
    uniwersum, żeby silnik mógł nimi zarządzać / je zamknąć, nawet gdy wypadły z TOP-K."""
    try:
        balances = broker.get_account_balances()
    except Exception:
        return set()
    out = set()
    for sym, qty in (balances or {}).items():
        try:
            if "/" in str(sym) and float(qty) > 0:
                out.add(str(sym))
        except (TypeError, ValueError):
            continue
    return out


def scan_universe(broker, settings: Settings) -> list[str]:
    """Zwraca dynamiczne uniwersum handlowe krypto: TOP-K najsilniejszych płynnych
    par (ranking po momentum / sile vs BTC) ∪ aktualnie trzymane ∪ BTC. Fallback na
    settings.crypto_symbols przy jakimkolwiek problemie."""
    fallback = list(settings.crypto_symbols)
    if not getattr(settings, "crypto_scanner_enabled", False):
        return fallback

    held = _held_crypto(broker)
    try:
        pool = broker.list_crypto_symbols()
    except Exception:
        pool = []
    if not pool:
        logger.info("Skaner: pusta lista par z brokera — fallback na statyczne uniwersum")
        pool = list(fallback)
    pool = pool[: max(1, settings.crypto_scanner_max_scan)]

    mom_days = max(2, settings.crypto_scanner_momentum_days)
    bars = mom_days + 5
    btc_closes, _ = _daily_closes_vols(broker, "BTC/USD", bars)
    btc_mom = _momentum_pct(btc_closes, mom_days) or 0.0
    rs_vs_btc = bool(getattr(settings, "crypto_scanner_rs_vs_btc", True))
    min_dollar_vol = float(getattr(settings, "crypto_scanner_min_dollar_vol_usd", 0.0))

    scored: list[tuple[float, str]] = []
    for sym in pool:
        closes, vols = _daily_closes_vols(broker, sym, bars)
        if len(closes) < mom_days // 2:
            continue
        mom = _momentum_pct(closes, mom_days)
        if mom is None:
            continue
        # Płynność: średni dzienny obrót $ (close × wolumen). Trzymane zwolnione z
        # filtra (musimy móc je domknąć), reszta pod progiem odpada.
        if vols and min_dollar_vol > 0 and sym not in held:
            avg_dollar_vol = sum(c * v for c, v in zip(closes, vols)) / len(closes)
            if avg_dollar_vol < min_dollar_vol:
                continue
        score = mom - (btc_mom if rs_vs_btc else 0.0)  # #2: siła WZGLĘDEM BTC
        scored.append((score, sym))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[: max(1, settings.crypto_scanner_top_k)]]

    # Zawsze: TOP-K + trzymane (zarządzanie/wyjścia) + BTC jako kotwica. Dedup, kolejność stabilna.
    anchor = ["BTC/USD"] if "BTC/USD" in pool else []
    result = list(dict.fromkeys(top + sorted(held) + anchor))
    return result or fallback
