"""Annonces macro US : CPI (08:30 NY), FOMC (14:00 NY), et rappel NFP (08:30 NY). Règle = celle validée sur le NFP, inchangée.

Range des 30 minutes avant l'annonce ; 1er franchissement entre l'annonce et +2 h 30 (sans dépasser 15:30) ; deux sens ;
stop = bord opposé ; sortie TP 1:2 ou clôture 16:00. Coûts doublés (spread d'annonce).
Dates officielles : BLS (CPI, NFP) et Réserve fédérale (FOMC, réunions programmées uniquement ; exclus : 2020-03-02,
2020-03-15 en urgence, 2025-08-22 vote par écrit).
Critère « standard » : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, OOS > 0 avec coûts encore doublés.
Critère « strict » (lot 8, plus de 300 variantes déjà testées) : standard + t ≥ 2.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("nfp_bt", os.path.join(os.path.dirname(HERE), "nfp", "backtest.py"))
_nfp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_nfp)
NFP = _nfp.NFP

CPI = """2020-02-13 2020-03-11 2020-04-10 2020-05-12 2020-06-10 2020-07-14 2020-08-12 2020-09-11 2020-10-13 2020-11-12 2020-12-10
2021-01-13 2021-02-10 2021-03-10 2021-04-13 2021-05-12 2021-06-10 2021-07-13 2021-08-11 2021-09-14 2021-10-13 2021-11-10 2021-12-10
2022-01-12 2022-02-10 2022-03-10 2022-04-12 2022-05-11 2022-06-10 2022-07-13 2022-08-10 2022-09-13 2022-10-13 2022-11-10 2022-12-13
2023-01-12 2023-02-14 2023-03-14 2023-04-12 2023-05-10 2023-06-13 2023-07-12 2023-08-10 2023-09-13 2023-10-12 2023-11-14 2023-12-12
2024-01-11 2024-02-13 2024-03-12 2024-04-10 2024-05-15 2024-06-12 2024-07-11 2024-08-14 2024-09-11 2024-10-10 2024-11-13 2024-12-11
2025-01-15 2025-02-12 2025-03-12 2025-04-10 2025-05-13 2025-06-11 2025-07-15 2025-08-12 2025-09-11 2025-10-24 2025-12-18
2026-01-13 2026-02-13 2026-03-11 2026-04-10 2026-05-12 2026-06-10 2026-07-14 2026-08-12 2026-09-11 2026-10-14""".split()
FOMC = """2020-01-29 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10
2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29 2026-09-16""".split()
EVENTS = {"NFP": (NFP, 510), "CPI": (CPI, 510), "FOMC": (FOMC, 840)}   # minute de l'annonce (NY)
COST = {"NASDAQ100": 1.5 * 2, "SP500": 0.75 * 2}


def run(inst):
    df = load_m1(inst, "America/New_York")
    rows, missing = [], []
    for ev, (dates, t0) in EVENTS.items():
        dset = set(pd.to_datetime(dates))
        got = set()
        for day, g in df[df["day"].isin(dset)].groupby("day"):
            hm, O, H, L, C = (g[c].values for c in ("hm", "open", "high", "low", "close"))
            rg = (hm >= t0 - 30) & (hm < t0)
            if rg.sum() < 24:
                continue
            got.add(day)
            hi, lo = H[rg].max(), L[rg].min()
            idx = np.where((hm >= t0) & (hm < min(t0 + 150, 930)))[0]
            if len(idx) == 0:
                continue
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
            endi = np.where(hm >= 960)[0]
            last = (endi[0] - 1) if len(endi) else len(hm) - 1
            for ex in ("TP 1:2", "clôture 16:00"):
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
                rows.append({"instrument": inst, "evenement": ev, "sortie": ex, "day": day, "d": d, "risque": risk,
                             "gross_r": (px - entry) * d / risk, "cost_r": COST[inst] / risk})
        missing.append((inst, ev, len(dset) - len(got)))
    return rows, missing


def main():
    rows, miss = [], []
    for inst in COST:
        r, m = run(inst); rows += r; miss += m
    print("annonces sans données suffisantes (marché, événement, nombre) :", miss)
    t = pd.DataFrame(rows)
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    groups = list(t.groupby(["instrument", "evenement", "sortie"]))
    groups += [((i, "CPI + FOMC", s), g) for (i, s), g in t[t["evenement"] != "NFP"].groupby(["instrument", "sortie"])]
    groups += [((i, "NFP + CPI + FOMC", s), g) for (i, s), g in t.groupby(["instrument", "sortie"])]
    for (inst, ev, ex), g in groups:
        g = g.sort_values("day")
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        r = {"instrument": inst, "evenement": ev, "sortie": ex, "brut": st(g["gross_r"].values), "net": st(x.values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "sans_top3": float(x.drop(x.nlargest(3).index).mean())}
        r["standard"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        r["strict"] = bool(r["standard"] and r["t_stat"] >= 2)
        res.append(r)
        tag = "✔✔" if r["strict"] else ("✔ " if r["standard"] else "  ")
        print(f"{tag} {inst:9} {ev:17} {ex:13} n{r['net']['trades']:>4} WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} "
              f"En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} "
              f"t{r['t_stat']:+.2f} sansTop3{r['sans_top3']:+.3f} {r['net']['resultat_eur']:>6.0f}€ DD{r['net']['max_dd_eur']:>5.0f}€")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
