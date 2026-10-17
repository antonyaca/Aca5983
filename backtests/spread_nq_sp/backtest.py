"""Écart Nasdaq / S&P 500 intraday — retour à la moyenne. Règles fixées avant le test (heure de New York, séance 09:30-16:00).

Écart(t) = ln(NQ_t / NQ_ouverture) − β · ln(SP_t / SP_ouverture), β = régression des rendements 1 min NQ sur SP des 20 séances
précédentes. σ = écart-type de l'écart sur toutes les minutes des 20 séances précédentes. z = écart / σ.
Entrée (10:00-15:00, 1 trade/jour) : z > +seuil → vendre NQ / acheter β·SP ; z < −seuil → l'inverse. Exécution au prix de clôture
de la minute du signal. Sortie : z repasse par 0, ou stop à |z| ≥ 4, ou clôture 16:00.
Taille : 1 R = perte si l'écart s'écarte de 2σ (de 2 à 4 avec le seuil 2 ; de 3 à 5 avec le seuil 3, stop = seuil + 2).
Coûts : deux jambes ; aller-retour NQ 1,5 point, SP 0,75 point (× β en nominal), convertis en R.
Seuils testés : 2 et 3. Critère habituel. 100 € par R.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402


def sessions(inst):
    df = load_m1(inst, "America/New_York")
    df = df[(df["hm"] >= 570) & (df["hm"] < 960)]
    out = {}
    for d, g in df.groupby("day"):
        if d.dayofweek < 5 and len(g) >= 370 and g["hm"].iloc[0] == 570:
            out[d] = g.set_index("hm")["close"].reindex(range(570, 960)).ffill().values
    return out


def main():
    nq, sp = sessions("NASDAQ100"), sessions("SP500")
    days = sorted(set(nq) & set(sp))
    hist = []                       # (rendements 1 min NQ, SP, écart du jour) des séances passées
    rows = []
    for day in days:
        a, b = nq[day], sp[day]
        if np.isnan(a).any() or np.isnan(b).any():
            continue
        ra, rb = np.diff(np.log(a)), np.diff(np.log(b))
        if len(hist) >= 20:
            HA = np.concatenate([h[0] for h in hist[-20:]]); HB = np.concatenate([h[1] for h in hist[-20:]])
            beta = float(np.dot(HA, HB) / np.dot(HB, HB))
            sig = float(np.concatenate([np.log(h[2]) - beta * np.log(h[3]) for h in hist[-20:]]).std())
            spread = np.log(a / a[0]) - beta * np.log(b / b[0])
            z = spread / sig
            cost_ret = 1.5 / a[0] + beta * 0.75 / b[0]          # coût aller-retour des deux jambes, en rendement
            for thr in (2.0, 3.0):
                stop_z = thr + 2.0
                R_ret = 2.0 * sig                                 # 1 R = 2σ de mouvement défavorable de l'écart
                k = None
                for m in range(30, 330):                           # 10:00 → 15:00
                    if abs(z[m]) >= thr:
                        k = m; break
                if k is None:
                    continue
                d = -1 if z[k] > 0 else 1                           # d = sens de la position sur l'écart
                ez = z[k]; xz = None
                for m in range(k + 1, 390):
                    if (d == -1 and z[m] <= 0) or (d == 1 and z[m] >= 0):
                        xz = z[m]; why = "retour à 0"; break
                    if abs(z[m]) >= stop_z and np.sign(z[m]) == np.sign(ez):
                        xz = z[m]; why = "stop"; break
                if xz is None:
                    xz = z[389]; why = "clôture"
                gross_r = d * (xz - ez) * sig / R_ret
                rows.append({"reglage": f"seuil z = {thr:.0f}", "day": day, "d": d, "beta": beta, "sigma": sig,
                             "z_in": ez, "z_out": xz, "motif": why, "gross_r": gross_r, "cost_r": cost_ret / R_ret})
        hist.append((ra, rb, a / a[0], b / b[0]))
    t = pd.DataFrame(rows)
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for reg, g in t.groupby("reglage"):
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        r = {"reglage": reg, "brut": st(g["gross_r"].values), "net": st(x.values), "is": st(is_["net_r"].values),
             "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "beta_median": float(g["beta"].median()),
             "cout_median_r": float(g["cost_r"].median()), "motifs": g["motif"].value_counts().to_dict(),
             "par_annee": {str(y): round(float(v["net_r"].mean()), 3) for y, v in g.groupby(g["day"].dt.year)}}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {reg} n{r['net']['trades']} WR{r['net']['win_rate']:.1f} Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} "
              f"PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} "
              f"{r['net']['resultat_eur']:.0f}€ DD{r['net']['max_dd_eur']:.0f}€ β{r['beta_median']:.2f} coût{r['cout_median_r']:.3f}R "
              f"{r['motifs']} ans{r['par_annee']}")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
