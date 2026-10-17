"""Portefeuille des 4 stratégies validées par la campagne (2011-2026), 100 € par trade, cumul simple."""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H)
sys.path.insert(0, C); import lib  # noqa
w = pd.read_csv(f"{C}/hors_echantillon/trades_NASDAQ100.csv.gz", parse_dates=["day"])
w = w[w.strategie == "Williams"].copy(); w["cost_r"] = w.entry * 1.25e-4 / w.risque
n = pd.read_csv(f"{C}/nfp_2011/trades_XAUUSD.csv.gz", parse_dates=["day"])
n = n[n.reglage == "avant (08:00-08:30) · TP 1:2"]
parts = {"Williams Nasdaq": w, "NFP or": n,
         "RSI2 Nasdaq+S&P": pd.read_csv(f"{H}/trades_RSI2.csv.gz", parse_dates=["day"]),
         "3 baisses Nasdaq+S&P": pd.read_csv(f"{H}/trades_3_baisses.csv.gz", parse_dates=["day"])}
allt = []
for k, t in parts.items():
    t = t[t.day >= "2011-01-01"]; x = (t.gross_r - t.cost_r) * 100
    yrs = (t.day.max() - pd.Timestamp("2011-01-01")).days / 365.25
    cum = x.cumsum(); dd = (cum.cummax().clip(lower=0) - cum).max()
    print(f"{k:22} {len(t):5} trades  {x.sum():8.0f} €  {x.sum()/yrs:6.0f} €/an  DD {dd:6.0f} €  ratio {x.sum()/yrs/dd:.2f}")
    allt.append(pd.DataFrame({"day": t.day.values, "pnl": x.values}))
p = pd.concat(allt).groupby("day").pnl.sum().sort_index()
cum = p.cumsum(); dd = (cum.cummax().clip(lower=0) - cum).max()
m = p.resample("ME").sum(); y = p.resample("YE").sum()
print(f"PORTEFEUILLE : {p.sum():.0f} € sur 2011-2026, {p.sum()/15.77:.0f} €/an, DD {dd:.0f} €, mois positifs {(m>0).mean()*100:.0f} %, "
      f"pire mois {m.min():.0f} €, années positives {(y>0).sum()}/{len(y)}")
print("par année :", {k.year: round(v) for k, v in y.items()})
