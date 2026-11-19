"""Audyt konfiguracji wejść (#85 backlog). Czysto odczytowe: liczy, ile bramek
NOWYCH WEJŚĆ jest włączonych naraz i sygnalizuje RYZYKO PARALIŻU — gdy zbyt wiele
filtrów kierunku/trendu działa przez AND, prawdopodobieństwo przejścia spada do ~0
i silnik przestaje handlować (dokładnie stan z listopada 2026: tydzień+ w gotówce).

Nie zmienia niczego — tylko nazywa problem, który dotąd był niewidoczny, aż
właściciel zauważył, że apka nie handluje."""

# Bramki, które CELUJĄ w kierunek/trend wejścia (nakładają się — trzy mierzą to
# samo: trend BTC). Gdy >= PARALYSIS_TREND_GATES z nich jest ON, ostrzegamy.
PARALYSIS_TREND_GATES = 3


def entry_gate_audit(settings) -> dict:
    """Zwraca aktywne bramki wejścia + flagę paralysis_risk. `settings` to
    EFEKTYWNE ustawienia venue (dla krypto: po effective_settings)."""
    def on(name: str, default=False):
        return getattr(settings, name, default)

    gates: list[dict] = []
    # Filtry kierunku/trendu — najczęstsza przyczyna paraliżu (nakładają się).
    trend_gates = 0
    if on("regime_filter_enabled"):
        gates.append({"gate": "regime_filter", "kind": "trend", "detail": f"BTC > SMA{on('regime_filter_ma_period', 100)} ({on('regime_filter_timeframe', '1d')})"})
        trend_gates += 1
    if on("crypto_btc_core_mode"):
        gates.append({"gate": "btc_core", "kind": "trend", "detail": "alty blokowane gdy BTC pod trendem"})
        trend_gates += 1
    if on("mtf_confirm_enabled"):
        gates.append({"gate": "mtf_confirm", "kind": "trend", "detail": f"potwierdzenie {on('mtf_timeframe', '4h')} > SMA{on('mtf_ma_period', 50)}"})
        trend_gates += 1
    # Filtry jakości setupu.
    if on("entry_filter_enabled"):
        gates.append({"gate": "confluence", "kind": "quality", "detail": f"score >= {on('entry_min_score', 2)}"})
    if (on("min_adx", 0.0) or 0.0) > 0:
        gates.append({"gate": "min_adx", "kind": "quality", "detail": f"ADX >= {on('min_adx')}"})
    if on("breakout_entry_enabled"):
        gates.append({"gate": "breakout", "kind": "quality", "detail": f"wybicie {on('breakout_lookback', 20)}"})
    if on("altseason_gate_enabled"):
        gates.append({"gate": "altseason", "kind": "trend", "detail": "alty tylko gdy prowadzą BTC"})
    # Bramki makro/ryzyka (wstrzymują wejścia w złych warunkach).
    if (on("max_total_exposure_pct", 0.0) or 0.0) > 0:
        gates.append({"gate": "exposure_cap", "kind": "risk", "detail": f"ekspozycja <= {on('max_total_exposure_pct')}%"})
    if (on("loss_streak_pause", 0) or 0) > 0:
        gates.append({"gate": "loss_streak", "kind": "risk", "detail": f"pauza po {on('loss_streak_pause')} stratach"})
    if (on("fng_pause_above", 0.0) or 0.0) > 0:
        gates.append({"gate": "fng_pause", "kind": "risk", "detail": f"pauza gdy Fear&Greed >= {on('fng_pause_above')}"})
    if (on("funding_pause_above_pct", 0.0) or 0.0) > 0:
        gates.append({"gate": "funding_pause", "kind": "risk", "detail": f"pauza gdy funding >= {on('funding_pause_above_pct')}%"})

    paralysis_risk = trend_gates >= PARALYSIS_TREND_GATES
    if paralysis_risk:
        note = (f"PARALIŻ: {trend_gates} nakładających się filtrów trendu BTC naraz "
                "(mierzą to samo) — longi wchodzą tylko w wyraźnej hossie BTC, inaczej gotówka. "
                "Rozważ zostawienie JEDNEGO filtra trendu.")
    elif len(gates) >= 7:
        note = f"{len(gates)} bramek wejścia naraz — wysokie ryzyko, że setupy rzadko przechodzą wszystkie przez AND."
        paralysis_risk = True
    else:
        note = f"{len(gates)} bramek wejścia aktywnych."
    return {
        "active_gates": gates,
        "count": len(gates),
        "trend_gates": trend_gates,
        "paralysis_risk": paralysis_risk,
        "note": note,
    }
