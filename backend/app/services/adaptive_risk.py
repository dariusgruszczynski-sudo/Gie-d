"""Adaptacyjne ryzyko: oba "mózgi" same podkręcają lub luzują agresję zależnie
od reżimu rynku LICZONEGO PER SILNIK (compute_market_regime).

Zamiast sztywnej bramki „risk-off = nie handluj", parametry przesuwają się
płynnie z wynikiem reżimu:
  - rynek sprzyjający agresji (risk-on, dodatni score)  -> WIĘKSZE ryzyko/pozycja,
    NIŻSZY próg pewności, WIĘCEJ wejść (bardzo agresywnie),
  - rynek defensywny (risk-off, ujemny score)           -> MNIEJSZE ryzyko/pozycja,
    WYŻSZY próg pewności, MNIEJ wejść (konserwatywnie),
  - neutralny                                           -> profil bazowy (×1.0).

Skalujemy tylko knoby WEJŚCIA/wielkości (ryzyko na transakcję, liczba i limit
pozycji, próg pewności kupna). Geometrii WYJŚCIA (stopy, trailing, take-profit)
NIE ruszamy -- ochrona kapitału ma być stała niezależnie od nastroju rynku.
"""

from app.config import Settings


def aggression_factor(regime: dict) -> float:
    """Mnożnik agresji z wyniku reżimu. Każdy +1 score dokłada agresji, każdy -1
    ujmuje; przycięte do rozsądnego pasma, żeby ekstremalny odczyt nie wystrzelił
    ryzyka ani nie zdusił silnika do zera."""
    score = regime.get("score", 0) or 0
    return max(0.35, min(1.5, 1.0 + 0.18 * score))


def aggression_label(factor: float) -> str:
    if factor >= 1.25:
        return "bardzo agresywna"
    if factor >= 1.08:
        return "agresywna"
    if factor >= 0.9:
        return "zrównoważona"
    if factor >= 0.6:
        return "ostrożna"
    return "obronna"


def adaptive_settings(settings: Settings, regime: dict) -> tuple[Settings, float]:
    """Zwraca (Settings dostrojone do reżimu, mnożnik agresji). Woła się PO
    obliczeniu reżimu danego silnika, a przed sizingiem/bramką wejścia."""
    f = aggression_factor(regime)

    # Wyższa agresja -> niższy próg pewności (więcej wejść); niższa agresja ->
    # wyższy próg (tylko mocne setupy). ±0.30 na skrajach mnożnika.
    conf = settings.min_buy_confidence - (f - 1.0) * 0.30
    conf = max(0.40, min(0.90, conf))

    update = {
        # Wielkość ryzyka na transakcję rośnie/maleje wprost z agresją.
        "risk_per_trade_pct": round(settings.risk_per_trade_pct * f, 4),
        # Liczba nowych wejść dziennie i limit równoległych pozycji skalują się
        # z agresją (min. 1 równoległa, żeby silnik nie zamarł całkowicie).
        "max_new_positions_per_day": max(0, round(settings.max_new_positions_per_day * f)),
        "max_concurrent_positions": max(1, round(settings.max_concurrent_positions * f)),
        "min_buy_confidence": round(conf, 3),
    }
    return settings.model_copy(update=update), f
