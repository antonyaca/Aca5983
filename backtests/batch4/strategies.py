"""Lot 4 — stratégies publiées par des spécialistes. Critère inchangé (fixé avant) :
E nette > 0 en IS et OOS, PF ≥ 1,10, OOS > 0 avec frais doublés. 100 € par R.

1. « Noise area » (Zarattini, Aziz & Barbon, 2024, « Beat the Market », SPY) — séance 09:30-16:00 New York.
   sigma(m) = moyenne sur les 14 séances précédentes de |cours à la minute m / ouverture − 1|.
   Borne haute = max(ouverture, clôture veille) × (1 + sigma(m)) ; borne basse = min(ouverture, clôture veille) × (1 − sigma(m)).
   Toutes les 30 min (10:00 → 15:30) : au-dessus de la borne haute → achat ; sous la borne basse → vente.
   Position en cours coupée au contrôle suivant si le cours repasse sous la borne haute (achat) / au-dessus de la basse (vente).
   Sortie 16:00. Pas de VWAP (pas de volumes dans nos données). R = 0,5 ATR 14 jours.
   Variantes : deux sens / achats seuls.
2. Cassure de volatilité (Larry Williams) — niveaux = ouverture ± k × amplitude de la veille (k = 0,25 ou 0,5).
   Entrée au 1er franchissement, stop = ouverture, sortie à la clôture. Variantes : deux sens / achats seuls.
   Indices US (09:30-16:00 New York) et DAX (09:00-17:30 Paris).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, COST, IS_END, RISK_EUR, st  # noqa: E402

SESS = {"SP500": ("America/New_York", 570, 960), "NASDAQ100": ("America/New_York", 570, 960),
        "DAX": ("Europe/Paris", 540, 1050)}


def sessions(inst):
    tz, a, b = SESS[inst]
    df = load_m1(inst, tz)
    df = df[(df["hm"] >= a) & (df["hm"] < b)]
    out = {}
    n = b - a
    for d, g in df.groupby("day"):
        if d.dayofweek >= 5 or len(g) < n * 0.92 or g["hm"].iloc[0] != a:
            continue
        g = g.set_index(g["hm"] - a).reindex(range(n)).ffill()
        out[d] = g
    return out, n


def noise_area(inst, days, n):
    keys = sorted(days)
    O = np.array([days[k]["open"].iloc[0] for k in keys])
    C = np.array([days[k]["close"].values for k in keys])          # jours × minutes
    H = np.array([days[k]["high"].max() for k in keys]); L = np.array([days[k]["low"].min() for k in keys])
    last = C[:, -1]
    move = np.abs(C / O[:, None] - 1)
    prevc = np.r_[np.nan, last[:-1]]
    tr = np.nanmax(np.vstack([H - L, abs(H - prevc), abs(L - prevc)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    rows = []
    checks = list(range(30, n - 29, 30))                            # 10:00 ... 15:30
    for i in range(15, len(keys)):
        if np.isnan(atr[i]):
            continue
        sigma = move[i - 14:i].mean(axis=0)
        ub = max(O[i], prevc[i]) * (1 + sigma)
        lb = min(O[i], prevc[i]) * (1 - sigma)
        c = C[i]
        R = 0.5 * atr[i]
        for long_only in (False, True):
            reg = "Noise area · " + ("achats seuls" if long_only else "deux sens")
            pos, entry = 0, None
            for m in checks:
                px = c[m - 1]
                if pos == 1 and px < ub[m - 1] or pos == -1 and px > lb[m - 1]:
                    rows.append((inst, "Noise area", reg, keys[i], pos, entry, px, R))
                    pos = 0
                if pos == 0:
                    if px > ub[m - 1]:
                        pos, entry = 1, px
                    elif px < lb[m - 1] and not long_only:
                        pos, entry = -1, px
            if pos:
                rows.append((inst, "Noise area", reg, keys[i], pos, entry, c[-1], R))
    return rows


def williams(inst, days, n):
    keys = sorted(days)
    rows = []
    for a, b in zip(keys[:-1], keys[1:]):
        pr = days[a]["high"].max() - days[a]["low"].min()
        g = days[b]
        o = g["open"].iloc[0]
        for k in (0.25, 0.5):
            up_l, dn_l = o + k * pr, o - k * pr
            up, dn = (g["high"] > up_l).values, (g["low"] < dn_l).values
            hit = up | dn
            if not hit.any():
                continue
            j = hit.argmax()
            if up[j] and dn[j]:
                continue
            d = 1 if up[j] else -1
            bar = g.iloc[j]
            entry = max(bar["open"], up_l) if d == 1 else min(bar["open"], dn_l)
            stop = o
            risk = (entry - stop) * d
            if risk <= 0:
                continue
            rest = g.iloc[j:]
            px = rest["close"].iloc[-1]
            for t, (oo, hh, ll) in enumerate(rest[["open", "high", "low"]].itertuples(index=False)):
                if (ll <= stop) if d == 1 else (hh >= stop):
                    px = oo if t > 0 and ((oo < stop) if d == 1 else (oo > stop)) else stop
                    break
            kk = str(k).replace(".", ",")
            rows.append((inst, "Williams", f"Williams k={kk} · deux sens", b, d, entry, px, risk))
            if d == 1:
                rows.append((inst, "Williams", f"Williams k={kk} · achats seuls", b, d, entry, px, risk))
    return rows


def main():
    rows = []
    for inst in ("NASDAQ100", "SP500", "DAX"):
        days, n = sessions(inst)
        if inst != "DAX":
            rows += noise_area(inst, days, n)
        rows += williams(inst, days, n)
    t = pd.DataFrame(rows, columns=["instrument", "strategie", "reglage", "day", "d", "entry", "exit", "risque"])
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
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))),
             "par_annee": {str(y): round(float(v["net_r"].mean()), 3) for y, v in g.groupby(g["day"].dt.year)}}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {inst:10} {reg:32} n{r['net']['trades']:>5} Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} "
              f"PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} "
              f"{r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
