"""Nasdaq : réduire le drawdown (22/10/2026). Règles fixées AVANT calcul. Coût ∝ prix 1,25 pb (+ swap pour les swings).
Critère de classement demandé par Anto : gain annuel / drawdown max (en plus de lib.evaluate).
Base : Williams régulier V04 (50 % à +0,5 R, stop à l'entrée ; 2e trade si perte).
 W-A achats seulement ; W-B achats seulement si clôture de la veille > SMA200 ; W-C sens de la SMA200 (achats au-dessus,
 ventes en dessous) ; W-D un seul trade par jour (pas de 2e trade).
Comparés avec : Williams régulier de base, RSI2 < 20, RSI2 < 10, 3 baisses, et les combinaisons RSI2<20 + 3 baisses.
"""
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
trend = (c > sma200).shift(1)                      # connu avant l'ouverture du jour
v = pd.read_csv(os.path.join(C, "jour", "plan_valides", "verif_v04_trades.csv.gz"), parse_dates=["day"])
v["cost_r"] = v.entry * 1.25e-4 / v.risque
up = v.day.map(trend).astype("boolean").fillna(False).astype(bool)
W = {"Williams régulier (base)": v, "W-A achats seulement": v[v.d == 1],
     "W-B achats si > SMA200": v[(v.d == 1) & up], "W-C sens de la SMA200": v[((v.d == 1) & up) | ((v.d == -1) & ~up)],
     "W-D 1 seul trade/jour": v[v.n == 1]}
sw = {}
for lab, cond in (("RSI2 < 20", rsi(c, 2) < 20), ("RSI2 < 10", b.rsi < 10)):
    t = swing((cond & (c > sma200)).values, (c > sma5).values, None, 1); t["cost_r"] = t.entry * 1.25e-4 / t.risque + t.swap_r; sw[lab] = t
d3 = (c < c.shift()) & (c.shift() < c.shift(2)) & (c.shift(2) < c.shift(3))
t = swing(d3.values, (c > c.shift()).values, 5, 1); t["cost_r"] = t.entry * 1.25e-4 / t.risque + t.swap_r; sw["3 baisses"] = t
combos = {**W, **sw, "RSI2<20 + 3 baisses": pd.concat([sw["RSI2 < 20"], sw["3 baisses"]]),
          "W-B + RSI2<20 + 3 baisses": pd.concat([W["W-B achats si > SMA200"], sw["RSI2 < 20"], sw["3 baisses"]])}
rows = []
for lab, t in combos.items():
    t = t[t.day >= lib.START]
    r = lib.evaluate(t, lab)
    p = (t.gross_r - t.cost_r).groupby(t.day).sum()
    full = p.reindex(pd.bdate_range(lib.START, lib.DATA_END), fill_value=0); cum = full.cumsum()
    dd = (cum.cummax().clip(lower=0) - cum).max(); an = full.sum() / (len(full) / 261)
    rows.append((lab, len(t), r["net"]["e_r"], r["t_stat"], r["valide"], an * 100, dd * 100, an / dd,
                 len(t) / len(full), (full.resample("ME").sum() > 0).mean() * 100))
out = pd.DataFrame(rows, columns=["stratégie", "trades", "E", "t", "valide", "€/an (100 €/R)", "DD €", "gain an / DD",
                                  "trades/jour", "mois +%"]).sort_values("gain an / DD", ascending=False)
print(out.round(3).to_string(index=False))
out.to_csv(os.path.join(H, "drawdown.csv"), index=False)
