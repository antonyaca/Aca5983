"""Deux stratégies intraday sur indices US (heure de New York, heure d'été gérée).

1. Momentum intraday (d'après Gao, Han, Li & Zhou, 2018) :
   sens = signe du mouvement entre la clôture de la veille (16:00) et 10:00.
   Entrée à 15:30 dans ce sens, sortie à 16:00. Stop de protection = k × ATR14 journalier (k = 0,25 / 0,5 / 1).
2. Opening Range Breakout (ORB) :
   range des N premières minutes après 09:30 (N = 15 ou 30). Entrée au premier franchissement
   (ordre stop sur le bord du range), stop au bord opposé. Sortie à RR 1, RR 2 ou à 16:00 (« clôture »).
   Un trade max par jour, entrées jusqu'à 15:00. Si les deux bords sont franchis dans la même minute : pas de trade.

Capital 10 000 €, 100 € risqués par trade (1 R = 100 €), sans composition.
Usage : python3 backtest.py [SP500 NASDAQ100 ...]
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))

COSTS = {  # aller-retour : spread + slippage + commission, en points
    "SP500": 0.50 + 0.25,
    "NASDAQ100": 1.00 + 0.50,
}
IS_END = pd.Timestamp("2024-01-01")
CAPITAL_EUR, RISK_EUR = 10_000, 100
NY = "America/New_York"
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def load(inst):
    files = sorted(glob.glob(os.path.join(ROOT, "data", inst, f"{inst}_M1_*.csv.gz")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates("time").sort_values("time")
    df = df[df["time"] >= "2020-01-01"].reset_index(drop=True)
    ny = df["time"].dt.tz_convert(NY)
    df["day"] = ny.dt.date
    df["hm"] = ny.dt.hour * 60 + ny.dt.minute          # minutes depuis minuit, heure de New York
    return df


def rth_days(df):
    """Séances 09:30-16:00 complètes (au moins 360 minutes sur 390)."""
    rth = df[(df["hm"] >= 570) & (df["hm"] < 960)]
    out = {}
    for day, g in rth.groupby("day"):
        if len(g) >= 360 and pd.Timestamp(day).dayofweek < 5:
            out[day] = g
    return out


def daily_atr(days):
    keys = sorted(days)
    hi = np.array([days[k]["high"].max() for k in keys])
    lo = np.array([days[k]["low"].min() for k in keys])
    cl = np.array([days[k]["close"].iloc[-1] for k in keys])
    prev = np.concatenate([[np.nan], cl[:-1]])
    tr = np.nanmax(np.vstack([hi - lo, np.abs(hi - prev), np.abs(lo - prev)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values   # uniquement les jours précédents
    return dict(zip(keys, atr)), dict(zip(keys, cl))


def walk(g, start_hm, direction, entry, stop, tp, end_hm=959, conservative_first=True):
    """Parcourt les minutes [start_hm, end_hm]. Renvoie (prix de sortie, motif, heure)."""
    bars = g[(g["hm"] >= start_hm) & (g["hm"] <= end_hm)]
    for i, (o, h, l, c, hm) in enumerate(bars[["open", "high", "low", "close", "hm"]].itertuples(index=False)):
        hit_sl = l <= stop if direction == 1 else h >= stop
        hit_tp = tp is not None and (h >= tp if direction == 1 else l <= tp)
        if hit_sl:
            gap = (o < stop) if direction == 1 else (o > stop)
            return (o if gap and i > 0 else stop), "SL", hm
        if hit_tp:
            gap = (o > tp) if direction == 1 else (o < tp)
            return (o if gap and i > 0 else tp), "TP", hm
    last = bars.iloc[-1]
    return last["close"], "Clôture", int(last["hm"])


def momentum(inst, days, atr, close):
    keys = sorted(days)
    rows = []
    for prev_day, day in zip(keys[:-1], keys[1:]):
        g = days[day]
        a = atr.get(day)
        if a is None or np.isnan(a):
            continue
        b10 = g[g["hm"] == 599]           # bougie 09:59 -> prix de 10:00
        b1530 = g[g["hm"] == 930]
        if b10.empty or b1530.empty:
            continue
        r1 = b10["close"].iloc[0] - close[prev_day]
        if r1 == 0:
            continue
        d = 1 if r1 > 0 else -1
        entry = b1530["open"].iloc[0]
        for k in (0.25, 0.5, 1.0):
            risk = k * a
            px, why, _ = walk(g, 930, d, entry, entry - d * risk, None)
            rows.append({"strategie": "Momentum", "reglage": f"Momentum · stop {str(k).replace('.', ',')} ATR",
                         "day": day, "direction": "BUY" if d == 1 else "SELL", "entry": entry, "exit": px,
                         "motif": why, "risque": risk, "gross_r": (px - entry) * d / risk})
    return rows


def orb(inst, days):
    rows = []
    for day in sorted(days):
        g = days[day]
        for n in (15, 30):
            rng = g[(g["hm"] >= 570) & (g["hm"] < 570 + n)]
            if len(rng) < n - 2:
                continue
            rh, rl = rng["high"].max(), rng["low"].min()
            after = g[(g["hm"] >= 570 + n) & (g["hm"] <= 900)]   # entrées jusqu'à 15:00
            up = after["high"] > rh
            dn = after["low"] < rl
            hit = up | dn
            if not hit.any():
                continue
            j = hit.values.argmax()
            if up.values[j] and dn.values[j]:
                continue
            bar = after.iloc[j]
            d = 1 if up.values[j] else -1
            lvl = rh if d == 1 else rl
            entry = max(bar["open"], lvl) if d == 1 else min(bar["open"], lvl)
            stop = rl if d == 1 else rh
            risk = (entry - stop) * d
            if risk <= 0:
                continue
            for rr in (1.0, 2.0, None):
                tp = None if rr is None else entry + d * rr * risk
                # minute d'entrée : on ne compte que le stop (prudent), puis minutes suivantes
                l_, h_ = bar["low"], bar["high"]
                if (d == 1 and l_ <= stop) or (d == -1 and h_ >= stop):
                    px, why = stop, "SL"
                else:
                    px, why, _ = walk(g, int(bar["hm"]) + 1, d, entry, stop, tp)
                label = "clôture" if rr is None else f"RR {int(rr)}"
                rows.append({"strategie": "ORB", "reglage": f"ORB {n} min · sortie {label}",
                             "day": day, "direction": "BUY" if d == 1 else "SELL", "entry": entry, "exit": px,
                             "motif": why, "risque": risk, "gross_r": (px - entry) * d / risk})
    return rows


def stats(t, col):
    if len(t) == 0:
        return None
    r = t[col].values
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    cum = np.cumsum(r)
    peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
    dd = float((peak - cum).max())
    streak = best = 0
    for x in r:
        streak = streak + 1 if x < 0 else 0
        best = max(best, streak)
    return {"trades": int(len(r)), "win_rate": float((r > 0).mean() * 100),
            "profit_factor": float(pos / neg) if neg > 0 else None, "esperance_r": float(r.mean()),
            "total_r": float(r.sum()), "max_dd_r": dd, "pire_serie": int(best),
            "resultat_eur": float(r.sum() * RISK_EUR), "max_dd_eur": dd * RISK_EUR,
            "max_dd_pct_capital": dd * RISK_EUR / CAPITAL_EUR * 100}


def main(inst):
    out = os.path.join(HERE, "results", inst)
    os.makedirs(out, exist_ok=True)
    df = load(inst)
    days = rth_days(df)
    atr, close = daily_atr(days)
    trades = pd.DataFrame(momentum(inst, days, atr, close) + orb(inst, days))
    trades["day"] = pd.to_datetime(trades["day"])
    trades["net_r"] = trades["gross_r"] - COSTS[inst] / trades["risque"]
    trades = trades.sort_values(["reglage", "day"])
    trades.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")

    summary = {"instrument": inst, "cout_points": COSTS[inst], "capital_eur": CAPITAL_EUR, "risque_eur": RISK_EUR,
               "periode": [str(trades["day"].min().date()), str(trades["day"].max().date())],
               "jours_rth": len(days), "combinaisons": []}
    for reg, t in trades.groupby("reglage", sort=False):
        c = {"strategie": t["strategie"].iloc[0], "reglage": reg,
             "risque_median_points": float(t["risque"].median())}
        for col, lab in (("gross_r", "brut"), ("net_r", "net")):
            c[lab] = {
                "total": stats(t, col),
                "in_sample": stats(t[t["day"] < IS_END], col),
                "out_of_sample": stats(t[t["day"] >= IS_END], col),
                "par_annee": {str(y): stats(g, col) for y, g in t.groupby(t["day"].dt.year)},
                "par_direction": {k: stats(g, col) for k, g in t.groupby("direction")},
                "par_jour": {JOURS[k]: stats(g, col) for k, g in t.groupby(t["day"].dt.dayofweek)},
            }
        c["equity"] = {"dates": t["day"].dt.strftime("%Y-%m-%d").tolist(),
                       "brut": np.round(np.cumsum(t["gross_r"].values), 2).tolist(),
                       "net": np.round(np.cumsum(t["net_r"].values), 2).tolist()}
        summary["combinaisons"].append(c)
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(summary, f, ensure_ascii=False)
    print(inst, len(days), "séances,", len(trades), "trades")


if __name__ == "__main__":
    for name in (sys.argv[1:] or list(COSTS)):
        main(name.upper())
