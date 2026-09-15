"""Monte Carlo: rzut realnego, ZMIERZONEGO edge GielDarka na ~rok w przód.

To NIE jest prognoza rynku (nikt jej nie ma) — to projekcja rozkładu wyników przy
założeniu, że strategia zachowa swój dotychczasowy, realny edge:
  win_rate 27.8% (15W/39L), śr. wygrana +$2.74, śr. strata -$1.24 (payoff 2.21x),
  edge/transakcję -$0.13, ~520 zamknięć/rok, konto startowe ~$993.

Modelujemy KAŻDĄ transakcję jako zwrot na UŁAMKU konta wystawionym na ryzyko
(position_fraction). Zwrot per transakcja (na wystawionym kapitale) wyliczamy z
realnych $ i typowej wielkości pozycji, więc scenariusze różnią się tylko tym, ILE
konta bot wystawia (obecne małe pozycje vs auto-deploy ~25%/nazwę).
"""

import numpy as np

P_WIN = 15 / 54            # 0.278 — realny win rate
AVG_WIN_USD = 2.74
AVG_LOSS_USD = 1.24        # wartość bezwzględna
START = 993.0
TRADES_PER_YEAR = 520
N_PATHS = 20000
RNG = np.random.default_rng(42)

# Typowa wielkość pozycji DOTYCHCZAS (leżąca gotówka -> małe pozycje). Z danych:
# equity ~$110-170 na ~2 nazwy => ~$75/pozycję. To zamienia $ na % wystawionego kapitału.
AVG_POSITION_USD_NOW = 75.0
WIN_RET = AVG_WIN_USD / AVG_POSITION_USD_NOW      # +3.65% na wystawionym kapitale
LOSS_RET = -AVG_LOSS_USD / AVG_POSITION_USD_NOW   # -1.65%

BREAKEVEN_WR = 1 / (1 + AVG_WIN_USD / AVG_LOSS_USD)


def simulate(position_fraction: float, trades: int, monthly_deposit: float = 0.0,
             win_ret: float = WIN_RET, loss_ret: float = LOSS_RET, p_win: float = P_WIN):
    """Zwraca (końcowe_salda, ścieżki_min_dla_drawdown, macierz_ścieżek[N, kroki])."""
    wins = RNG.random((N_PATHS, trades)) < p_win
    rets = np.where(wins, win_ret, loss_ret) * position_fraction
    factors = 1.0 + rets
    # deposits: dorzucane równomiernie w ciągu roku (12 rat)
    deposit_at = set(int(trades * m / 12) for m in range(1, 13)) if monthly_deposit else set()
    bal = np.full(N_PATHS, START)
    peak = bal.copy()
    max_dd = np.zeros(N_PATHS)
    # próbkujemy krzywą co ~1/52 roku do wykresu (52 punkty)
    sample_every = max(1, trades // 52)
    curve = [bal.copy()]
    for t in range(trades):
        bal = bal * factors[:, t]
        bal = np.maximum(bal, 0.0)
        if t in deposit_at:
            bal = bal + monthly_deposit
        peak = np.maximum(peak, bal)
        dd = (peak - bal) / np.where(peak > 0, peak, 1)
        max_dd = np.maximum(max_dd, dd)
        if (t + 1) % sample_every == 0:
            curve.append(bal.copy())
    return bal, max_dd, np.array(curve)


def report(name, bal, max_dd, deposited=0.0):
    pcts = np.percentile(bal, [5, 25, 50, 75, 95])
    invested = START + deposited
    prob_profit = float(np.mean(bal > invested)) * 100
    print(f"\n=== {name} ===")
    print(f"  wpłacony kapitał (start+dopłaty): ${invested:,.0f}")
    print(f"  mediana konta po roku:   ${pcts[2]:,.0f}  ({(pcts[2]/invested-1)*100:+.1f}%)")
    print(f"  zakres 25-75%:           ${pcts[1]:,.0f} … ${pcts[3]:,.0f}")
    print(f"  zakres 5-95%:            ${pcts[0]:,.0f} … ${pcts[4]:,.0f}")
    print(f"  P(na plusie po roku):    {prob_profit:.0f}%")
    print(f"  mediana maks. obsunięcia:{np.percentile(max_dd,50)*100:.0f}%   (95. pct {np.percentile(max_dd,95)*100:.0f}%)")


print(f"Break-even win rate przy payoff 2.21x: {BREAKEVEN_WR*100:.1f}%  (obecnie {P_WIN*100:.1f}% -> PONIŻEJ)")
print(f"Zwrot/transakcję na wystawionym kapitale: {(P_WIN*WIN_RET+(1-P_WIN)*LOSS_RET)*100:.3f}%")

# Scenariusz 1: obecne (małe) pozycje ~7.5% konta na transakcję.
b1, dd1, c1 = simulate(position_fraction=AVG_POSITION_USD_NOW / START, trades=TRADES_PER_YEAR)
report("1) Status quo (małe pozycje ~7.5% konta)", b1, dd1)

# Scenariusz 2: auto-deploy ~25%/nazwę (3.3x większe pozycje), więcej obrotu (+30%).
b2, dd2, c2 = simulate(position_fraction=0.25, trades=int(TRADES_PER_YEAR * 1.3))
report("2) Auto-deploy 25%/nazwę, wyższy obrót", b2, dd2)

# Scenariusz 3: jak 2 + dopłaty $300/mies.
b3, dd3, c3 = simulate(position_fraction=0.25, trades=int(TRADES_PER_YEAR * 1.3), monthly_deposit=300.0)
report("3) Auto-deploy + dopłaty $300/mies", b3, dd3, deposited=3600.0)

# Scenariusz 4: „co jeśli edge się poprawi" — win rate 35% (powyżej break-even).
b4, dd4, c4 = simulate(position_fraction=0.25, trades=int(TRADES_PER_YEAR * 1.3), p_win=0.35)
report("4) HIPOTETYCZNIE win rate 35% (powyżej break-even), auto-deploy", b4, dd4)

# Zapisz percentyle krzywych do JSON dla wykresu.
import json
weeks = list(range(c2.shape[0]))
out = {
    "weeks": weeks,
    "breakeven_wr": BREAKEVEN_WR,
    "p_win": P_WIN,
    "scenarios": {},
}
for key, c, name in [("status_quo", c1, "Status quo"), ("auto_deploy", c2, "Auto-deploy 25%"),
                     ("auto_deploy_deposits", c3, "Auto-deploy + dopłaty"), ("better_edge", c4, "Win rate 35%")]:
    out["scenarios"][key] = {
        "name": name,
        "p5": np.percentile(c, 5, axis=1).round(1).tolist(),
        "p25": np.percentile(c, 25, axis=1).round(1).tolist(),
        "p50": np.percentile(c, 50, axis=1).round(1).tolist(),
        "p75": np.percentile(c, 75, axis=1).round(1).tolist(),
        "p95": np.percentile(c, 95, axis=1).round(1).tolist(),
    }
with open("/tmp/claude-0/-home-user-Gie-d/fe1df807-8e8a-512a-a12c-6c9b924b2af0/scratchpad/sim.json", "w") as f:
    json.dump(out, f)
print("\nZapisano percentyle krzywych do scratchpad/sim.json")
