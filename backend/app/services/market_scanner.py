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
import time

from app.config import Settings

logger = logging.getLogger(__name__)

# Stablecoiny / pegi USD — WYKLUCZONE ze skanera: momentum peg-a ~$1 to szum, a na
# obrót venue potrafią wyjść na szczyt listy (USDC/USDT/USDG) i zaśmiecać ranking.
# Tokeny towarowe (PAXG/XAUT — złoto) ZOSTAJĄ: realnie trendują.
_STABLES = {"USDC", "USDT", "USDG", "DAI", "PYUSD", "USDP", "TUSD", "GUSD", "USDD", "FDUSD"}

# Cache rankingu (audyt Partia 5 — efektywność): momentum 30-dniowe to WOLNY
# sygnał, a cykl krypto biega co ~15 min. Bez cache skaner pobierał dzienne świece
# dla ~40 par KAŻDY cykl (~96×/dobę) — marnotrawstwo API i ryzyko limitów. Trzymamy
# ostatni ranking per SYGNATURA wejścia (pula+parametry) na crypto_scanner_cache_min
# minut; trzymane pozycje i BTC domykamy ZAWSZE świeżo (one zmieniają się szybko).
_RANK_CACHE: dict[tuple, tuple[float, list[str]]] = {}


def _reset_cache() -> None:
    """Czyści cache rankingu (dla testów / ręcznego wymuszenia świeżego skanu)."""
    _RANK_CACHE.clear()


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


def _liquidity_summary(liq: dict[str, float]) -> dict:
    """Rozkład średniego dziennego obrotu $ po parach (audyt: do dobrania progu
    płynności z DANYCH, nie na oko). Zwraca min/p25/mediana/p75/max + top-12 par."""
    vals = sorted(liq.values())
    if not vals:
        return {}
    n = len(vals)

    def q(p: float) -> float:
        if n == 1:
            return vals[0]
        i = min(n - 1, max(0, int(round(p * (n - 1)))))
        return vals[i]

    top = sorted(liq.items(), key=lambda kv: kv[1], reverse=True)[:12]
    return {
        "count": n,
        "min_usd": round(vals[0]),
        "p25_usd": round(q(0.25)),
        "median_usd": round(q(0.50)),
        "p75_usd": round(q(0.75)),
        "max_usd": round(vals[-1]),
        "top": [[s, round(v)] for s, v in top],
    }


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
    return scan_universe_report(broker, settings)["universe"]


def scan_universe_report(broker, settings: Settings) -> dict:
    """Jak scan_universe, ale zwraca też DIAGNOSTYKĘ (obserwowalność — audyt): ile
    par realnie daje broker, ile przeszło ranking, czy zadziałał fallback i dlaczego.
    Bez tego nie dało się z zewnątrz stwierdzić, czy skaner naprawdę poszerza
    uniwersum, czy po cichu siedzi na statycznej 7-tce. Zwraca:
      {universe, pool_size, scanned, scored, top, fell_back, reason, cached}."""
    fallback = list(settings.crypto_symbols)

    def _report(universe, *, pool_size=0, scanned=0, scored=0, top=None,
                fell_back=False, reason="", cached=False, skips=None, liquidity=None) -> dict:
        return {
            "universe": universe or fallback, "pool_size": pool_size, "scanned": scanned,
            "scored": scored, "top": top or [], "fell_back": fell_back, "reason": reason,
            "cached": cached, "skips": skips or {}, "liquidity": liquidity or {},
        }

    if not getattr(settings, "crypto_scanner_enabled", False):
        return _report(fallback, fell_back=True, reason="skaner wyłączony")

    held = _held_crypto(broker)
    try:
        pool_raw = broker.list_crypto_symbols()
    except Exception:
        logger.warning("Skaner: list_crypto_symbols rzucił wyjątek — fallback", exc_info=True)
        return _report(fallback, fell_back=True, reason="broker.list_crypto_symbols błąd")
    pool_size = len(pool_raw or [])
    fell_back = not pool_raw
    if not pool_raw:
        logger.info("Skaner: pusta lista par z brokera — fallback na statyczne uniwersum")
        pool_raw = list(fallback)
    pool = pool_raw[: max(1, settings.crypto_scanner_max_scan)]

    # CACHE: w obrębie crypto_scanner_cache_min minut nie przeliczamy rankingu od
    # nowa (oszczędza ~40 fetchy/cykl). Trzymane i BTC i tak domykamy świeżo niżej.
    cache_min = float(getattr(settings, "crypto_scanner_cache_min", 0.0) or 0.0)
    sig = (
        tuple(sorted(pool)), settings.crypto_scanner_top_k, settings.crypto_scanner_momentum_days,
        float(getattr(settings, "crypto_scanner_min_dollar_vol_usd", 0.0)),
        bool(getattr(settings, "crypto_scanner_rs_vs_btc", True)),
    )
    now = time.monotonic()
    if cache_min > 0:
        hit = _RANK_CACHE.get(sig)
        if hit is not None and now < hit[0]:
            anchor = ["BTC/USD"] if "BTC/USD" in pool else []
            uni = list(dict.fromkeys(hit[1] + sorted(held) + anchor))
            return _report(uni, pool_size=pool_size, scanned=len(pool), scored=len(hit[1]),
                           top=hit[1], fell_back=fell_back, reason="cache", cached=True)

    mom_days = max(2, settings.crypto_scanner_momentum_days)
    bars = mom_days + 5
    btc_closes, _ = _daily_closes_vols(broker, "BTC/USD", bars)
    btc_mom = _momentum_pct(btc_closes, mom_days) or 0.0
    rs_vs_btc = bool(getattr(settings, "crypto_scanner_rs_vs_btc", True))
    min_dollar_vol = float(getattr(settings, "crypto_scanner_min_dollar_vol_usd", 0.0))

    # Liczniki powodów odrzucenia (audyt: żeby wiedzieć, CO dławi ranking —
    # za mało świec / brak momentum / za cienka płynność).
    skips = {"stablecoin": 0, "too_few_bars": 0, "no_momentum": 0, "illiquid": 0}
    liq: dict[str, float] = {}   # sym -> śr. dzienny obrót $ (dla WSZYSTKICH z danymi)
    scored: list[tuple[float, str]] = []
    for sym in pool:
        if str(sym).split("/")[0].upper() in _STABLES:
            skips["stablecoin"] += 1
            continue
        closes, vols = _daily_closes_vols(broker, sym, bars)
        if len(closes) < mom_days // 2:
            skips["too_few_bars"] += 1
            continue
        mom = _momentum_pct(closes, mom_days)
        if mom is None:
            skips["no_momentum"] += 1
            continue
        # Płynność: średni dzienny obrót $ (close × wolumen). Liczona dla KAŻDEJ pary
        # z danymi (żeby dało się dobrać próg z rozkładu), potem używana jako filtr.
        dv = sum(c * v for c, v in zip(closes, vols)) / len(closes) if vols else 0.0
        liq[sym] = dv
        # Trzymane zwolnione z filtra (musimy móc je domknąć), reszta pod progiem odpada.
        if min_dollar_vol > 0 and sym not in held and dv < min_dollar_vol:
            skips["illiquid"] += 1
            continue
        score = mom - (btc_mom if rs_vs_btc else 0.0)  # #2: siła WZGLĘDEM BTC
        scored.append((score, sym))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[: max(1, settings.crypto_scanner_top_k)]]
    if cache_min > 0:
        _RANK_CACHE[sig] = (now + cache_min * 60.0, top)

    # Zawsze: TOP-K + trzymane (zarządzanie/wyjścia) + BTC jako kotwica. Dedup, kolejność stabilna.
    anchor = ["BTC/USD"] if "BTC/USD" in pool else []
    result = list(dict.fromkeys(top + sorted(held) + anchor))
    # Sygnał „efektywnie statyczne": ranking nic nowego nie dołożył ponad trzymane+BTC.
    if not top and not fell_back:
        reason = "ranking pusty (brak par z danymi/płynnością) — tylko trzymane+BTC"
        fell_back = True
    else:
        reason = "ok"
    return _report(result, pool_size=pool_size, scanned=len(pool), scored=len(scored),
                   top=top, fell_back=fell_back, reason=reason, skips=skips,
                   liquidity=_liquidity_summary(liq))
