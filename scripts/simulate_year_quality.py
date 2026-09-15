"""Monte Carlo v2 — NOWE WARUNKI: profil jakości + dopłaty $300/mies.

Zmiany vs poprzedni model:
  - Profil jakości: mniejsze i rzadsze pozycje (ryzyko/trade 2%, entry_min_score 2,
    auto-deploy OFF) => ~10% konta na transakcję, ~300 transakcji/rok.
  - Dopłaty: $300 co miesiąc (12 rat).
  - Trafność jest NIEZNANA (całe zacieśnienie ma ją podnieść) — więc liczymy
    PASMO scenariuszy trafności: 28% (bez poprawy), 31% (próg), 34%, 38%.
Oddzielamy „wpłacony kapitał" (start + dopłaty) od „wkładu bota" (co realnie
dołożył/odjął handel), żeby nie mylić dopłat z zyskiem.
"""
import json
import numpy as np

AVG_WIN_USD, AVG_LOSS_USD = 2.74, 1.24        # realny payoff 2.21x (zakładamy stały)
AVG_POSITION_USD_NOW = 75.0
WIN_RET = AVG_WIN_USD / AVG_POSITION_USD_NOW   # +3.65% na wystawionym kapitale
LOSS_RET = -AVG_LOSS_USD / AVG_POSITION_USD_NOW
START = 993.0
DEPOSIT = 300.0
DEP_TOTAL = DEPOSIT * 12
POS_FRAC = 0.10        # profil jakości: ~10% konta/trade (mniej niż auto-deploy 25%)
TRADES = 300           # mniej wejść (entry_min_score 2, mniej slotów)
N = 20000
BREAKEVEN = 1 / (1 + AVG_WIN_USD / AVG_LOSS_USD)   # 0.312
RNG = np.random.default_rng(7)
SCEN = {"p28": (0.278, "28% — bez poprawy (obecna)"), "p31": (0.312, "31% — próg opłacalności"),
        "p34": (0.34, "34% — umiarkowana poprawa"), "p38": (0.38, "38% — dobra poprawa")}


def sim(p):
    wins = RNG.random((N, TRADES)) < p
    fac = 1.0 + np.where(wins, WIN_RET, LOSS_RET) * POS_FRAC
    # 12 rat: m=1..12 mapowane na indeksy transakcji 24..299 (ostatnia rata w
    # ostatniej transakcji) — bez tego gubiła się 12. wpłata.
    dep_at = {int(round(TRADES * m / 12)) - 1 for m in range(1, 13)}
    bal = np.full(N, START); peak = bal.copy(); mdd = np.zeros(N)
    every = max(1, TRADES // 52); curve = [bal.copy()]
    for t in range(TRADES):
        bal = np.maximum(bal * fac[:, t], 0.0)
        if t in dep_at:
            bal += DEPOSIT
        peak = np.maximum(peak, bal); mdd = np.maximum(mdd, (peak - bal) / np.where(peak > 0, peak, 1))
        if (t + 1) % every == 0:
            curve.append(bal.copy())
    return bal, mdd, np.array(curve)


invested = START + DEP_TOTAL
print(f"Wpłacony kapitał (start ${START:.0f} + 12×${DEPOSIT:.0f}): ${invested:,.0f}")
print(f"Próg opłacalności: {BREAKEVEN*100:.1f}%  |  pozycja ~{POS_FRAC*100:.0f}% konta, {TRADES} transakcji/rok\n")
out = {"invested": invested, "start": START, "dep_total": DEP_TOTAL, "breakeven": BREAKEVEN,
       "weeks": None, "scenarios": {}}
for key, (p, label) in SCEN.items():
    bal, mdd, curve = sim(p)
    pct = np.percentile(bal, [5, 50, 95])
    contrib = np.percentile(bal - invested, 50)   # mediana wkładu bota (po odjęciu wpłat)
    pcontrib = float(np.mean(bal > invested)) * 100
    print(f"{label}")
    print(f"   mediana konta: ${pct[1]:,.0f}   (5–95%: ${pct[0]:,.0f}–${pct[2]:,.0f})")
    print(f"   wkład bota (mediana, po odjęciu wpłat): {'+' if contrib>=0 else ''}${contrib:,.0f}   "
          f"P(bot dołożył plus): {pcontrib:.0f}%   maks. obsun. med {np.percentile(mdd,50)*100:.0f}%\n")
    out["weeks"] = list(range(curve.shape[0]))
    out["scenarios"][key] = {"name": label, "p": p, "median_end": round(float(pct[1])),
        "p5_end": round(float(pct[0])), "p95_end": round(float(pct[2])),
        "contrib": round(float(contrib)), "pcontrib": round(pcontrib), "dd": round(float(np.percentile(mdd,50)*100)),
        "p5": np.percentile(curve, 5, axis=1).round(1).tolist(),
        "p50": np.percentile(curve, 50, axis=1).round(1).tolist(),
        "p95": np.percentile(curve, 95, axis=1).round(1).tolist()}
# krzywa „tylko wpłaty" (bez handlu) do odniesienia
depcurve = []
for w in range(len(out["weeks"])):
    frac = w / (len(out["weeks"]) - 1)
    depcurve.append(round(START + DEP_TOTAL * frac, 1))
out["deposit_only"] = depcurve

SCRATCH = "/tmp/claude-0/-home-user-Gie-d/fe1df807-8e8a-512a-a12c-6c9b924b2af0/scratchpad"
json.dump(out, open(f"{SCRATCH}/sim2.json", "w"))
print("Zapisano ->", f"{SCRATCH}/sim2.json")
