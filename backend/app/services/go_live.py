"""Quest GO-LIVE (#1/#43 backlog): 6 twardych kryteriów z docs/krypto-dziennik.md
przeliczonych na stan „met / pending / unmet" + licznik. Zasila grywalizowaną
kartę („odblokuj realny kapitał, gdy 6/6 zielone"). Czysto obliczeniowe — wejścia
podaje warstwa API ze scorecardu/metryk/budżetu."""


def go_live_criteria(*, closed_trades: int, weeks: float, beats_btc, expectancy_r,
                     max_dd_pct, ai_spend_usd, ai_budget_usd: float = 9.0,
                     min_trades: int = 50, min_weeks: float = 3.0, max_dd_limit: float = 25.0) -> dict:
    """Zwraca {criteria:[{key,label,met,pending,value}], met, total, go_live}.
    `pending` = za mało danych na werdykt (nie liczy się jako spełnione). go_live
    = wszystkie met. Próbka < min_trades blokuje werdykty zależne od wyniku."""
    sample_ok = closed_trades >= min_trades

    def crit(key, label, met, value, pending=False):
        return {"key": key, "label": label, "met": bool(met) and not pending, "pending": pending, "value": value}

    rows = [
        crit("trades", "≥50 zamkniętych trejdów", closed_trades >= min_trades, f"{closed_trades}/{min_trades}"),
        crit("weeks", "≥3 tygodnie handlu", weeks >= min_weeks, f"{weeks:.0f} tyg."),
        crit("beats_btc", "Bije trzymanie BTC", beats_btc is True and sample_ok,
             ("za mało danych" if (beats_btc is None or not sample_ok) else ("tak" if beats_btc else "nie")),
             pending=(beats_btc is None or not sample_ok)),
        crit("edge", "Dodatni edge (expectancy > 0)",
             (expectancy_r is not None and expectancy_r > 0 and sample_ok),
             (f"{expectancy_r}R" if expectancy_r is not None else "—"),
             pending=(expectancy_r is None or not sample_ok)),
        crit("drawdown", "Drawdown ≤ 25%",
             (max_dd_pct is not None and max_dd_pct <= max_dd_limit),
             (f"{max_dd_pct}%" if max_dd_pct is not None else "—"),
             pending=(max_dd_pct is None)),
        crit("ai_cost", "Koszt AI ≈ $0",
             (ai_spend_usd is not None and ai_spend_usd <= ai_budget_usd),
             (f"${ai_spend_usd:.0f}/mies" if ai_spend_usd is not None else "—")),
    ]
    met = sum(1 for r in rows if r["met"])
    return {"criteria": rows, "met": met, "total": len(rows), "go_live": met == len(rows)}
