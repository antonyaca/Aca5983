"""Recodage indépendant (Claude, 17/10/2026) des deux candidats swing de l'agent « retour à la moyenne ».

Code écrit sans réutiliser retour_moyenne/run.py. Barres journalières construites autrement : barre = séance
09:30-15:55 NY ; prix d'exécution = clôture de la minute 15:55 (≈ ouverture de 15:56 dans le code de l'agent).
RSI2 de Wilder calculé par boucle explicite. 1 R = ATR14 (séance du signal incluse), coûts lib.COST + swap lib.SWAP.
Contrôle de robustesse supplémentaire (fixé avant calcul) : exécution à l'OUVERTURE 09:30 de la séance suivante
(entrée et sortie) au lieu de la fin de séance du signal.
 RSI2 : achat si RSI2 < 10 et C > SMA200 ; sortie dès C > SMA5. Nasdaq + S&P.
 3 baisses : achat si 3 clôtures consécutives en baisse ; sortie 1re clôture en hausse ou après 5 séances. Nasdaq + S&P
 (sous-ensemble US du V08 de l'agent, qui inclut FTSE et Nikkei).
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib  # noqa


def bars(inst):
    df = lib.load(inst)
    s = df[(df.hm >= 570) & (df.hm <= 955)]
    g = s.groupby("day")
    b = pd.DataFrame({"O": g.open.first(), "H": g.high.max(), "L": g.low.min(), "C": g.close.last(),
                      "n": g.size(), "first": g.hm.first(), "last": g.hm.last()})
    b = b[(b.n >= 300) & (b["first"] <= 575) & (b["last"] >= 950) & (b.index.dayofweek < 5)]
    pc = b.C.shift()
    b["atr"] = pd.concat([b.H - b.L, (b.H - pc).abs(), (b.L - pc).abs()], axis=1).max(axis=1).rolling(14).mean()
    c = b.C.values
    rsi = np.full(len(c), np.nan); au = ad = None
    for i in range(1, len(c)):
        ch = c[i] - c[i - 1]; u, d = max(ch, 0), max(-ch, 0)
        if i == 2:
            au, ad = (max(c[1]-c[0], 0) + u) / 2, (max(c[0]-c[1], 0) + d) / 2
        elif i > 2:
            au, ad = (au + u) / 2, (ad + d) / 2   # Wilder, période 2 : alpha = 1/2
        if i >= 2:
            rsi[i] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    b["rsi"] = rsi
    b["sma200"], b["sma5"] = b.C.rolling(200).mean(), b.C.rolling(5).mean()
    return b


def run(inst, b, entry_sig, exit_sig, maxd, at_open):
    days, C, O, atr = b.index, b.C.values, b.O.values, b.atr.values
    sl, ss = lib.SWAP[inst]; rows = []; i = 0; n = len(b)
    while i < n - 2:
        if not entry_sig[i] or not np.isfinite(atr[i]):
            i += 1; continue
        j = i + 1
        while j < n and not (exit_sig[j] or (maxd and j - i >= maxd)):
            j += 1
        if j >= n - 1:
            break
        if ((days[i + 1:j + 1] - days[i:j]).days > 7).any():
            i = j + 1; continue
        e_i, x_i = (i + 1, j + 1) if at_open else (i, j)
        pe, px = (O[e_i], O[x_i]) if at_open else (C[e_i], C[x_i])
        nights = (days[x_i] - days[e_i]).days
        R = atr[i]
        rows.append({"day": days[i], "instrument": inst, "gross_r": (px - pe) / R,
                     "cost_r": lib.COST[inst] / R + pe * sl * nights / 360 / R})
        i = j + 1
    return rows


out = {}
for inst in ("NASDAQ100", "SP500"):
    b = bars(inst)
    C = b.C
    sig = {"RSI2": (((b.rsi < 10) & (C > b.sma200)).values, (C > b.sma5).values, None),
           "3 baisses": (((C < C.shift()) & (C.shift() < C.shift(2)) & (C.shift(2) < C.shift(3))).values,
                         (C > C.shift()).values, 5)}
    for name, (es, xs, md) in sig.items():
        for at_open in (False, True):
            out.setdefault((name, at_open), []).extend(run(inst, b, es, xs, md, at_open))
for (name, at_open), rows in out.items():
    t = pd.DataFrame(rows)
    print(lib.line(lib.evaluate(t, f"{name} · {'ouverture J+1' if at_open else 'fin de séance'}")))
for (name, at_open), rows in out.items():
    if not at_open:
        pd.DataFrame(rows).to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"trades_{name.replace(' ', '_')}.csv.gz"), index=False)
