"""Lot 8 (stratégies 2 à 5) — Nasdaq, S&P 500 en contrôle. Règles fixées avant le test (heure de New York, séance 09:30-16:00).

2. Cassure du plus haut / plus bas de la veille : 1er franchissement entre 09:30 et 15:00 (à l'ouverture si gap au-delà) ;
   deux sens ; stop = milieu du range de la veille ; sortie 16:00.
3. Power hour : à 15:00, si |cours 14:59 − ouverture| ≥ 0,5 ATR14 → entrée à 15:00 dans ce sens ; stop = 0,25 ATR ; sortie 16:00.
4. Nuit conditionnelle : si clôture > ouverture et clôture dans le quart haut du range du jour → achat à la clôture 16:00,
   vente à l'ouverture 09:30 suivante. 1 R = 0,5 ATR. Swap 6 %/an du nominal par nuit calendaire.
5. Williams k = 0,5 seulement après une séance NR7 (amplitude la plus faible des 7 dernières) ; comparé au Williams tous les jours.
Coûts aller-retour : NASDAQ100 1,5 ; SP500 0,75. 100 € par R. ATR14 = séances précédentes.
Critère standard : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, OOS > 0 avec coûts doublés. Strict : + t ≥ 2.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402

COST = {"NASDAQ100": 1.5, "SP500": 0.75}


def sessions(inst):
    df = load_m1(inst, "America/New_York")
    df = df[(df["hm"] >= 570) & (df["hm"] < 960)]
    S = {}
    for d, g in df.groupby("day"):
        if d.dayofweek < 5 and len(g) >= 360 and g["hm"].iloc[0] == 570:
            S[d] = tuple(g[c].values for c in ("hm", "open", "high", "low", "close"))
    return S


def exit_px(hm, O, H, L, C, k, d, stop):
    if (L[k] <= stop) if d == 1 else (H[k] >= stop):
        return stop
    for j in range(k + 1, len(hm)):
        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
            return O[j] if ((O[j] < stop) if d == 1 else (O[j] > stop)) else stop
    return C[-1]


def run(inst):
    S = sessions(inst)
    keys = sorted(S)
    Hd = np.array([S[k][2].max() for k in keys]); Ld = np.array([S[k][3].min() for k in keys])
    Od = np.array([S[k][1][0] for k in keys]); Cd = np.array([S[k][4][-1] for k in keys])
    pc = np.r_[np.nan, Cd[:-1]]
    tr = np.nanmax(np.vstack([Hd - Ld, abs(Hd - pc), abs(Ld - pc)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    rng = Hd - Ld
    rows = []
    for i in range(7, len(keys)):
        day = keys[i]
        if (day - keys[i - 1]).days > 4 or np.isnan(atr[i]):
            continue
        hm, O, H, L, C = S[day]
        # 2. Cassure de la veille
        ph, pl = Hd[i - 1], Ld[i - 1]
        mid = (ph + pl) / 2
        idx = np.where(hm < 900)[0]
        up, dn = H[idx] > ph, L[idx] < pl
        hit = up | dn
        if hit.any():
            j = int(hit.argmax())
            if not (up[j] and dn[j]):
                k, d = idx[j], (1 if up[j] else -1)
                entry = max(O[k], ph) if d == 1 else min(O[k], pl)
                risk = (entry - mid) * d
                if risk > 0:
                    rows.append((inst, "Cassure de la veille", day, d, entry, exit_px(hm, O, H, L, C, k, d, mid), risk, 0))
        # 3. Power hour
        k15 = np.where(hm >= 900)[0]
        if len(k15) and hm[k15[0]] < 910:
            k = k15[0]
            move = C[k - 1] - O[0]
            if abs(move) >= 0.5 * atr[i]:
                d = 1 if move > 0 else -1
                entry = O[k]
                stop = entry - d * 0.25 * atr[i]
                rows.append((inst, "Power hour", day, d, entry, exit_px(hm, O, H, L, C, k, d, stop), 0.25 * atr[i], 0))
        # 4. Nuit conditionnelle (achat à la clôture du jour i, vente à l'ouverture du jour i+1)
        if i + 1 < len(keys) and (keys[i + 1] - day).days <= 4:
            if Cd[i] > Od[i] and rng[i] > 0 and (Cd[i] - Ld[i]) / rng[i] >= 0.75:
                nights = (keys[i + 1] - day).days
                swap = Cd[i] * 0.06 * nights / 360
                rows.append((inst, "Nuit conditionnelle", day, 1, Cd[i], Od[i + 1], 0.5 * atr[i], swap))
        # 5. Williams (tous les jours / après NR7)
        pr = rng[i - 1]
        upl, dnl = O[0] + 0.5 * pr, O[0] - 0.5 * pr
        up, dn = H >= upl, L <= dnl
        hit = up | dn
        if hit.any():
            j = int(hit.argmax())
            if not (up[j] and dn[j]):
                d = 1 if up[j] else -1
                entry = max(O[j], upl) if d == 1 else min(O[j], dnl)
                risk = (entry - O[0]) * d
                if risk > 0:
                    px = exit_px(hm, O, H, L, C, j, d, O[0])
                    rows.append((inst, "Williams · tous les jours", day, d, entry, px, risk, 0))
                    if rng[i - 1] == rng[i - 7:i].min():
                        rows.append((inst, "Williams · après NR7", day, d, entry, px, risk, 0))
    t = pd.DataFrame(rows, columns=["instrument", "strategie", "day", "d", "entry", "exit", "risque", "swap"])
    t["gross_r"] = (t["exit"] - t["entry"]) * t["d"] / t["risque"]
    t["cost_r"] = (COST[inst] + t["swap"]) / t["risque"]
    return t


def main():
    t = pd.concat([run(i) for i in COST])
    t = t[t["day"] >= "2020-01-01"]
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (inst, s), g in t.groupby(["instrument", "strategie"]):
        g = g.sort_values("day")
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        r = {"instrument": inst, "strategie": s, "brut": st(g["gross_r"].values), "net": st(x.values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "sans_top5": float(x.drop(x.nlargest(5).index).mean()),
             "par_annee": {str(y): round(float(v["net_r"].mean()), 3) for y, v in g.groupby(g["day"].dt.year)}}
        r["standard"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        r["strict"] = bool(r["standard"] and r["t_stat"] >= 2)
        res.append(r)
        tag = "✔✔" if r["strict"] else ("✔ " if r["standard"] else "  ")
        print(f"{tag} {inst:9} {s:26} n{r['net']['trades']:>5} WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} "
              f"PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} "
              f"sansTop5{r['sans_top5']:+.3f} {r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€ ans{r['par_annee']}")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
