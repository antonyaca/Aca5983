"""Lot 6 — edges hors Nasdaq. Règles et critère fixés avant le test.

Marchés et séances : XAUUSD et EURUSD 08:00-16:30 Londres ; SP500 09:30-16:00 New York ; DAX et CAC40 09:00-17:30 Paris.

1. Turtle Soup intraday (Linda Raschke) : une bougie M15 dépasse le plus haut (bas) de la séance précédente puis clôture
   en dessous (au-dessus) → vente (achat) à la clôture de cette bougie. Stop = extrême du jour atteint jusque-là.
   Sorties : RR 1, RR 2, clôture de séance. 1er signal du jour seulement, entrées jusqu'à 1 h 30 avant la clôture.
   Critère habituel : E nette > 0 en IS et OOS, PF ≥ 1,10, OOS > 0 avec frais doublés.
2. Heure de la journée (test aveugle) : sur 2020-2023 uniquement, on mesure pour chaque créneau de 30 min de la séance
   le mouvement moyen (en ATR) et on retient le créneau au |t| le plus élevé avec son sens. Ce créneau est ensuite tradé
   tel quel sur 2024-2026 : entrée au début, sortie à la fin. R = 0,25 ATR 14 jours. Critère : sur 2024-2026 seulement,
   E nette > 0, PF ≥ 1,10, E > 0 avec frais doublés.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, COST, IS_END, st  # noqa: E402

COST = dict(COST, EURUSD=0.00015, CAC40=1.5)
SESS = {"XAUUSD": ("Europe/London", 480, 990), "EURUSD": ("Europe/London", 480, 990),
        "SP500": ("America/New_York", 570, 960), "DAX": ("Europe/Paris", 540, 1050), "CAC40": ("Europe/Paris", 540, 1050)}


def sessions(inst):
    tz, a, b = SESS[inst]
    df = load_m1(inst, tz)
    df = df[(df["hm"] >= a) & (df["hm"] < b)]
    out = {}
    for d, g in df.groupby("day"):
        if d.dayofweek < 5 and len(g) > 0.9 * (b - a) and g["hm"].iloc[0] == a:
            out[d] = g.set_index(g["hm"] - a).reindex(range(b - a)).ffill()
    keys = sorted(out)
    H = np.array([out[k]["high"].max() for k in keys]); L = np.array([out[k]["low"].min() for k in keys])
    C = np.array([out[k]["close"].iloc[-1] for k in keys]); prev = np.r_[np.nan, C[:-1]]
    tr = np.nanmax(np.vstack([H - L, abs(H - prev), abs(L - prev)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    return out, keys, H, L, atr, b - a


def turtle(inst, days, keys, PH, PL, n):
    rows = []
    for i in range(1, len(keys)):
        g = days[keys[i]]
        h, l, o, c = g["high"].values, g["low"].values, g["open"].values, g["close"].values
        ph, pl = PH[i - 1], PL[i - 1]
        for e in range(14, n - 90, 15):                      # clôture de chaque bougie M15
            hh, ll = h[e - 14:e + 1].max(), l[e - 14:e + 1].min()
            d = 0
            if hh > ph and c[e] < ph:
                d, stop = -1, h[:e + 1].max()
            elif ll < pl and c[e] > pl:
                d, stop = 1, l[:e + 1].min()
            if d == 0:
                continue
            entry = c[e]
            risk = (entry - stop) * d
            if risk <= 0:
                break
            for rr in (1, 2, None):
                tp = None if rr is None else entry + d * rr * risk
                px = c[-1]
                for j in range(e + 1, n):
                    if (l[j] <= stop) if d == 1 else (h[j] >= stop):
                        px = o[j] if ((o[j] < stop) if d == 1 else (o[j] > stop)) else stop
                        break
                    if tp is not None and ((h[j] >= tp) if d == 1 else (l[j] <= tp)):
                        px = o[j] if ((o[j] > tp) if d == 1 else (o[j] < tp)) else tp
                        break
                rows.append((inst, "Turtle Soup", f"Turtle Soup · {'clôture' if rr is None else f'RR 1:{rr}'}",
                             keys[i], d, entry, px, risk))
            break
    return rows


def seasonality(inst, days, keys, atr, n):
    tz, a, _ = SESS[inst]
    slots = list(range(0, n - 29, 30))
    rec = []
    for i, k in enumerate(keys):
        if np.isnan(atr[i]):
            continue
        g = days[k]
        o, c = g["open"].values, g["close"].values
        for s in slots:
            rec.append((k, s, o[s], c[s + 29], atr[i]))
    x = pd.DataFrame(rec, columns=["day", "slot", "o", "c", "atr"])
    x["mv"] = (x["c"] - x["o"]) / x["atr"]
    ins = x[x["day"] < IS_END]
    tstat = ins.groupby("slot")["mv"].agg(lambda v: v.mean() / v.std() * np.sqrt(len(v)))
    best = tstat.abs().idxmax()
    d = 1 if tstat[best] > 0 else -1
    hh, mm = divmod(a + best, 60)
    label = f"Créneau {hh:02d}:{mm:02d}-{(a + best + 30) // 60:02d}:{(a + best + 30) % 60:02d} ({tz.split('/')[1]}) · {'achat' if d == 1 else 'vente'}"
    t = x[x["slot"] == best]
    rows = [(inst, "Heure de la journée", label, r.day, d, r.o, r.c, 0.25 * r.atr) for r in t.itertuples()]
    return rows, {"creneau": label, "t_is": float(tstat[best]), "t_tous": {int(s): round(float(v), 2) for s, v in tstat.items()}}


def main():
    rows, seas = [], {}
    for inst in SESS:
        days, keys, H, L, atr, n = sessions(inst)
        rows += turtle(inst, days, keys, H, L, n)
        r, info = seasonality(inst, days, keys, atr, n)
        rows += r
        seas[inst] = info
        print(inst, "créneau retenu sur 2020-2023 :", info["creneau"], f"t = {info['t_is']:+.2f}")
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
        seasonal = g["strategie"].iloc[0] == "Heure de la journée"
        base = oos if seasonal else g
        r = {"instrument": inst, "reglage": reg, "strategie": g["strategie"].iloc[0], "brut": st(base["gross_r"].values),
             "net": st(base["net_r"].values), "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values),
             "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(base["net_r"].mean() / base["net_r"].std() * np.sqrt(len(base)))}
        if seasonal:
            r["valide"] = bool(r["oos"]["e_r"] > 0 and (r["oos"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        else:
            r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        tag = "OOS seul" if seasonal else "2020-26"
        print(f"{'✔' if r['valide'] else ' '} {inst:7} {reg:52} [{tag}] n{r['net']['trades']:>5} WR{r['net']['win_rate']:5.1f} "
              f"Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} "
              f"x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} {r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump({"resultats": res, "saisonnalite": seas}, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
