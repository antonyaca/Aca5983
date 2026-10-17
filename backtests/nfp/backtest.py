"""Jours de NFP (Employment Situation, publication 08:30 New York). Règles fixées avant le test.

Dates : calendrier officiel BLS (https://www.bls.gov/bls/news-release/empsit.htm), 2020-02 → 2026-10 ; octobre 2025 non publié.
Variante « avant » : range 08:00-08:30 ; 1er franchissement entre 08:30 et 11:00 ; stop = bord opposé.
Variante « après » : range 08:30-08:45 ; 1er franchissement entre 08:45 et 11:00 ; stop = bord opposé.
Sorties : clôture 16:00 ou TP 1:2. Deux sens. Marchés : NASDAQ100, XAUUSD.
Coûts : le double des coûts habituels (spread d'annonce) ; test de résistance à 4 fois.
Critère : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, OOS > 0 avec frais encore doublés. 100 € par R.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402

NFP = """2020-02-07 2020-03-06 2020-04-03 2020-05-08 2020-06-05 2020-07-02 2020-08-07 2020-09-04 2020-10-02 2020-11-06 2020-12-04
2021-01-08 2021-02-05 2021-03-05 2021-04-02 2021-05-07 2021-06-04 2021-07-02 2021-08-06 2021-09-03 2021-10-08 2021-11-05 2021-12-03
2022-01-07 2022-02-04 2022-03-04 2022-04-01 2022-05-06 2022-06-03 2022-07-08 2022-08-05 2022-09-02 2022-10-07 2022-11-04 2022-12-02
2023-01-06 2023-02-03 2023-03-10 2023-04-07 2023-05-05 2023-06-02 2023-07-07 2023-08-04 2023-09-01 2023-10-06 2023-11-03 2023-12-08
2024-01-05 2024-02-02 2024-03-08 2024-04-05 2024-05-03 2024-06-07 2024-07-05 2024-08-02 2024-09-06 2024-10-04 2024-11-01 2024-12-06
2025-01-10 2025-02-07 2025-03-07 2025-04-04 2025-05-02 2025-06-06 2025-07-03 2025-08-01 2025-09-05 2025-11-20 2025-12-16
2026-01-09 2026-02-11 2026-03-06 2026-04-03 2026-05-08 2026-06-05 2026-07-02 2026-08-07 2026-09-04 2026-10-02""".split()
COST = {"NASDAQ100": 1.5 * 2, "XAUUSD": 0.47 * 2}


def run(inst):
    df = load_m1(inst, "America/New_York")
    dates = set(pd.to_datetime(NFP))
    rows, missing = [], []
    for day, g in df[df["day"].isin(dates)].groupby("day"):
        hm, O, H, L, C = (g[c].values for c in ("hm", "open", "high", "low", "close"))
        end = np.where(hm >= 960)[0]
        last = (end[0] - 1) if len(end) else len(hm) - 1
        for var, r0, r1 in (("avant (08:00-08:30)", 480, 510), ("après (08:30-08:45)", 510, 525)):
            rg = (hm >= r0) & (hm < r1)
            if rg.sum() < 0.8 * (r1 - r0):
                missing.append((str(day.date()), var)); continue
            hi, lo = H[rg].max(), L[rg].min()
            idx = np.where((hm >= r1) & (hm < 660))[0]
            up, dn = H[idx] > hi, L[idx] < lo
            hit = up | dn
            if not hit.any():
                continue
            j = int(hit.argmax())
            if up[j] and dn[j]:
                continue
            k, d = idx[j], (1 if up[j] else -1)
            entry = max(O[k], hi) if d == 1 else min(O[k], lo)
            stop = lo if d == 1 else hi
            risk = (entry - stop) * d
            if risk <= 0:
                continue
            for ex in ("clôture 16:00", "TP 1:2"):
                tp = entry + 2 * d * risk if ex == "TP 1:2" else None
                if (L[k] <= stop) if d == 1 else (H[k] >= stop):
                    px = stop
                else:
                    px = C[last]
                    for i in range(k + 1, last + 1):
                        if (L[i] <= stop) if d == 1 else (H[i] >= stop):
                            px = O[i] if ((O[i] < stop) if d == 1 else (O[i] > stop)) else stop; break
                        if tp is not None and ((H[i] >= tp) if d == 1 else (L[i] <= tp)):
                            px = O[i] if ((O[i] > tp) if d == 1 else (O[i] < tp)) else tp; break
                rows.append({"instrument": inst, "reglage": f"{var} · {ex}", "day": day, "d": d, "risque": risk,
                             "gross_r": (px - entry) * d / risk, "cost_r": COST[inst] / risk})
    return rows, missing


def main():
    rows, miss = [], []
    for inst in COST:
        r, m = run(inst); rows += r; miss += [(inst,) + x for x in m]
    print("jours NFP sans données suffisantes :", miss or "aucun")
    t = pd.DataFrame(rows)
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (inst, reg), g in t.groupby(["instrument", "reglage"]):
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        r = {"instrument": inst, "reglage": reg, "brut": st(g["gross_r"].values), "net": st(x.values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "sans_top3": float(x.drop(x.nlargest(3).index).mean()),
             "par_annee": {str(y): round(float(v["net_r"].sum()), 2) for y, v in g.groupby(g["day"].dt.year)}}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {inst:9} {reg:36} n{r['net']['trades']:>3} WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} "
              f"En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f}({r['is']['trades']}) OOS{r['oos']['e_r']:+.3f}({r['oos']['trades']}) "
              f"x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} sansTop3{r['sans_top3']:+.3f} {r['net']['resultat_eur']:>6.0f}€ DD{r['net']['max_dd_eur']:>5.0f}€ "
              f"R/an{r['par_annee']}")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
