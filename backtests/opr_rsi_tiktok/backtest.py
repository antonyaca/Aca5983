"""Réplique de l'EA TikTok « OPR_SIMPLE + RSI » sur XAUUSD M5 (23/10/2026).

Règles (reconstituées d'après les captures MT5, fixées avant le test) :
- Heure serveur Fusion Markets = heure de New York + 7 h (GMT+2 hiver / GMT+3 été).
- Range (OPR) : bougies M5 de H:ms à H:me incluses (H = 7 h serveur). Haut / bas du range.
- Cassure : première clôture M5 après le range au-dessus du haut (achat) ou sous le bas (vente),
  avec RSI(période) de cette bougie dans [RSI_min, RSI_max] (mode A) ;
  mode B : achat si RSI <= max, vente si RSI >= min. Une seule position par jour.
- Entrée à la clôture de la bougie de cassure. SL = autre borne du range (buffer 0). TP = RR x risque (RR 2).
- Sortie résolue en M1 (SL prioritaire si SL et TP dans la même minute) ; clôture forcée à 23h55 serveur.
- Lundi-vendredi. Risque fixe 100 $ par trade (1 % de 10 000, sans composition).
- Frais : 0 $ (comme la vidéo, « exécution idéale ») puis 0,10 $/oz (≈ Fusion Zero) et 0,47 $/oz (hypothèse du repo).
Données : HistData M1 bid, UTC.
"""
import sys, json, itertools
import numpy as np, pandas as pd
from numba import njit

ROOT = "data/XAUUSD/XAUUSD_M1_{}.csv.gz"
YEARS = range(2020, 2027)


def load():
    df = pd.concat([pd.read_csv(ROOT.format(y)) for y in YEARS])
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates("time").set_index("time").sort_index()
    ny = df.index.tz_convert("America/New_York").tz_localize(None)
    df.index = ny + pd.Timedelta(hours=7)  # heure serveur
    return df


def rsi(close, n):
    d = np.diff(close, prepend=close[0])
    up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    au = pd.Series(up).ewm(alpha=1 / n, adjust=False).mean().values
    ad = pd.Series(dn).ewm(alpha=1 / n, adjust=False).mean().values
    rs = au / np.where(ad == 0, 1e-12, ad)
    return 100 - 100 / (1 + rs)


@njit(cache=True)
def simulate(day5, mod5, c5, h5, l5, m1end5, rsi5, h1, l1, c1, day1, mod1,
             H, ms, me, rmin, rmax, mode, rr, d0, d1):
    out = np.zeros((4000, 4))  # day, dir, R brut, risque $
    k = 0
    n = len(c5)
    i = 0
    while i < n:
        d = day5[i]
        j = i
        while j < n and day5[j] == d:
            j += 1
        if d >= d0 and d <= d1:
            hi = -1e18; lo = 1e18; cnt = 0
            for b in range(i, j):
                if mod5[b] >= H * 60 + ms and mod5[b] <= H * 60 + me:
                    if h5[b] > hi: hi = h5[b]
                    if l5[b] < lo: lo = l5[b]
                    cnt += 1
            if cnt == (me - ms) // 5 + 1 and hi > lo:
                for b in range(i, j):
                    if mod5[b] <= H * 60 + me or mod5[b] >= 23 * 60 + 55:
                        continue
                    r = rsi5[b]
                    dr = 0
                    if c5[b] > hi:
                        if (mode == 0 and r >= rmin and r <= rmax) or (mode == 1 and r <= rmax):
                            dr = 1
                    elif c5[b] < lo:
                        if (mode == 0 and r >= rmin and r <= rmax) or (mode == 1 and r >= rmin):
                            dr = -1
                    if dr == 0:
                        continue
                    e = c5[b]
                    sl = lo if dr == 1 else hi
                    risk = abs(e - sl)
                    if risk <= 0:
                        break
                    tp = e + dr * rr * risk
                    res = 0.0
                    m = m1end5[b]
                    done = False
                    while m < len(c1) and day1[m] == d:
                        if dr == 1:
                            if l1[m] <= sl: res = -1.0; done = True
                            elif h1[m] >= tp: res = rr; done = True
                        else:
                            if h1[m] >= sl: res = -1.0; done = True
                            elif l1[m] <= tp: res = rr; done = True
                        if done: break
                        if mod1[m] >= 23 * 60 + 55:
                            res = dr * (c1[m] - e) / risk; done = True; break
                        m += 1
                    if not done:
                        m = min(m, len(c1) - 1)
                        res = dr * (c1[m - 1] - e) / risk
                    out[k, 0] = d; out[k, 1] = dr; out[k, 2] = res; out[k, 3] = risk
                    k += 1
                    break
        i = j
    return out[:k]


def stats(tr, cost):
    if len(tr) == 0:
        return dict(n=0, pnl=0, pf=0, wr=0, dd=0)
    rnet = tr[:, 2] - cost / tr[:, 3]
    pnl = 100 * rnet
    eq = np.cumsum(pnl)
    dd = np.max(np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq)
    g, l_ = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    return dict(n=len(tr), pnl=round(pnl.sum(), 0), pf=round(g / l_ if l_ else 99, 2),
                wr=round(100 * (pnl > 0).mean(), 1), dd=round(dd, 0),
                med_risk=round(float(np.median(tr[:, 3])), 2))


def main():
    df = load()
    m5 = df.resample("5min").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    m5 = m5[m5.index.dayofweek < 5]
    df = df[df.index.dayofweek < 5]
    epoch = pd.Timestamp("2000-01-01")
    day5 = ((m5.index.normalize() - epoch).days).values.astype(np.int64)
    mod5 = (m5.index.hour * 60 + m5.index.minute).values.astype(np.int64)
    day1 = ((df.index.normalize() - epoch).days).values.astype(np.int64)
    mod1 = (df.index.hour * 60 + df.index.minute).values.astype(np.int64)
    m1end5 = np.searchsorted(df.index.values, (m5.index + pd.Timedelta(minutes=5)).values).astype(np.int64)
    c5, h5, l5 = (m5[x].values for x in ("close", "high", "low"))
    h1, l1, c1 = (df[x].values for x in ("high", "low", "close"))
    rsis = {p: rsi(c5, p) for p in range(7, 22)}
    D = lambda s: (pd.Timestamp(s) - epoch).days

    cache = {}

    def run(p, d0, d1):
        ms, me, per, rmin, rmax, mode = p
        if (d0, d1) not in cache:
            a, b = np.searchsorted(day5, D(d0)), np.searchsorted(day5, D(d1) + 1)
            a1, b1 = np.searchsorted(day1, D(d0)), np.searchsorted(day1, D(d1) + 2)
            cache[(d0, d1)] = (a, b, a1, b1)
        a, b, a1, b1 = cache[(d0, d1)]
        return simulate(day5[a:b], mod5[a:b], c5[a:b], h5[a:b], l5[a:b], m1end5[a:b] - a1, rsis[per][a:b],
                        h1[a1:b1], l1[a1:b1], c1[a1:b1], day1[a1:b1], mod1[a1:b1],
                        7, ms, me, rmin, rmax, mode, 2.0, D(d0), D(d1))

    IS = ("2026-01-02", "2026-10-15")
    grid = [(ms, me, per, rmin, rmax, mode)
            for ms in range(0, 55, 5) for me in range(5, 60, 5) if me > ms
            for per in range(7, 22) for rmin in range(5, 45, 5) for rmax in range(60, 100, 5)
            for mode in (0, 1)]
    rows = []
    for p in grid:
        s = stats(run(p, *IS), 0.0)
        rows.append((*p, s["n"], s["pnl"], s["pf"], s["dd"]))
    g = pd.DataFrame(rows, columns=["ms", "me", "rsi", "rmin", "rmax", "mode", "n", "pnl", "pf", "dd"])
    g.to_csv("backtests/opr_rsi_tiktok/results/grid_2026.csv.gz", index=False)
    res = {"grid_size": len(g), "share_positive_2026": round(float((g.pnl > 0).mean()), 3)}

    tiktok = (20, 55, 8, 10, 60)
    best = tuple(g.sort_values("pnl", ascending=False).iloc[0][["ms", "me", "rsi", "rmin", "rmax", "mode"]].astype(int))
    configs = {"tiktok_modeA": (*tiktok, 0), "tiktok_modeB": (*tiktok, 1), "best_grid": best,
               "sans_rsi": (20, 55, 8, 0, 100, 0)}
    for name, p in configs.items():
        res[name] = {"params": list(map(int, p))}
        for lbl, (a, b) in {"IS_2026": IS, "OOS_2020_2025": ("2020-01-01", "2025-12-31")}.items():
            tr = run(p, a, b)
            res[name][lbl] = {f"cost_{c}": stats(tr, c) for c in (0.0, 0.10, 0.47)}
        tr = run(p, "2020-01-01", "2025-12-31")
        yrs = pd.to_datetime(epoch) + pd.to_timedelta(tr[:, 0], "D")
        res[name]["OOS_par_annee_cost_0.10"] = {
            int(y): stats(tr[yrs.year == y], 0.10)["pnl"] for y in range(2020, 2026)}

    # robustesse : les 50 meilleurs de 2026, que donnent-ils hors échantillon ?
    top = g.sort_values("pnl", ascending=False).head(50)
    oos = [stats(run(tuple(int(v) for v in r[["ms", "me", "rsi", "rmin", "rmax", "mode"]]),
                     "2020-01-01", "2025-12-31"), 0.10)["pnl"] for _, r in top.iterrows()]
    res["top50_2026_OOS_2020_2025_cost_0.10"] = {
        "median": float(np.median(oos)), "min": float(np.min(oos)), "max": float(np.max(oos)),
        "share_positive": float(np.mean(np.array(oos) > 0))}
    json.dump(res, open("backtests/opr_rsi_tiktok/results/summary.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
