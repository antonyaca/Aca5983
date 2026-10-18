"""Deux edges académiques sur indices US (pistes 1 et 2 de jour/recherche), 18/10/2026. Règles fixées AVANT calcul.

A « Jours d'annonce » (Savor & Wilson 2013 ; Ai, Bansal & Guo 2023) : achat à la clôture (15:55 NY) de la veille d'un jour
  NFP, CPI ou FOMC programmé ; vente à la clôture (15:55) du jour d'annonce. 1 nuit de swap.
B « Semaines paires du cycle FOMC » (Cieslak, Morse & Vissing-Jorgensen 2019) : jour 0 = jour de décision FOMC ;
  semaines paires = jours de bourse [-1, +3], [9, 13], [19, 23], [29, 33] (comptés en séances depuis le jour 0) ;
  achat à la clôture de la séance précédant chaque fenêtre, vente à la clôture de la dernière séance de la fenêtre.
Marchés : Nasdaq et S&P (barres 09:30-15:55 de verification/verif_swing.py). 1 R = ATR14 du jour d'entrée.
Coûts : lib.COST + swap lib.SWAP par nuit calendaire. Jugement : lib.evaluate sur les 2 indices réunis (2 tests).
Dates : NFP/CPI/FOMC 2011-2019 du dépôt (BLS, Fed, relevées par les agents) + 2020-2026 (events/, nfp/).
"""
import importlib.util, os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(os.path.dirname(H)); BT = os.path.dirname(C)
sys.path.insert(0, C)
import lib  # noqa
src = open(os.path.join(C, "verification", "verif_swing.py")).read()
ns = {"__file__": os.path.join(C, "verification", "verif_swing.py")}; exec(src[:src.index("out = {}")], ns); bars = ns["bars"]
s = importlib.util.spec_from_file_location("ev_bt", os.path.join(BT, "events", "backtest.py"))
ev = importlib.util.module_from_spec(s); s.loader.exec_module(ev)
fx = open(os.path.join(C, "jour", "forex_or", "run.py")).read(); d = {}
exec(fx[fx.index('CPI_BLS = """'):fx.index("assert len(NFP_2011_2019)")], {}, d)
nfp_src = open(os.path.join(C, "nfp_2011", "run.py")).read(); d2 = {}
exec(nfp_src[nfp_src.index('BLS_2011_2019 = """'):nfp_src.index("assert len(BLS_2011_2019)")], {}, d2)
NFP = set(pd.to_datetime(d2["BLS_2011_2019"] + list(ev.NFP)))
CPI = set(pd.to_datetime(d["CPI_2011_2019"] + list(ev.CPI)))
FOMC = sorted(set(pd.to_datetime(d["FOMC_2011_2019"] + list(ev.FOMC))))
ANN = NFP | CPI | set(FOMC)
WINDOWS = [(-1, 3), (9, 13), (19, 23), (29, 33)]


def trade(inst, b, i, j, rule):
    days, Cc, atr = b.index, b.C.values, b.atr.values
    if not np.isfinite(atr[i]) or j <= i:
        return None
    sl, _ = lib.SWAP[inst]; R = atr[i]; nights = (days[j] - days[i]).days
    if nights > 10:
        return None
    return {"regle": rule, "instrument": inst, "day": days[i], "gross_r": (Cc[j] - Cc[i]) / R,
            "cost_r": lib.COST[inst] / R + Cc[i] * sl * nights / 360 / R}


rows = []
for inst in ("NASDAQ100", "SP500"):
    b = bars(inst); days = b.index; pos = {dd: k for k, dd in enumerate(days)}
    for k in range(1, len(days)):                       # A : veille → jour d'annonce
        if days[k] in ANN:
            r = trade(inst, b, k - 1, k, "A jours d'annonce")
            if r: rows.append(r)
    for f in FOMC:                                       # B : semaines paires du cycle
        if f not in pos:
            continue
        k0 = pos[f]
        for a, z in WINDOWS:
            i, j = k0 + a - 1, k0 + z
            if i >= 0 and j < len(days):
                r = trade(inst, b, i, j, "B semaines paires FOMC")
                if r: rows.append(r)
t = pd.DataFrame(rows)
t.to_csv(os.path.join(H, "edges_fed_trades.csv.gz"), index=False, float_format="%.6f")
for rule, g in t.groupby("regle"):
    print(lib.line(lib.evaluate(g, f"{rule} · 2 indices")), "| brut %+.3f" % g.gross_r.mean())
    for inst, gi in g.groupby("instrument"):
        print("   ", lib.line(lib.evaluate(gi, f"{rule[:1]} {inst}")))
