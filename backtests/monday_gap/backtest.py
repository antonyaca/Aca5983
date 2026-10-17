"""Gap du lundi — Nasdaq. Règles fixées avant le test (heure de New York, séance 09:30-16:00).

Gap = ouverture 09:30 du jour − clôture 16:00 de la séance précédente (vendredi pour un lundi).
Condition : |gap| ≥ 0,25 × ATR 14 séances (séances précédentes). Entrée au cours d'ouverture 09:30.
- Comblement : position contre le gap ; objectif = clôture précédente ; stop = entrée ± |gap| (1 R = gap) ; sinon sortie 16:00.
- Continuation : position dans le sens du gap ; stop = clôture précédente (1 R = gap) ; sortie 16:00 ou TP 1:2.
Testé le lundi (hypothèse) et, pour comparaison, les autres jours. Coût 1,5 point aller-retour. 100 € par R.
Critère habituel : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, OOS > 0 avec frais doublés.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402

COST = 1.5


def main():
    df = load_m1("NASDAQ100", "America/New_York")
    df = df[(df["hm"] >= 570) & (df["hm"] < 960)]
    S = {}
    for d, g in df.groupby("day"):
        if d.dayofweek < 5 and len(g) >= 360 and g["hm"].iloc[0] == 570:
            S[d] = (g["open"].values, g["high"].values, g["low"].values, g["close"].values)
    keys = sorted(S)
    H = np.array([S[k][1].max() for k in keys]); L = np.array([S[k][2].min() for k in keys]); C = np.array([S[k][3][-1] for k in keys])
    pc = np.r_[np.nan, C[:-1]]
    tr = np.nanmax(np.vstack([H - L, abs(H - pc), abs(L - pc)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    rows = []
    for i in range(1, len(keys)):
        day, prev = keys[i], keys[i - 1]
        if (day - prev).days > 4 or np.isnan(atr[i]):         # séance précédente manquante
            continue
        O, Hh, Ll, Cc = S[day]
        o, c0 = O[0], C[i - 1]
        gap = o - c0
        if abs(gap) < 0.25 * atr[i]:
            continue
        g_dir = 1 if gap > 0 else -1
        risk = abs(gap)
        jour = "Lundi" if day.dayofweek == 0 else "Mardi-vendredi"

        def walk(d, stop, tp):
            for j in range(len(O)):
                if (Ll[j] <= stop) if d == 1 else (Hh[j] >= stop):
                    return O[j] if (j > 0 and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop
                if tp is not None and ((Hh[j] >= tp) if d == 1 else (Ll[j] <= tp)):
                    return O[j] if (j > 0 and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp
            return Cc[-1]

        for name, d, stop, tp in (("Comblement", -g_dir, o + g_dir * risk, c0),
                                  ("Continuation · clôture", g_dir, c0, None),
                                  ("Continuation · TP 1:2", g_dir, c0, o + g_dir * 2 * risk)):
            px = walk(d, stop, tp)
            rows.append({"jour": jour, "reglage": name, "day": day, "d": d, "risque": risk,
                         "gross_r": (px - o) * d / risk, "cost_r": COST / risk})
    t = pd.DataFrame(rows)
    t = t[t["day"] >= "2020-01-01"]
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (jour, reg), g in t.groupby(["jour", "reglage"]):
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        r = {"jour": jour, "reglage": reg, "brut": st(g["gross_r"].values), "net": st(x.values), "is": st(is_["net_r"].values),
             "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "sans_top3": float(x.drop(x.nlargest(3).index).mean()),
             "par_annee": {str(y): round(float(v["net_r"].mean()), 3) for y, v in g.groupby(g["day"].dt.year)}}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {jour:15} {reg:23} n{r['net']['trades']:>4} WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} "
              f"En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} "
              f"t{r['t_stat']:+.2f} sansTop3{r['sans_top3']:+.3f} {r['net']['resultat_eur']:>6.0f}€ DD{r['net']['max_dd_eur']:>5.0f}€")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
