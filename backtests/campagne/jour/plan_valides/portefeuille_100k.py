"""Portefeuille des stratégies validées, risque par trade réglé pour une moyenne de 100 €/jour ouvré (18/10/2026).
A = Williams Nasdaq (sortie 16:00) + RSI2 Nasdaq/S&P + NFP or + 3 baisses Nasdaq/S&P.
B = idem avec le Williams « régulier » (50 % à +0,5 R, stop à l'entrée ; règle d'Anto).
Coûts : Williams proportionnel 1,25 pb ; autres = coûts du dépôt. Gains rapportés au jour d'entrée."""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(os.path.dirname(H)); sys.path.insert(0, C)
import lib  # noqa
w = pd.read_csv(f"{H}/williams_2e_chance_trades.csv.gz", parse_dates=["day"]); w = w[w.n == 1].assign(cost_r=lambda x: x.entry * 1.25e-4 / x.risque)
v = pd.read_csv(f"{H}/verif_v04_trades.csv.gz", parse_dates=["day"]).assign(cost_r=lambda x: x.entry * 1.25e-4 / x.risque)
n = pd.read_csv(f"{C}/nfp_2011/trades_XAUUSD.csv.gz", parse_dates=["day"]); n = n[n.reglage == "avant (08:00-08:30) · TP 1:2"]
r = pd.read_csv(f"{C}/verification/trades_RSI2.csv.gz", parse_dates=["day"]); b = pd.read_csv(f"{C}/verification/trades_3_baisses.csv.gz", parse_dates=["day"])
for nom, wl in (("A (Williams clôture)", w), ("B (Williams régulier)", v)):
    t = pd.concat([x[["day", "gross_r", "cost_r"]] for x in (wl, n, r, b)])
    t = t[t.day >= lib.START]
    p1 = ((t.gross_r - t.cost_r)).groupby(t.day).sum()            # en R par jour
    days = pd.bdate_range(lib.START, lib.DATA_END); full = p1.reindex(days, fill_value=0)
    risk = 100 / full.mean()                                         # € par R pour 100 €/jour en moyenne
    pe = full * risk; cum = pe.cumsum(); dd = (cum.cummax().clip(lower=0) - cum).max()
    m = pe.resample("ME").sum(); y = pe.resample("YE").sum()
    print(f"{nom}: risque {risk:.0f} €/trade | {pe.mean():.0f} €/jour ouvré | jours tradés positifs {(p1 > 0).mean()*100:.0f} % | "
          f"pire jour {pe.min():,.0f} € | drawdown max {dd:,.0f} € | mois positifs {(m > 0).mean()*100:.0f} % | pire mois {m.min():,.0f} € | "
          f"années positives {(y > 0).sum()}/{len(y)} | pire année {y.min():,.0f} €")
