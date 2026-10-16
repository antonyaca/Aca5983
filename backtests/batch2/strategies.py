"""Lot 2 de stratégies intraday — règles et critère fixés avant les tests.

Critère de validation (fixé à l'avance) : espérance nette > 0 en in-sample (2020-2023) ET en out-of-sample (2024+),
profit factor net global ≥ 1,10, et espérance nette OOS encore > 0 avec frais doublés.

1. Range asiatique (XAUUSD, EURUSD) — heure de Londres : range 00:00-07:00, entrée au 1er franchissement entre 07:00 et 12:00,
   stop au bord opposé, sortie RR 1 / RR 2 / 16:30 Londres.
2. ORB Londres 30 min (XAUUSD, EURUSD) — range 08:00-08:30 Londres, entrée jusqu'à 12:00, stop au bord opposé,
   sortie RR 1 / RR 2 / 16:30 Londres.
3. Gap fade (SP500, NASDAQ100) — heure de New York : gap = ouverture 09:30 − clôture veille (16:00).
   Si |gap| ≥ k × ATR14 (k = 0,25 ou 0,5) : position contre le gap à l'ouverture, objectif = clôture de la veille,
   stop = entrée ± |gap| ; sortie 16:00 sinon.
Capital 10 000 €, 100 € par trade (1 R).
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
COST = {"XAUUSD": 0.47, "EURUSD": 0.00015, "SP500": 0.75, "NASDAQ100": 1.5}
IS_END = pd.Timestamp("2024-01-01")
RISK_EUR, CAPITAL = 100, 10_000


def load(inst, tz):
    files = sorted(glob.glob(os.path.join(ROOT, "data", inst, f"{inst}_M1_*.csv.gz")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates("time").sort_values("time")
    df = df[df["time"] >= "2020-01-01"].reset_index(drop=True)
    loc = df["time"].dt.tz_convert(tz)
    df["day"] = loc.dt.date
    df["hm"] = loc.dt.hour * 60 + loc.dt.minute
    return {d: g for d, g in df.groupby("day") if pd.Timestamp(d).dayofweek < 5}


def walk(bars, d, entry, stop, tp):
    """bars : minutes après l'entrée. SL prioritaire. Sortie à la clôture de la dernière minute sinon."""
    for i, (o, h, l) in enumerate(bars[["open", "high", "low"]].itertuples(index=False)):
        if (l <= stop) if d == 1 else (h >= stop):
            return (o if (i > 0 and ((o < stop) if d == 1 else (o > stop))) else stop), "SL"
        if tp is not None and ((h >= tp) if d == 1 else (l <= tp)):
            return (o if (i > 0 and ((o > tp) if d == 1 else (o < tp))) else tp), "TP"
    return (bars["close"].iloc[-1], "Clôture") if len(bars) else (None, None)


def breakout(days, name, r0, r1, e_end, x_end, min_range_bars):
    rows = []
    for day, g in days.items():
        rng = g[(g["hm"] >= r0) & (g["hm"] < r1)]
        if len(rng) < min_range_bars:
            continue
        rh, rl = rng["high"].max(), rng["low"].min()
        after = g[(g["hm"] >= r1) & (g["hm"] < e_end)]
        up, dn = after["high"] > rh, after["low"] < rl
        hit = (up | dn).values
        if not hit.any():
            continue
        j = hit.argmax()
        if up.values[j] and dn.values[j]:
            continue
        bar = after.iloc[j]
        d = 1 if up.values[j] else -1
        entry = max(bar["open"], rh) if d == 1 else min(bar["open"], rl)
        stop = rl if d == 1 else rh
        risk = (entry - stop) * d
        if risk <= 0:
            continue
        rest = g[(g["hm"] > bar["hm"]) & (g["hm"] < x_end)]
        for rr in (1, 2, None):
            tp = None if rr is None else entry + d * rr * risk
            if (d == 1 and bar["low"] <= stop) or (d == -1 and bar["high"] >= stop):
                px, why = stop, "SL"
            else:
                px, why = walk(rest, d, entry, stop, tp)
                if px is None:
                    continue
            rows.append({"strategie": name, "reglage": f"{name} · sortie {'clôture' if rr is None else f'RR {rr}'}",
                         "day": day, "direction": "BUY" if d == 1 else "SELL", "risque": risk,
                         "entry_hm": int(bar["hm"]), "range": rh - rl,
                         "gross_r": (px - entry) * d / risk, "motif": why})
    return rows


def gap_fade(days):
    keys = sorted(d for d, g in days.items() if (g["hm"] == 570).any() and (g["hm"] == 959).any())
    rth = {k: days[k][(days[k]["hm"] >= 570) & (days[k]["hm"] < 960)] for k in keys}
    hi = np.array([rth[k]["high"].max() for k in keys]); lo = np.array([rth[k]["low"].min() for k in keys])
    cl = np.array([rth[k]["close"].iloc[-1] for k in keys])
    prev = np.r_[np.nan, cl[:-1]]
    tr = np.nanmax(np.vstack([hi - lo, abs(hi - prev), abs(lo - prev)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    rows = []
    for i in range(1, len(keys)):
        if np.isnan(atr[i]):
            continue
        g = rth[keys[i]]
        o = g["open"].iloc[0]
        gap = o - cl[i - 1]
        for k in (0.25, 0.5):
            if abs(gap) < k * atr[i]:
                continue
            d = -1 if gap > 0 else 1
            risk = abs(gap)
            px, why = walk(g, d, o, o - d * risk, cl[i - 1])
            rows.append({"strategie": "Gap fade", "reglage": f"Gap fade · gap ≥ {str(k).replace('.', ',')} ATR",
                         "day": keys[i], "direction": "BUY" if d == 1 else "SELL", "risque": risk,
                         "entry_hm": 570, "range": abs(gap),
                         "gross_r": (px - o) * d / risk, "motif": why})
    return rows


def st(r):
    if len(r) == 0:
        return None
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    cum = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max())
    s = b = 0
    for x in r:
        s = s + 1 if x < 0 else 0
        b = max(b, s)
    return {"trades": int(len(r)), "win_rate": float((r > 0).mean() * 100), "pf": float(pos / neg) if neg else None,
            "e_r": float(r.mean()), "resultat_eur": float(r.sum() * RISK_EUR), "max_dd_eur": dd * RISK_EUR, "pire_serie": b}


def run(inst):
    rows = []
    if inst in ("XAUUSD", "EURUSD"):
        days = load(inst, "Europe/London")
        rows += breakout(days, "Range asiatique", 0, 420, 720, 990, 300)
        rows += breakout(days, "ORB Londres 30 min", 480, 510, 720, 990, 25)
    else:
        rows += gap_fade(load(inst, "America/New_York"))
    t = pd.DataFrame(rows)
    t["day"] = pd.to_datetime(t["day"])
    t["net_r"] = t["gross_r"] - COST[inst] / t["risque"]
    t["net2_r"] = t["gross_r"] - 2 * COST[inst] / t["risque"]
    t["instrument"] = inst
    return t


def main(insts):
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    all_t = pd.concat([run(i) for i in insts], ignore_index=True).sort_values(["instrument", "reglage", "day"])
    all_t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (inst, reg), t in all_t.groupby(["instrument", "reglage"], sort=False):
        is_, oos = t[t["day"] < IS_END], t[t["day"] >= IS_END]
        r = {"instrument": inst, "reglage": reg, "strategie": t["strategie"].iloc[0],
             "brut": st(t["gross_r"].values), "net": st(t["net_r"].values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values),
             "oos_cout_x2_e_r": float(oos["net2_r"].mean()),
             "par_annee": {str(y): float(g["net_r"].mean()) for y, g in t.groupby(t["day"].dt.year)},
             "risque_median": float(t["risque"].median())}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10 and r["oos_cout_x2_e_r"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {inst:9} {reg:36} n{r['net']['trades']:>5} Eb{r['brut']['e_r']:+.3f} | En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} "
              f"IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_cout_x2_e_r']:+.3f} | {r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€ stop{r['risque_median']:.4g}")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:] or ["XAUUSD", "EURUSD", "SP500", "NASDAQ100"])
