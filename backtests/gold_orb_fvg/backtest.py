"""Or — ORB 30 min ouverture New York + retest de FVG M1. Règles fixées avant le test (heure de New York).

Range        : 09:30-10:00.
Cassure      : 1re clôture M1 au-dessus du haut (achat) ou sous le bas (vente), entre 10:00 et 12:00.
FVG          : 1er FVG M1 dans le sens de la cassure dont la 3e bougie est entre la bougie de cassure et 30 min après.
               Haussier : bas[i] > haut[i-2] → zone [haut[i-2], bas[i]]. Baissier : haut[i] < bas[i-2].
Entrée       : limite au bord du FVG (bas[i] en achat) au 1er retour dans les 60 min suivant le FVG, avant 14:00.
               Annulé si le prix touche l'objectif 1R avant le retest.
Stop         : bas de la 1re bougie du FVG (haut en vente).
Sorties      : A = 100 % à 1R ; B = 50 % à 1R puis stop au point d'entrée, 50 % à 2R ;
               C = 50 % à 1R puis stop au point d'entrée, 50 % à la clôture 16:00. Clôture forcée 16:00 dans tous les cas.
Filtre       : aucun / EMA 200 M15 (achat si clôture > EMA à la cassure, vente si <).
Stop minimum : aucun / ≥ 1,5 $.
Un trade max par jour. Coût 0,47 $ aller-retour sur la position entière. 100 € par R.
Critère : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, OOS > 0 avec frais doublés.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402

COST = 0.47


def main():
    df = load_m1("XAUUSD", "America/New_York")
    m15 = df.set_index("time")["close"].resample("15min", label="left", closed="left").last().dropna()
    ema = m15.ewm(span=200, adjust=False).mean()
    # EMA connue à la minute t = EMA de la dernière bougie M15 clôturée
    df["ema"] = ema.shift(1).reindex(df["time"].dt.floor("15min")).values
    rows = []
    for day, g in df.groupby("day"):
        if day.dayofweek >= 5 or day < pd.Timestamp("2020-01-01"):
            continue
        hm, O, H, L, C, E = (g[c].values for c in ("hm", "open", "high", "low", "close", "ema"))
        rg = (hm >= 570) & (hm < 600)
        if rg.sum() < 27:
            continue
        rh, rl = H[rg].max(), L[rg].min()
        idx = np.where((hm >= 600) & (hm < 720))[0]
        brk = [(k, 1) for k in idx if C[k] > rh] + [(k, -1) for k in idx if C[k] < rl]
        if not brk:
            continue
        b, d = min(brk)
        # FVG
        f = None
        for i in range(max(b, 2), len(hm)):
            if hm[i] > hm[b] + 30:
                break
            if d == 1 and L[i] > H[i - 2]:
                f = i; top, stop = L[i], L[i - 2]; break
            if d == -1 and H[i] < L[i - 2]:
                f = i; top, stop = H[i], H[i - 2]; break
        if f is None:
            continue
        risk0 = (top - stop) * d
        if risk0 <= 0:
            continue
        tp1_0 = top + d * risk0
        # retest
        k = None
        for j in range(f + 1, len(hm)):
            if hm[j] > hm[f] + 60 or hm[j] >= 840:
                break
            if (H[j] >= tp1_0) if d == 1 else (L[j] <= tp1_0):
                break
            if (L[j] <= top) if d == 1 else (H[j] >= top):
                k = j; break
        if k is None:
            continue
        entry = min(O[k], top) if d == 1 else max(O[k], top)
        risk = (entry - stop) * d
        if risk <= 0:
            continue
        trend_ok = (not np.isnan(E[b])) and ((C[b] > E[b]) if d == 1 else (C[b] < E[b]))
        tp1, tp2 = entry + d * risk, entry + 2 * d * risk
        end = np.where(hm >= 960)[0]
        last = (end[0] - 1) if len(end) else len(hm) - 1

        def walk(mode):
            """Résultat brut en R de la position entière."""
            if (L[k] <= stop) if d == 1 else (H[k] >= stop):
                return -1.0
            half_done, sl = False, stop
            for j in range(k + 1, last + 1):
                hit_sl = (L[j] <= sl) if d == 1 else (H[j] >= sl)
                if hit_sl:
                    px = O[j] if ((O[j] < sl) if d == 1 else (O[j] > sl)) else sl
                    r = (px - entry) * d / risk
                    return 0.5 + 0.5 * r if half_done else r
                if not half_done and ((H[j] >= tp1) if d == 1 else (L[j] <= tp1)):
                    if mode == "A":
                        return 1.0
                    half_done, sl = True, entry
                    # même minute : on ne compte pas l'objectif 2 (prudent)
                    continue
                if half_done and mode == "B" and ((H[j] >= tp2) if d == 1 else (L[j] <= tp2)):
                    return 0.5 + 0.5 * 2.0
            r = (C[last] - entry) * d / risk
            return 0.5 + 0.5 * r if half_done else r

        for mode, lab in (("A", "A · 100 % à 1R"), ("B", "B · 50 % à 1R + BE, reste à 2R"), ("C", "C · 50 % à 1R + BE, reste à 22h")):
            gr = walk(mode)
            for filt in ("sans filtre", "EMA 200 M15"):
                if filt == "EMA 200 M15" and not trend_ok:
                    continue
                for mn in ("stop libre", "stop ≥ 1,5 $"):
                    if mn == "stop ≥ 1,5 $" and risk < 1.5:
                        continue
                    rows.append({"reglage": f"{lab} | {filt} | {mn}", "day": day, "d": d, "risque": risk, "gross_r": gr})
    t = pd.DataFrame(rows)
    t["cost_r"] = COST / t["risque"]
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for reg, g in t.groupby("reglage"):
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        wk = g.groupby(g["day"].dt.to_period("W"))["net_r"].sum()
        r = {"reglage": reg, "brut": st(g["gross_r"].values), "net": st(x.values), "is": st(is_["net_r"].values),
             "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "risque_median": float(g["risque"].median()),
             "cout_median_r": float(g["cost_r"].median()), "semaines_pos": float((wk > 0).mean() * 100),
             "par_annee": {str(y): round(float(v["net_r"].mean()), 3) for y, v in g.groupby(g["day"].dt.year)}}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {reg:58} n{r['net']['trades']:>4} WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} "
              f"En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} "
              f"t{r['t_stat']:+.2f} {r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€ stop{r['risque_median']:.2f}$ "
              f"coût{r['cout_median_r']:.2f}R")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
