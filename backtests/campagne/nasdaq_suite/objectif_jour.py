"""Nasdaq seul, 1-2 trades/jour : Williams régulier (V04) + RSI2 < 20 + 3 baisses. Risque par trade nécessaire pour
100 et 300 €/jour en moyenne, drawdown et capital conseillé (drawdown ≤ 20 % du capital). Coût ∝ prix + swap."""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); sys.path.insert(0, C)
import lib  # noqa
src = open(os.path.join(C, "verification", "verif_swing.py")).read()
ns = {"__file__": os.path.join(C, "verification", "verif_swing.py")}; exec(src[:src.index("out = {}")], ns)
b = ns["bars"]("NASDAQ100")
code = open(os.path.join(H, "run.py")).read()
exec(code[code.index("def rsi("):code.index("c = b.C; sma200")], globals())
c = b.C; sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
r = swing(((rsi(c, 2) < 20) & (c > sma200)).values, (c > sma5).values, None, 1)
d3 = (c < c.shift()) & (c.shift() < c.shift(2)) & (c.shift(2) < c.shift(3))
t3 = swing(d3.values, (c > c.shift()).values, 5, 1)
for x in (r, t3):
    x["cost_r"] = x.entry * 1.25e-4 / x.risque + x.swap_r
v = pd.read_csv(os.path.join(C, "jour", "plan_valides", "verif_v04_trades.csv.gz"), parse_dates=["day"])
v["cost_r"] = v.entry * 1.25e-4 / v.risque
for lab, parts in (("Williams régulier seul", [v]), ("Williams régulier + RSI2<20 + 3 baisses", [v, r, t3])):
    t = pd.concat([x[["day", "gross_r", "cost_r"]] for x in parts]); t = t[t.day >= lib.START]
    p = (t.gross_r - t.cost_r).groupby(t.day).sum()
    full = p.reindex(pd.bdate_range(lib.START, lib.DATA_END), fill_value=0)
    cum = full.cumsum(); dd = (cum.cummax().clip(lower=0) - cum).max()
    print(f"{lab}: {len(t)/len(full):.2f} trades/jour ouvré | {full.mean():.3f} R/jour | DD {dd:.1f} R | pire jour {full.min():.1f} R | "
          f"jours tradés + {(p > 0).mean()*100:.0f} % | mois + {(full.resample('ME').sum() > 0).mean()*100:.0f} % | années + {(full.resample('YE').sum() > 0).sum()}/16")
    for target in (100, 300):
        R = target / full.mean()
        print(f"   {target} €/jour → risque {R:,.0f} €/trade | drawdown {dd*R:,.0f} € | pire jour {full.min()*R:,.0f} € | capital conseillé {dd*R/0.2:,.0f} €")
