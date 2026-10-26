"""Walidacja walk-forward / out-of-sample (wniosek #15, Partia 5).

Problem, który to rozwiązuje: pojedynczy zbiorczy backtest łatwo zakłamać —
dodatni wynik może pochodzić z JEDNEGO szczęśliwego okna (np. jednej hossy), a
nie z powtarzalnej przewagi. To dokładnie czerwona flaga z kryteriów GO-LIVE
(„nie z 1–2 strzałów") i sedno pytania „czy bijemy BTC KONSEKWENTNIE, czy raz".

Co robi: tnie historię na K kolejnych, ROZŁĄCZNYCH okien OUT-OF-SAMPLE i puszcza
przez każde TEN SAM mechaniczny silnik (backtest.run_backtest) z tymi samymi,
NIESTROJONYMI pod okno nastawami. Dla każdego okna każdy symbol dostaje swój
rozbieg (warmup) PRZED oknem, więc SMA200 itd. są policzone uczciwie. Potem
agreguje: w ilu oknach pobiliśmy benchmark (BTC), mediana/min alfy, najgorsze
obsunięcie — i zwraca UCZCIWY werdykt spójności przewagi w czasie.

To narzędzie POMIARU, nie handlu: nie zmienia żadnego knoba na żywo. Czyste i
samowystarczalne — te same dane co run_backtest ({symbol: [[t,o,h,l,c,v],...]}).
"""

from bisect import bisect_left, bisect_right
from datetime import UTC, datetime
from statistics import median

from app.config import Settings
from app.services.backtest import WARMUP, _epoch, run_backtest


def _iso_date(epoch_s: float) -> str:
    try:
        return datetime.fromtimestamp(epoch_s, UTC).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return "?"


def walk_forward(
    bars_by_symbol: dict[str, list[list]],
    settings: Settings,
    *,
    benchmark_symbol: str | None = None,
    folds: int = 4,
    starting_cash: float = 1000.0,
    warmup: int = WARMUP,
) -> dict:
    """Puszcza run_backtest na K rozłącznych oknach OOS i agreguje spójność przewagi.

    Zwraca dict: {folds: [...per-okno raporty...], summary: {...}} albo {"error": ...}
    gdy historii jest za mało na sensowny podział."""
    if folds < 2:
        return {"error": "walk-forward wymaga >= 2 okien", "folds_requested": folds}

    symbols = [s for s, b in bars_by_symbol.items() if len(b) > warmup]
    if not symbols:
        return {"error": "insufficient history", "bars": 0}

    times = {s: [_epoch(r[0]) for r in bars_by_symbol[s]] for s in symbols}
    timeline = sorted({e for s in symbols for e in times[s]})
    # Region OOS = oś czasu PO globalnym rozbiegu; dzielimy go na równe segmenty.
    if len(timeline) <= warmup + folds * 2:
        return {"error": "insufficient history for folds", "steps": len(timeline), "folds": folds}
    oos = timeline[warmup:]
    seg = len(oos) // folds

    fold_reports: list[dict] = []
    for k in range(folds):
        lo = oos[k * seg]
        hi = oos[-1] if k == folds - 1 else oos[(k + 1) * seg - 1]
        fold_bars: dict[str, list[list]] = {}
        for s in symbols:
            ts = times[s]
            j = bisect_left(ts, lo)              # pierwszy bar okna
            jhi = bisect_right(ts, hi)           # tuż za ostatnim barem okna
            start = max(0, j - warmup)           # rozbieg PRZED oknem
            sl = bars_by_symbol[s][start:jhi]
            if len(sl) > warmup:
                fold_bars[s] = sl
        if not fold_bars:
            continue
        rep = run_backtest(
            fold_bars, settings, benchmark_symbol=benchmark_symbol,
            starting_cash=starting_cash, warmup=warmup,
        )
        if "error" in rep:
            continue
        fold_reports.append({
            "fold": k + 1,
            "from": _iso_date(lo),
            "to": _iso_date(hi),
            "entries": rep.get("entries"),
            "closed_trades": rep.get("closed_trades"),
            "win_rate_pct": rep.get("win_rate_pct"),
            "total_return_pct": rep.get("total_return_pct"),
            "benchmark_return_pct": rep.get("benchmark_return_pct"),
            "alpha_pct": rep.get("alpha_pct"),
            "max_drawdown_pct": rep.get("max_drawdown_pct"),
            "calmar": rep.get("calmar"),
        })

    if not fold_reports:
        return {"error": "no fold produced a usable report", "folds": folds}

    alphas = [r["alpha_pct"] for r in fold_reports if r["alpha_pct"] is not None]
    rets = [r["total_return_pct"] for r in fold_reports if r["total_return_pct"] is not None]
    dds = [r["max_drawdown_pct"] for r in fold_reports if r["max_drawdown_pct"] is not None]
    n_alpha = len(alphas)
    beat = sum(1 for a in alphas if a > 0)
    positive_ret = sum(1 for r in rets if r > 0)

    # Werdykt spójności (HEURYSTYKA, nie wyrocznia): przewaga „trzyma się w czasie",
    # gdy pobiliśmy benchmark w WIĘKSZOŚCI okien (>= 60%) ORAZ mediana alfy > 0.
    edge_consistent = bool(n_alpha) and beat >= (n_alpha * 0.6) and median(alphas) > 0

    summary = {
        "folds_run": len(fold_reports),
        "folds_beating_benchmark": f"{beat}/{n_alpha}" if n_alpha else None,
        "folds_positive_return": f"{positive_ret}/{len(rets)}" if rets else None,
        "median_alpha_pct": round(median(alphas), 2) if alphas else None,
        "min_alpha_pct": round(min(alphas), 2) if alphas else None,
        "max_alpha_pct": round(max(alphas), 2) if alphas else None,
        "worst_fold_drawdown_pct": round(max(dds), 2) if dds else None,
        "edge_consistent": edge_consistent,
    }
    return {"folds": fold_reports, "summary": summary}


def gate_verdict(result: dict, *, min_folds_beating_pct: float = 50.0,
                 min_median_alpha_pct: float = 0.0) -> dict:
    """#28 BRAMKA (anty-zygzak): zamienia raport walk-forward w twardy werdykt
    PASS/FAIL dla zmiany strategii/configu. FAIL, gdy przewaga NIE jest spójna —
    pobiliśmy benchmark w < min_folds_beating_pct okien LUB mediana alfy <
    min_median_alpha_pct. Użycie: uruchom PRZED wdrożeniem zmiany; nie promuj
    zmiany, która nie przechodzi OOS. Zwraca {passed, reasons, metrics}."""
    if "error" in result or "summary" not in result:
        return {"passed": False, "reasons": [f"brak wyniku walk-forward: {result.get('error', 'nieznany')}"], "metrics": {}}
    s = result["summary"]
    beat = s.get("folds_beating_benchmark") or "0/0"
    try:
        num, den = (int(x) for x in str(beat).split("/"))
        beat_pct = (num / den * 100) if den else 0.0
    except (ValueError, ZeroDivisionError):
        beat_pct = 0.0
    median_alpha = s.get("median_alpha_pct")
    reasons = []
    if beat_pct < min_folds_beating_pct:
        reasons.append(f"pobiło benchmark tylko w {beat} okien ({beat_pct:.0f}% < {min_folds_beating_pct:.0f}%)")
    if median_alpha is None or median_alpha < min_median_alpha_pct:
        reasons.append(f"mediana alfy {median_alpha}% < próg {min_median_alpha_pct}%")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "metrics": {"folds_beating_pct": round(beat_pct, 1), "median_alpha_pct": median_alpha,
                    "worst_fold_drawdown_pct": s.get("worst_fold_drawdown_pct")},
    }


def format_report(result: dict) -> str:
    """Zwięzły, czytelny markdown walk-forward (do SUMMARY/CI/dziennika)."""
    if "error" in result:
        return f"Walk-forward: BŁĄD — {result['error']}"
    s = result["summary"]
    lines = [
        "## Walk-forward (out-of-sample) — czy przewaga trzyma się w czasie",
        "",
        f"- Okien przebiegło: **{s['folds_run']}**",
        f"- Pobiło BTC: **{s['folds_beating_benchmark']}** · dodatni zwrot: **{s['folds_positive_return']}**",
        f"- Alfa vs BTC: mediana **{s['median_alpha_pct']}%** (min {s['min_alpha_pct']}%, max {s['max_alpha_pct']}%)",
        f"- Najgorsze obsunięcie w oknie: **{s['worst_fold_drawdown_pct']}%**",
        f"- Przewaga spójna w czasie: **{'TAK' if s['edge_consistent'] else 'NIE'}**",
        "",
        "| # | od | do | wejścia | trafność% | zwrot% | BTC% | alfa% | maxDD% | Calmar |",
        "|---|----|----|---------|-----------|--------|------|-------|--------|--------|",
    ]
    for r in result["folds"]:
        lines.append(
            f"| {r['fold']} | {r['from']} | {r['to']} | {r['entries']} | {r['win_rate_pct']} | "
            f"{r['total_return_pct']} | {r['benchmark_return_pct']} | {r['alpha_pct']} | "
            f"{r['max_drawdown_pct']} | {r['calmar']} |"
        )
    return "\n".join(lines)
