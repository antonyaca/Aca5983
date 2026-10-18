"""Vérification indépendante de quelques trades (V01, V03, V10, V15) : recalcul « à la main » depuis les minutes brutes,
avec une implémentation différente de run.py (pandas, heures locales via tz_convert, boucle minute par minute).
Seules données reprises de run.py : le calendrier MACRO (dates d'annonce) et les fichiers de trades à contrôler."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from lib import load, COST  # noqa: E402
from run import MACRO  # noqa: E402

EPOCH = pd.Timestamp("1970-01-01")


def bars(inst):
    df = load(inst, "UTC")[["time", "open", "high", "low", "close"]]
    ny = df["time"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    df["tday"] = (ny + pd.Timedelta(hours=7)).dt.normalize()            # journée close 17:00 NY
    df["lon"] = df["time"].dt.tz_convert("Europe/London").dt.tz_localize(None)
    df["nyl"] = ny
    return df


def daily(df):
    g = df.groupby("tday")
    d = pd.DataFrame({"h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last(), "n": g.size()})
    c = d[d["n"] >= 600].copy()
    pc = c["c"].shift(1)
    c["tr"] = pd.concat([c["h"] - c["l"], (c["h"] - pc).abs(), (c["l"] - pc).abs()], axis=1).max(axis=1)
    c["atr"] = c["tr"].rolling(14).mean()
    c["sma"] = c["c"].rolling(20).mean()
    return d, c


def prev_complete(c, D):
    return c[c.index < D].iloc[-1]


def sim(seg, d, E, S, T):
    """seg : minutes de l'entrée jusqu'à la dernière < 16:00 NY. Boucle explicite."""
    rows = list(seg.itertuples())
    r0 = rows[0]
    if (d == 1 and r0.low <= S) or (d == -1 and r0.high >= S):
        return S, r0.time
    for r in rows[1:]:
        stop = (r.low <= S) if d == 1 else (r.high >= S)
        tgt = (r.high >= T) if d == 1 else (r.low <= T)
        if stop:
            gap = (r.open < S) if d == 1 else (r.open > S)
            return (r.open if gap else S), r.time
        if tgt:
            return T, r.time
    return rows[-1].close, rows[-1].time


def window(df, D, col, a, b):
    t0, t1 = D + pd.Timedelta(minutes=a), D + pd.Timedelta(minutes=b)
    return df[(df["tday"] == D) & (df[col] >= t0) & (df[col] < t1)]


def check(inst, var, tr, df, d_all, comp):
    D = tr["day"]
    p = prev_complete(comp, D)
    atr = p["atr"]
    sess_end = D + pd.Timedelta(hours=16)                                 # 16:00 NY
    entry_end = D + pd.Timedelta(hours=12)                                # 12:00 NY
    day = df[df["tday"] == D]
    if var == "V01":
        rg = window(df, D, "lon", 480, 540)
        up, dn = rg["high"].max(), rg["low"].min()
        cand = day[(day["lon"] >= D + pd.Timedelta(minutes=540)) & (day["nyl"] < entry_end)]
        hit = cand[(cand["high"] > up) | (cand["low"] < dn)].iloc[0]
        d = 1 if hit["high"] > up else -1
        E = max(hit["open"], up) if d == 1 else min(hit["open"], dn)
        R = E - dn if d == 1 else up - E
        S, T = E - d * R, E + d * R
        t_in = hit["time"]
    elif var == "V03":
        pre = day[day["lon"] < D + pd.Timedelta(minutes=480)]
        HS, LS = pre["high"].max(), pre["low"].min()
        lv = ([(p["h"], 1)] if HS < p["h"] else []) + ([(p["l"], -1)] if LS > p["l"] else [])
        cand = day[(day["lon"] >= D + pd.Timedelta(minutes=480)) & (day["nyl"] < entry_end)]
        best = None
        for X, pos in lv:
            h = cand[(cand["high"] > X) if pos == 1 else (cand["low"] < X)]
            if len(h) and (best is None or h["time"].iloc[0] < best[0]):
                best = (h["time"].iloc[0], X, pos)
        t_in, X, pos = best
        d, E, R = -pos, X, 0.5 * atr
        S, T = E - d * R, E + d * R
    elif var == "V10":
        d = 1 if p["c"] > p["sma"] else -1
        lab = "08:00 Londres" if tr["kind"] == "H08L" else "08:00 NY"
        col = "lon" if tr["kind"] == "H08L" else "nyl"
        r0 = day[day[col] >= D + pd.Timedelta(hours=8)].iloc[0]
        assert (r0[col] - (D + pd.Timedelta(hours=8))) <= pd.Timedelta(minutes=5), lab
        E, R, t_in = r0["open"], 0.5 * atr, r0["time"]
        S, T = E - d * R, E + d * R
    elif var == "V15":
        wk_start = D - pd.Timedelta(days=D.dayofweek)                     # lundi de la semaine de J
        prev = df[(df["tday"] >= wk_start - pd.Timedelta(days=7)) & (df["tday"] < wk_start)]
        pwh, pwl = prev["high"].max(), prev["low"].min()
        wtd = df[(df["tday"] >= wk_start) & ((df["tday"] < D) | ((df["tday"] == D) & (df["lon"] < D + pd.Timedelta(minutes=480))))]
        wh, wl = wtd["high"].max(), wtd["low"].min()
        lv = ([(pwh, 1)] if wh < pwh else []) + ([(pwl, -1)] if wl > pwl else [])
        cand = day[(day["lon"] >= D + pd.Timedelta(minutes=480)) & (day["nyl"] < entry_end)]
        best = None
        for X, pos in lv:
            h = cand[(cand["high"] > X) if pos == 1 else (cand["low"] < X)]
            if len(h) and (best is None or h["time"].iloc[0] < best[0]):
                best = (h["time"].iloc[0], X, pos)
        t_in, X, pos = best
        d, E, R = -pos, X, 0.5 * atr
        S, T = E - d * R, E + d * R
    seg = day[(day["time"] >= t_in) & (day["nyl"] < sess_end)]
    px, t_out = sim(seg, d, E, S, T)
    mult = 2.0 if int((D - EPOCH).days) in MACRO else 1.0
    g, c = (px - E) * d / R, COST[inst] * mult / R
    exp_in = pd.Timestamp(int(tr["t_in_min"]) * 60, unit="s", tz="UTC")
    exp_out = pd.Timestamp(int(tr["t_out_min"]) * 60, unit="s", tz="UTC")
    ok = (t_in == exp_in and t_out == exp_out and abs(E - tr["entry"]) < 1e-6 * max(1, abs(E))
          and abs(px - tr["exit"]) < 1e-6 * max(1, abs(px)) and abs(g - tr["gross_r"]) < 1e-4 and abs(c - tr["cost_r"]) < 1e-4
          and d == tr["d"])
    print(f"{'OK ' if ok else 'ÉCART'} {var} {inst} {D.date()} sens {d:+d} entrée {t_in.tz_convert('Europe/London'):%H:%M} Londres "
          f"@{E:.5f} stop {S:.5f} obj {T:.5f} | sortie {t_out.tz_convert('America/New_York'):%H:%M} NY @{px:.5f} | "
          f"brut {g:+.3f} R (fichier {tr['gross_r']:+.3f}) coût {c:.3f} R (fichier {tr['cost_r']:.3f}){' annonce x2' if mult > 1 else ''}")
    return ok


def main():
    rng = np.random.default_rng(20261018)
    picks = []
    for var in ("V01", "V03", "V10", "V15"):
        t = pd.read_csv(os.path.join(HERE, "trades", f"{var}.csv.gz"), parse_dates=["day"]).sort_values(["day", "t_in"])
        first = t.groupby(["day", "instrument"]).cumcount() == 0           # 1er candidat du jour sur ce marché
        t = t[t["pris"] & (t["day"] >= "2011-01-01") & (first | (t["kind"] == "H08NY"))]
        idx = list(rng.choice(len(t), 3, replace=False))
        if var == "V03":
            idx.append(int(np.flatnonzero(t["annonce"].values)[0]))       # au moins un jour d'annonce
        picks += [(var, t.iloc[i]) for i in idx]
    res = []
    for inst in sorted({p[1]["instrument"] for p in picks}):
        df = bars(inst)
        d_all, comp = daily(df)
        for var, tr in picks:
            if tr["instrument"] == inst:
                res.append(check(inst, var, tr, df, d_all, comp))
        del df
    print(f"{sum(res)}/{len(res)} trades recalculés à l'identique")


if __name__ == "__main__":
    main()
