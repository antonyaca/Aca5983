"""Stop de sécurité sur RSI2 et « 3 baisses » (Nasdaq + S&P), 18/10/2026. Règles fixées AVANT calcul.

Signaux et sorties identiques à verification/verif_swing.py (barres 09:30-15:55 NY, exécution à 15:55).
Ajout : stop de sécurité à entrée − k × ATR14 (ATR de la séance du signal), k ∈ {2 ; 3} — 2 valeurs seulement.
Chaque séance de détention : si l'ouverture 09:30 est déjà sous le stop → sortie à l'ouverture (gap) ; sinon si le plus
bas de la séance touche le stop → sortie au stop ; sinon sortie normale à 15:55 si le signal de sortie est donné.
(Limite : la cotation de nuit du CFD n'est pas suivie ; un franchissement la nuit est pris à l'ouverture suivante.)
Comparaison avec la version sans stop (contrôle : doit retrouver verif_swing.py), puis portefeuille des 4 stratégies
dimensionné pour 100 €/jour en moyenne : pire jour, drawdown, mois positifs.
"""
import importlib.util, os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(os.path.dirname(H)); sys.path.insert(0, C)
import lib  # noqa
s = importlib.util.spec_from_file_location("vs_src", os.path.join(C, "verification", "verif_swing.py"))
src = open(os.path.join(C, "verification", "verif_swing.py")).read()
ns = {"__file__": os.path.join(C, "verification", "verif_swing.py")}
exec(src[:src.index("out = {}")], ns)          # importe bars() sans lancer le calcul
bars = ns["bars"]


def run(inst, b, es, xs, maxd, k):
    days, O, Hh, L, Cc, atr = b.index, b.O.values, b.H.values, b.L.values, b.C.values, b.atr.values
    sl, _ = lib.SWAP[inst]; rows = []; i = 0; n = len(b)
    while i < n - 2:
        if not es[i] or not np.isfinite(atr[i]):
            i += 1; continue
        R = atr[i]; entry = Cc[i]; stop = entry - k * R if k else -np.inf
        j, px = i + 1, None
        while j < n:
            if (days[j] - days[j - 1]).days > 7:
                px = None; break
            if O[j] <= stop:
                px = O[j]; break
            if L[j] <= stop:
                px = stop; break
            if xs[j] or (maxd and j - i >= maxd):
                px = Cc[j]; break
            j += 1
        if px is None or j >= n - 1:
            i = j + 1; continue
        nights = (days[j] - days[i]).days
        rows.append({"day": days[i], "instrument": inst, "gross_r": (px - entry) / R,
                     "cost_r": lib.COST[inst] / R + entry * sl * nights / 360 / R})
        i = j + 1
    return rows


out = {}
for inst in ("NASDAQ100", "SP500"):
    b = bars(inst); Cl = b.C
    sig = {"RSI2": (((b.rsi < 10) & (Cl > b.sma200)).values, (Cl > b.sma5).values, None),
           "3 baisses": (((Cl < Cl.shift()) & (Cl.shift() < Cl.shift(2)) & (Cl.shift(2) < Cl.shift(3))).values,
                         (Cl > Cl.shift()).values, 5)}
    for name, (es, xs, md) in sig.items():
        for k in (None, 3, 2):
            out.setdefault((name, k), []).extend(run(inst, b, es, xs, md, k))
for (name, k), rows in out.items():
    t = pd.DataFrame(rows); x = t.gross_r - t.cost_r
    r = lib.evaluate(t, f"{name} · {'sans stop' if k is None else f'stop {k} ATR'}")
    print(lib.line(r), f"| pire trade {x.min():+.2f} R")
    t.to_csv(os.path.join(H, f"swing_{name.replace(' ', '_')}_{'0' if k is None else k}.csv.gz"), index=False, float_format="%.6f")

# Portefeuille 4 stratégies (Williams régulier) dimensionné pour 100 €/jour
v = pd.read_csv(f"{H}/verif_v04_trades.csv.gz", parse_dates=["day"]).assign(cost_r=lambda x: x.entry * 1.25e-4 / x.risque)
nf = pd.read_csv(f"{C}/nfp_2011/trades_XAUUSD.csv.gz", parse_dates=["day"]); nf = nf[nf.reglage == "avant (08:00-08:30) · TP 1:2"]
for k in (None, 3, 2):
    sw = [pd.DataFrame(out[(nm, k)]) for nm in ("RSI2", "3 baisses")]
    t = pd.concat([x[["day", "gross_r", "cost_r"]] for x in [v, nf] + sw]); t = t[t.day >= lib.START]
    p1 = (t.gross_r - t.cost_r).groupby(t.day).sum()
    full = p1.reindex(pd.bdate_range(lib.START, lib.DATA_END), fill_value=0)
    risk = 100 / full.mean(); pe = full * risk; cum = pe.cumsum(); dd = (cum.cummax().clip(lower=0) - cum).max()
    m = pe.resample("ME").sum(); y = pe.resample("YE").sum()
    print(f"Portefeuille ({'sans stop' if k is None else f'stop {k} ATR'}) : risque {risk:.0f} €/trade | pire jour {pe.min():,.0f} € | "
          f"drawdown {dd:,.0f} € | jours tradés positifs {(p1 > 0).mean()*100:.0f} % | mois positifs {(m > 0).mean()*100:.0f} % | "
          f"pire mois {m.min():,.0f} € | années positives {(y > 0).sum()}/{len(y)} | pire année {y.min():,.0f} €")
