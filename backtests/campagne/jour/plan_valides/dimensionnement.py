"""Dimensionnement du portefeuille (18/10/2026) : le stop de sécurité ne coupe pas les pertes de gap. Test de 2 règles
de taille fixées avant calcul : poids des trades swing (RSI2, 3 baisses, sans stop) à 100 % / 50 % du risque standard ;
objectif 100 €/jour en moyenne. Gains rapportés au jour d'entrée (le « pire jour » est donc le pire trade combiné)."""
import os, sys
import pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(os.path.dirname(H)); sys.path.insert(0, C)
import lib  # noqa
v = pd.read_csv(f"{H}/verif_v04_trades.csv.gz", parse_dates=["day"]).assign(cost_r=lambda x: x.entry * 1.25e-4 / x.risque, w=1.0)
nf = pd.read_csv(f"{C}/nfp_2011/trades_XAUUSD.csv.gz", parse_dates=["day"]); nf = nf[nf.reglage == "avant (08:00-08:30) · TP 1:2"].assign(w=1.0)
sw = pd.concat([pd.read_csv(f"{H}/swing_RSI2_0.csv.gz", parse_dates=["day"]), pd.read_csv(f"{H}/swing_3_baisses_0.csv.gz", parse_dates=["day"])])
for wsw in (1.0, 0.5):
    t = pd.concat([x[["day", "gross_r", "cost_r", "w"]] for x in (v, nf, sw.assign(w=wsw))]); t = t[t.day >= lib.START]
    p1 = ((t.gross_r - t.cost_r) * t.w).groupby(t.day).sum()
    full = p1.reindex(pd.bdate_range(lib.START, lib.DATA_END), fill_value=0)
    risk = 100 / full.mean(); pe = full * risk; cum = pe.cumsum(); dd = (cum.cummax().clip(lower=0) - cum).max()
    m = pe.resample("ME").sum(); y = pe.resample("YE").sum()
    print(f"swing à {wsw:.0%} : risque {risk:.0f} € (swing {risk*wsw:.0f} €) | pire jour {pe.min():,.0f} € | drawdown {dd:,.0f} € | "
          f"jours tradés + {(p1 > 0).mean()*100:.0f} % | mois + {(m > 0).mean()*100:.0f} % | pire mois {m.min():,.0f} € | "
          f"années + {(y > 0).sum()}/{len(y)} | pire année {y.min():,.0f} €")
