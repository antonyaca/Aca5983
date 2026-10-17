"""Robustesse du trio Nasdaq (ORB 30 min achats + Williams deux sens + pré-marché deux sens) — 17/10/2026.
1. Sensibilité du k de Williams (0,3 → 0,8) : un edge réel ne doit pas dépendre d'une seule valeur.
2. Trio : résultats par année, par semaine (objectif +500 €/semaine), Monte Carlo (tirage de semaines entières,
   10 000 années simulées de 52 semaines) pour le drawdown et le gain annuel. 100 € par R, coûts inclus.
"""
import os, sys
import numpy as np, pandas as pd
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
sys.path.insert(0, os.path.join(B, "batch3"))
from strategies import COST, IS_END
_sp = importlib.util.spec_from_file_location("b4", os.path.join(B, "batch4", "strategies.py"))
s4 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(s4)

# 1. Sensibilité k
days, n = s4.sessions("NASDAQ100")
src = open(os.path.join(B, "batch4", "strategies.py")).read()
rows = []
for k in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
    code = src.split("def williams")[1].split("def main")[0].replace("for k in (0.25, 0.5):", f"for k in ({k},):")
    ns = {}; exec("def williams" + code, s4.__dict__, ns)
    rows += ns["williams"]("NASDAQ100", days, n)
t = pd.DataFrame(rows, columns=["instrument", "strategie", "reglage", "day", "d", "entry", "exit", "risque"])
t = t[(t["day"] >= "2020-01-01") & t["reglage"].str.contains("deux sens")]
t["net_r"] = (t["exit"] - t["entry"]) * t["d"] / t["risque"] - COST["NASDAQ100"] / t["risque"]
print("== Williams Nasdaq, deux sens : sensibilité de k")
for reg, g in t.groupby("reglage"):
    i, o = g[g.day < IS_END].net_r, g[g.day >= IS_END].net_r
    pf = g.net_r[g.net_r > 0].sum() / -g.net_r[g.net_r < 0].sum()
    print(f"{reg:28s} trades {len(g):5d}  E {g.net_r.mean():+.3f} R  PF {pf:.2f}  IS {i.mean():+.3f}  OOS {o.mean():+.3f}  total {g.net_r.sum()*100:+8.0f} €")

# 2. Trio
import subprocess, io
_c = "import sys; sys.path.insert(0, '.'); from run import trades; trades('A','NASDAQ100').groupby('day').net_r.sum().to_csv(sys.stdout)"
_o = subprocess.run([sys.executable, "-c", _c], cwd=os.path.join(B, "filters2"), capture_output=True, text=True, check=True).stdout
orb = pd.read_csv(io.StringIO(_o), parse_dates=["day"], index_col="day")["net_r"]
w4 = pd.read_csv(os.path.join(B, "batch4/results/trades.csv.gz"), parse_dates=["day"])
w7 = pd.read_csv(os.path.join(B, "batch7/results/trades.csv.gz"), parse_dates=["day"])
wil = w4[(w4.instrument == "NASDAQ100") & (w4.reglage == "Williams k=0,5 · deux sens")].groupby("day").net_r.sum()
pre = w7[(w7.instrument == "NASDAQ100") & (w7.reglage == "Pré-marché · deux sens")].groupby("day").net_r.sum()
d = pd.concat([orb.rename("ORB"), wil.rename("Williams"), pre.rename("Pre")], axis=1).fillna(0)
eur = d.sum(axis=1) * 100
print("\n== Trio : par année (€)")
print(eur.groupby(eur.index.year).sum().round(0).to_string())
wk = eur.resample("W-FRI").sum(); wk = wk[wk.index >= eur.index.min()]
print(f"\n== Semaines : {len(wk)} | positives {(wk>0).mean()*100:.0f} % | ≥ +500 € {(wk>=500).mean()*100:.0f} % | moyenne {wk.mean():+.0f} € | pire {wk.min():+.0f} € | meilleure {wk.max():+.0f} €")
rng = np.random.default_rng(42); W = wk.values
sims = W[rng.integers(0, len(W), (10000, 52))]
cum = sims.cumsum(1); dd = (np.maximum.accumulate(np.maximum(cum, 0), 1) - cum).max(1); tot = cum[:, -1]
q = lambda a, p: np.percentile(a, p)
print(f"\n== Monte Carlo 1 an (10 000 tirages de 52 semaines)")
print(f"gain annuel : médiane {q(tot,50):+.0f} € | 5 % pire {q(tot,5):+.0f} € | année perdante {(tot<0).mean()*100:.1f} %")
print(f"drawdown max : médiane {q(dd,50):.0f} € | 95e centile {q(dd,95):.0f} € | > 3 000 € {(dd>3000).mean()*100:.0f} % | > 5 000 € {(dd>5000).mean()*100:.1f} %")
