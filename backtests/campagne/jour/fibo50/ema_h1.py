"""Fibo M15 + filtre de tendance H1 EMA 20 / EMA 50 (demande d'Anto 22/10/2026). Règles fixées AVANT calcul.
Base et grille de gestion identiques à ameliorer.py (entrée 0,5/0,618/0,705/0,786 × objectif 0/−0,272/−0,618).
Bougies H1 en UTC construites depuis le M1 ; EMA sur les clôtures H1 ; on lit la dernière bougie H1 CLÔTURÉE au moment
de la clôture de la bougie M15 de cassure (aucune info future).
  (a) EMA20 > EMA50 → achats seulement ; EMA20 < EMA50 → ventes seulement.
  (b) (a) + clôture de la bougie de cassure du bon côté de l'EMA20 H1.
Découverte 2011-2018, validation 2019-2026 ; critère complet lib.evaluate.
"""
import itertools, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE))); sys.path.insert(0, HERE)
import lib  # noqa
from ameliorer import setups, sim, tstat, MARKETS, ENTRIES, TPS, SPLIT  # noqa

res, keep = [], {}
for inst in MARKETS:
    s, (O, H, L, C), T = setups(inst)
    c = pd.Series(C, index=pd.to_datetime(T, unit="m"))
    h1 = c.resample("1h", label="right", closed="left").last().dropna()    # étiquette = heure de clôture
    e20, e50 = h1.ewm(span=20, adjust=False).mean(), h1.ewm(span=50, adjust=False).mean()
    tclose = pd.to_datetime(T[s.ke.values - 1] + 1, unit="m")              # clôture de la bougie de cassure
    k = np.searchsorted(h1.index.values, tclose.values, side="right") - 1   # dernière H1 clôturée
    up = (e20.values[k] > e50.values[k]); dn = (e20.values[k] < e50.values[k])
    s["ema_a"] = np.where(s.d == 1, up, dn)
    cb = C[s.ke.values - 1]
    s["ema_b"] = s.ema_a & np.where(s.d == 1, cb > e20.values[k], cb < e20.values[k])
    print(inst, f"setups {len(s)} | dans le sens H1 (a) {s.ema_a.mean()*100:.0f}% (b) {s.ema_b.mean()*100:.0f}%", flush=True)
    for f, tp in itertools.product(ENTRIES, TPS):
        fill, g, r = sim(O, H, L, C, s.ke.values.astype(np.int64), s.idl.values.astype(np.int64), s.iend.values.astype(np.int64),
                         s.d.values.astype(np.int64), s.sl.values.astype(float), s.x0.values.astype(float), f, tp)
        t = s[fill].copy(); t["gross_r"] = g[fill]; t["cost_r"] = lib.COST[inst] / r[fill]; t["net"] = t.gross_r - t.cost_r
        for sess in ("Londres", "New York", "les deux"):
            ts = t if sess == "les deux" else t[t.session == sess]
            for flt in ("sans filtre", "ema_a", "ema_b", "contre ema_a"):
                kk = ts if flt == "sans filtre" else (ts[~ts.ema_a] if flt == "contre ema_a" else ts[ts[flt]])
                dsc, val = kk[kk.day < SPLIT], kk[kk.day >= SPLIT]
                res.append(dict(marché=inst, entrée=f, objectif=tp, session=sess, filtre=flt, n=len(kk), brut=kk.gross_r.mean(),
                                net=kk.net.mean(), net_dsc=dsc.net.mean(), net_val=val.net.mean(), t=tstat(kk.net),
                                réussite=(kk.gross_r > 0).mean() * 100))
                keep[(inst, f, tp, sess, flt)] = kk
R = pd.DataFrame(res); R.to_csv(os.path.join(HERE, "ema_h1.csv"), index=False, float_format="%.4f")
print("\nMoyenne sur toute la grille (brut / net par trade, en R) :")
print(R.groupby(["marché", "filtre"])[["brut", "net"]].mean().round(3).unstack("filtre").to_string())
print("\nRéglage de base (entrée 0,5, objectif 0), les deux sessions :")
print(R[(R.entrée == 0.5) & (R.objectif == 0) & (R.session == "les deux")].round(3).to_string(index=False))
f = R[R.filtre.isin(["ema_a", "ema_b"])]
print(f"\nVariantes filtrées positives en découverte ET validation : {((f.net_dsc > 0) & (f.net_val > 0)).sum()} / {len(f)}")
print("\nMeilleures variantes filtrées (classées sur 2011-2018) :")
top = f[f.n >= 150].sort_values("net_dsc", ascending=False).head(6)
for r in top.itertuples():
    print(lib.line(lib.evaluate(keep[(r.marché, r.entrée, r.objectif, r.session, r.filtre)], f"{r.marché} {r.session} e{r.entrée} tp{r.objectif} {r.filtre}")))
