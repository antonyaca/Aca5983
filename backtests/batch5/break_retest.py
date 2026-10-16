"""Cassure + retest (« break and retest »). Règles et critère fixés avant le test.

Niveaux :
  - « Range 30 min » : haut / bas des 30 premières minutes de séance.
  - « Veille » : plus haut / plus bas de la séance précédente.
Cassure : 1re clôture M5 au-delà d'un des niveaux (après la fin du range ; dès l'ouverture pour « Veille »).
Retest : le prix revient toucher le niveau → entrée limite au niveau (au cours d'ouverture de la minute si gap favorable).
Stop : « Range 30 min » → milieu du range ; « Veille » → niveau ∓ 0,25 ATR 14 jours.
Sortie : RR 1, RR 2, ou clôture de séance. Entrées admises jusqu'à 1 h 30 avant la clôture. Un trade max par jour et par niveau.
Minute d'entrée : si le stop est aussi touché dans cette minute → perte (prudent).
Séances : Nasdaq / S&P 500 09:30-16:00 New York ; DAX 09:00-17:30 Paris ; or 08:00-16:30 Londres.
Critère : E nette > 0 en IS et OOS, PF ≥ 1,10, OOS > 0 avec frais doublés. 100 € par R.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, COST, IS_END, st  # noqa: E402

SESS = {"NASDAQ100": ("America/New_York", 570, 960), "SP500": ("America/New_York", 570, 960),
        "DAX": ("Europe/Paris", 540, 1050), "XAUUSD": ("Europe/London", 480, 990)}


def run(inst):
    tz, a, b = SESS[inst]
    df = load_m1(inst, tz)
    df = df[(df["hm"] >= a) & (df["hm"] < b)]
    days = {d: g.reset_index(drop=True) for d, g in df.groupby("day") if d.dayofweek < 5 and len(g) > 0.9 * (b - a)}
    keys = sorted(days)
    hi = np.array([days[k]["high"].max() for k in keys]); lo = np.array([days[k]["low"].min() for k in keys])
    cl = np.array([days[k]["close"].iloc[-1] for k in keys])
    prev = np.r_[np.nan, cl[:-1]]
    tr = np.nanmax(np.vstack([hi - lo, abs(hi - prev), abs(lo - prev)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    rows = []
    cutoff = b - 90
    for i in range(1, len(keys)):
        g = days[keys[i]]
        hm = g["hm"].values; H = g["high"].values; L = g["low"].values; O = g["open"].values; C = g["close"].values
        setups = []
        rng = (hm >= a) & (hm < a + 30)
        if rng.sum() >= 27:
            rh, rl = H[rng].max(), L[rng].min()
            setups.append(("Range 30 min", rh, rl, a + 30, (rh + rl) / 2, (rh + rl) / 2))
        if not np.isnan(atr[i]):
            setups.append(("Veille", hi[i - 1], lo[i - 1], a, hi[i - 1] - 0.25 * atr[i], lo[i - 1] + 0.25 * atr[i]))
        for name, up_l, dn_l, start, stop_long, stop_short in setups:
            # clôtures M5 (minutes dont hm % 5 == 4), à partir de start
            d = 0
            for j in np.where((hm >= start) & (hm < cutoff) & ((hm - a) % 5 == 4))[0]:
                if C[j] > up_l:
                    d, lvl, stop, jb = 1, up_l, stop_long, j
                    break
                if C[j] < dn_l:
                    d, lvl, stop, jb = -1, dn_l, stop_short, j
                    break
            if d == 0 or (lvl - stop) * d <= 0:
                continue
            # retest
            k = None
            for j in range(jb + 1, len(hm)):
                if hm[j] >= cutoff:
                    break
                if (L[j] <= lvl) if d == 1 else (H[j] >= lvl):
                    k = j
                    break
            if k is None:
                continue
            entry = min(O[k], lvl) if d == 1 else max(O[k], lvl)
            risk = (entry - stop) * d
            if risk <= 0:
                continue
            for rr in (1, 2, None):
                tp = None if rr is None else entry + d * rr * risk
                if (L[k] <= stop) if d == 1 else (H[k] >= stop):
                    px = stop
                else:
                    px = C[-1]
                    for j in range(k + 1, len(hm)):
                        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                            px = O[j] if ((O[j] < stop) if d == 1 else (O[j] > stop)) else stop
                            break
                        if tp is not None and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
                            px = O[j] if ((O[j] > tp) if d == 1 else (O[j] < tp)) else tp
                            break
                sortie = "clôture" if rr is None else f"RR 1:{rr}"
                for sens in ("deux sens", "achats seuls"):
                    if sens == "achats seuls" and d == -1:
                        continue
                    rows.append((inst, f"Retest {name} · {sortie} · {sens}", keys[i], d, entry, px, risk))
    return rows


def main():
    rows = []
    for inst in SESS:
        rows += run(inst)
    t = pd.DataFrame(rows, columns=["instrument", "reglage", "day", "d", "entry", "exit", "risque"])
    t = t[t["day"] >= "2020-01-01"]
    t["gross_r"] = (t["exit"] - t["entry"]) * t["d"] / t["risque"]
    t["cost_r"] = t["instrument"].map(COST) / t["risque"]
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (inst, reg), g in t.groupby(["instrument", "reglage"]):
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        r = {"instrument": inst, "reglage": reg, "brut": st(g["gross_r"].values), "net": st(x.values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x)))}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {inst:10} {reg:52} n{r['net']['trades']:>5} WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} "
              f"En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} "
              f"t{r['t_stat']:+.2f} {r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
