"""Revalidation hors échantillon (2011-2019) des 3 stratégies Nasdaq validées sur 2020-2026.

Code d'origine réutilisé SANS MODIFICATION (backtests/robustesse/three_strats.py : pré-market, Williams k=0,5, ORB 30 min
achats seuls), seule la source de données change (lib.load : historique depuis nov. 2010).
Contrôle de non-régression : les résultats 2020-2026 doivent être identiques à ceux de three_strats (Williams identique,
ORB ≈ +15 441 €, pré-market ≈ +11 205 €).
Juge de paix : période 2011-2019, jamais vue lors de la mise au point. Coûts fixes en points (1,5 pt) : plus pénalisants
en 2011 (Nasdaq ≈ 2 300) qu'en 2024 (≈ 18 000) — on garde l'hypothèse prudente et on montre le coût en R.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CAMP = os.path.dirname(HERE)
sys.path.insert(0, CAMP)
sys.path.insert(0, os.path.join(os.path.dirname(CAMP), "robustesse"))
import lib  # noqa: E402
import three_strats  # noqa: E402

three_strats.load_m1 = lambda inst, tz: lib.load(inst, tz)


def stats(x):
    x = np.asarray(x)
    pos, neg = x[x > 0].sum(), -x[x < 0].sum()
    cum = np.cumsum(x)
    dd = float((np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max()) * 100
    t = x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else 0
    return {"trades": len(x), "e_r": round(float(x.mean()), 3), "pf": round(float(pos / neg), 2) if neg else None,
            "eur": round(float(x.sum() * 100)), "dd_eur": round(dd), "t": round(float(t), 2)}


def main():
    out = {}
    for inst in ("NASDAQ100", "SP500"):
        t = three_strats.run(inst)
        t = t[t["day"] >= "2011-01-01"].copy()
        t["net"] = t["gross_r"] - t["cost_r"]
        t["net2"] = t["gross_r"] - 2 * t["cost_r"]
        for s, g in t.groupby("strategie"):
            a, b = g[g["day"] < "2020-01-01"], g[g["day"] >= "2020-01-01"]
            r = {"2011-2019": stats(a["net"]), "2011-2019_frais_x2": round(float(a["net2"].mean()), 3),
                 "2011-2019_cout_median_R": round(float(a["cost_r"].median()), 3),
                 "2020-2026 (contrôle)": stats(b["net"]),
                 "par_annee_eur": {str(y): round(float(v.sum() * 100)) for y, v in g.groupby(g["day"].dt.year)["net"]}}
            out[f"{inst} · {s}"] = r
            print(inst, s, json.dumps(r, ensure_ascii=False))
        t.to_csv(os.path.join(HERE, f"trades_{inst}.csv.gz"), index=False, float_format="%.6f")
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
