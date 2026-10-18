"""Règle de journée d'Anto appliquée aux flèches JustUncleL (18/10/2026) : trades pris dans l'ordre de la journée ;
on s'arrête dès que le résultat du jour est positif, ou après 2 pertes. Sur les trades de run.py (frais déduits)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import lib  # noqa
t = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trades.csv.gz"), parse_dates=["day"])
t = t[t.day >= "2011-01-01"].sort_values(["instrument", "tf", "sortie", "day", "hm"])
t["net"] = t.gross_r - t.cost_r
keep = []
for _, g in t.groupby(["instrument", "tf", "sortie", "day"], sort=False):
    pnl, losses = 0.0, 0
    for idx, x in zip(g.index, g.net.values):
        keep.append(idx); pnl += x; losses += x < 0
        if pnl > 0 or losses >= 2:
            break
k = t.loc[keep]
for (tf, ex), g in k.groupby(["tf", "sortie"]):
    p = (g.net * 100).groupby([g.instrument, g.day]).sum()
    r = lib.evaluate(g, f"{tf} {ex} règle jour, 4 marchés")
    print(lib.line(r), f"| jours positifs {(p > 0).mean()*100:.0f} %  trades/jour/marché {len(g)/len(p):.2f}")
