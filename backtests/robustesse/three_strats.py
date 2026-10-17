"""Test de robustesse : les 3 stratégies validées sur le Nasdaq, appliquées SANS MODIFICATION à d'autres marchés.

Règles (identiques aux backtests d'origine, adaptées seulement à l'horaire de la séance principale de chaque marché) :
- Pré-marché : range des 5 h 30 précédant l'ouverture ; 1er franchissement entre l'ouverture et 1 h avant la clôture ;
  deux sens ; stop = bord opposé ; sortie à la clôture.
- Williams : ouverture ± 0,5 × amplitude de la séance précédente ; 1er niveau touché ; stop = ouverture ; deux sens ;
  sortie à la clôture.
- ORB 30 min achats seuls : range des 30 premières minutes ; achat au franchissement du haut jusqu'à 1 h avant la clôture,
  annulé si le bas casse d'abord ; stop = bas du range ; sortie à la clôture.
Exécution : M1 ; entrée au niveau (ou à l'ouverture de la minute si gap) ; stop prioritaire ; si le stop est touché dans la
minute d'entrée → perte ; deux niveaux franchis dans la même minute → pas de trade.
Contrôle : la même fonction appliquée au Nasdaq doit retrouver les résultats d'origine.
Critère (inchangé) : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, E nette OOS > 0 avec frais doublés. 100 € par R.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402

# marché : (fuseau, ouverture, clôture en minutes locales, coût aller-retour en unités de prix)
MARKETS = {
    "NASDAQ100": ("America/New_York", 570, 960, 1.5),
    "SP500":     ("America/New_York", 570, 960, 0.75),
    "WTI":       ("America/New_York", 540, 870, 0.06),   # NYMEX 09:00-14:30
    "XAGUSD":    ("America/New_York", 505, 805, 0.04),   # COMEX argent 08:25-13:25
    "FTSE100":   ("Europe/London",    480, 990, 1.5),    # LSE 08:00-16:30
    "NIKKEI225": ("Asia/Tokyo",       540, 900, 12.0),   # Tokyo 09:00-15:00
}


def day_arrays(inst, tz):
    df = load_m1(inst, tz)
    out = {}
    for d, g in df.groupby("day"):
        if d.dayofweek < 5:
            out[d] = (g["hm"].values, g["open"].values, g["high"].values, g["low"].values, g["close"].values)
    return out


def exit_price(hm, O, H, L, C, k, d, stop, close_m):
    if (L[k] <= stop) if d == 1 else (H[k] >= stop):
        return stop
    last = k
    for j in range(k + 1, len(hm)):
        if hm[j] >= close_m:
            break
        last = j
        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
            return O[j] if ((O[j] < stop) if d == 1 else (O[j] > stop)) else stop
    return C[last]


def first_cross(hm, O, H, L, lo_m, hi_m, up_lvl, dn_lvl):
    idx = np.where((hm >= lo_m) & (hm < hi_m))[0]
    if len(idx) == 0:
        return None
    up = H[idx] > up_lvl if up_lvl is not None else np.zeros(len(idx), bool)
    dn = L[idx] < dn_lvl if dn_lvl is not None else np.zeros(len(idx), bool)
    hit = up | dn
    if not hit.any():
        return None
    j = int(hit.argmax())
    if up[j] and dn[j]:
        return None
    return idx[j], (1 if up[j] else -1)


def run(inst):
    tz, op, cl, cost = MARKETS[inst]
    D = day_arrays(inst, tz)
    cutoff = cl - 60
    rows = []
    prev_range = None
    for day in sorted(D):
        hm, O, H, L, C = D[day]
        s = (hm >= op) & (hm < cl)
        full = s.sum() >= 0.9 * (cl - op) and (hm == op).any()
        if not full:
            continue
        k0 = int(np.where(hm == op)[0][0])
        day_open = O[k0]
        # --- Pré-marché
        pm = (hm >= op - 330) & (hm < op)
        if pm.sum() >= 200:
            ph, pl = H[pm].max(), L[pm].min()
            r = first_cross(hm, O, H, L, op, cutoff, ph, pl)
            if r:
                k, d = r
                entry = max(O[k], ph) if d == 1 else min(O[k], pl)
                stop = pl if d == 1 else ph
                risk = (entry - stop) * d
                if risk > 0:
                    rows.append((inst, "Pré-marché", day, d, entry, exit_price(hm, O, H, L, C, k, d, stop, cl), risk))
        # --- Williams
        if prev_range:
            up, dn = day_open + 0.5 * prev_range, day_open - 0.5 * prev_range
            idx = np.where(s)[0]
            hit_up, hit_dn = H[idx] >= up, L[idx] <= dn
            hit = hit_up | hit_dn
            if hit.any():
                j = int(hit.argmax())
                if not (hit_up[j] and hit_dn[j]):
                    k = idx[j]
                    d = 1 if hit_up[j] else -1
                    entry = max(O[k], up) if d == 1 else min(O[k], dn)
                    risk = (entry - day_open) * d
                    if risk > 0:
                        rows.append((inst, "Williams", day, d, entry, exit_price(hm, O, H, L, C, k, d, day_open, cl), risk))
        # --- ORB 30 min achats seuls
        rg = (hm >= op) & (hm < op + 30)
        if rg.sum() >= 27:
            rh, rl = H[rg].max(), L[rg].min()
            r = first_cross(hm, O, H, L, op + 30, cutoff + 1, rh, rl)
            if r and r[1] == 1:
                k = r[0]
                entry = max(O[k], rh)
                risk = entry - rl
                if risk > 0:
                    rows.append((inst, "ORB achats", day, 1, entry, exit_price(hm, O, H, L, C, k, 1, rl, cl), risk))
        prev_range = H[s].max() - L[s].min()
    t = pd.DataFrame(rows, columns=["instrument", "strategie", "day", "d", "entry", "exit", "risque"])
    t["gross_r"] = (t["exit"] - t["entry"]) * t["d"] / t["risque"]
    t["cost_r"] = cost / t["risque"]
    return t


def main(insts):
    t = pd.concat([run(i) for i in insts])
    t = t[t["day"] >= "2020-01-01"]
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, f"trades_{'_'.join(insts)}.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (inst, strat), g in t.groupby(["instrument", "strategie"]):
        g = g.sort_values("day")
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        r = {"instrument": inst, "strategie": strat, "brut": st(g["gross_r"].values), "net": st(x.values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "sans_top5": float(x.drop(x.nlargest(5).index).mean()),
             "par_annee": {str(y): round(float(v["net_r"].mean()), 3) for y, v in g.groupby(g["day"].dt.year)},
             "risque_median": float(g["risque"].median()), "cout_median_r": float(g["cost_r"].median())}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {inst:9} {strat:11} n{r['net']['trades']:>5} Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} "
              f"PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} "
              f"sansTop5{r['sans_top5']:+.3f} {r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€ "
              f"coût{r['cout_median_r']:.3f}R ans{r['par_annee']}")
    with open(os.path.join(out, f"summary_{'_'.join(insts)}.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
