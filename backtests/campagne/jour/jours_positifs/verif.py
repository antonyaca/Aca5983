"""Recalcul « à la main » de quelques trades de run.py, avec un code indépendant (pas d'import de run.py).

Choix fixé avant de regarder les chiffres : le DERNIER trade (2011-2026, 1er trade de sa journée) des variantes V04
(Williams 50 % + stop à l'entrée), V07 (RSI2 H1), V09 (gap), V13 (contrôle), V15 (TWAP) et V16 (RSI2 bail-out, swing).
ATR, RSI2 et barres H1 recalculés autrement (pandas : resample, ewm) ; balayage minute par minute explicite.
Imprime les minutes clés et compare gross_r / cost_r à trades.csv.gz.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import lib  # noqa: E402

T = pd.read_csv(os.path.join(HERE, "trades.csv.gz"), parse_dates=["day", "t_in", "t_out"])


def daily(df, end):
    """Barres journalières 09:30-end (séances régulières), ATR14 simple, SMA200, RSI2 (ewm alpha 1/2)."""
    s = df[(df.hm >= 570) & (df.hm < 960)]
    info = s.groupby("day").hm.agg(["size", "min", "max"])
    ok = info[(info["size"] >= 300) & (info["min"] <= 575) & (info["max"] >= 950)].index
    s = s[(s.hm < end) & s.day.isin(ok) & (s.day.dt.dayofweek < 5)]
    b = s.groupby("day").agg(O=("open", "first"), H=("high", "max"), L=("low", "min"), C=("close", "last"))
    tr = np.maximum(b.H - b.L, np.maximum((b.H - b.C.shift()).abs(), (b.L - b.C.shift()).abs()))
    tr.iloc[0] = b.H.iloc[0] - b.L.iloc[0]
    b["atr"] = tr.rolling(14).mean()
    b["sma200"] = b.C.rolling(200).mean()
    ch = b.C.diff()
    up, dn = ch.clip(lower=0).ewm(alpha=0.5, adjust=False).mean(), (-ch).clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    b["rsi2"] = 100 - 100 / (1 + up / dn)
    return b


def day_min(df, D):
    x = df[(df.day == D) & (df.hm >= 570) & (df.hm < 960)].reset_index(drop=True)
    return x


def show(name, D, mine, ref):
    print(f"{name} {D.date()} : recalcul gross_r {mine[0]:+.4f} cost_r {mine[1]:.4f} | trades.csv {ref.gross_r:+.4f} "
          f"{ref.cost_r:.4f} → {'OK' if abs(mine[0] - ref.gross_r) < 1e-4 and abs(mine[1] - ref.cost_r) < 1e-4 else 'ÉCART'}")


def last_trade(v, inst=None):
    """Dernier trade pris qui est le 1er trade de sa journée (pour ce marché)."""
    t = T[(T.variante == v) & (T.day >= "2011-01-01")]
    if inst:
        t = t[t.instrument == inst]
    t = t.sort_values(["day", "t_in"])
    return t[~t.duplicated("day", keep="first")].iloc[-1]


def fmt(x):
    return f"{int(x.hm) // 60:02d}:{int(x.hm) % 60:02d} O{x.open:.2f} H{x.high:.2f} L{x.low:.2f} C{x.close:.2f}"


for inst in ("NASDAQ100", "SP500"):
    df = lib.load(inst)
    bf, b55 = daily(df, 960), daily(df, 956)
    cost = lib.COST[inst]

    if inst == "NASDAQ100":
        # ---- V04 : Williams, 50 % à 0,5 R puis stop à l'entrée
        r = last_trade("V04")
        D = r.day
        x = day_min(df, D)
        prev = [d for d in sorted(df.day.unique()) if d < np.datetime64(D)]
        for pd_ in reversed(prev):                          # dernière séance complète
            y = day_min(df, pd.Timestamp(pd_))
            if len(y) >= 351 and y.hm.iloc[0] == 570:
                break
        rng = y.high.max() - y.low.min()
        o0 = x.open.iloc[0]
        up, dn = o0 + 0.5 * rng, o0 - 0.5 * rng
        k = int(np.argmax((x.high >= up) | (x.low <= dn)))
        d = 1 if x.high[k] >= up else -1
        entry = max(x.open[k], up) if d == 1 else min(x.open[k], dn)
        R = (entry - o0) * d
        tp, st, half, res = entry + d * 0.5 * R, o0, None, None
        for j in range(k, len(x)):
            if (x.low[j] <= st) if d == 1 else (x.high[j] >= st):
                px = st if j == k else (min(x.open[j], st) if d == 1 else max(x.open[j], st))
                res = (px - entry) * d / R * (0.5 if half is not None else 1) + (half or 0)
                print("   sortie stop", fmt(x.iloc[j]))
                break
            if half is None and j > k and ((x.high[j] >= tp) if d == 1 else (x.low[j] <= tp)):
                half = 0.5 * 0.5
                st = entry
                print("   50 % à l'objectif", fmt(x.iloc[j]))
        if res is None:
            res = (half or 0) + (x.close.iloc[-1] - entry) * d / R * (0.5 if half is not None else 1)
        print(f"V04 veille {pd.Timestamp(pd_).date()} amplitude {rng:.2f} ouverture {o0:.2f} niveaux {dn:.2f}/{up:.2f} "
              f"entrée {'achat' if d == 1 else 'vente'} {entry:.2f} à {fmt(x.iloc[k])[:5]} R {R:.2f}")
        show("V04", D, (res, cost / R), r)

        # ---- V13 : contrôle, achat à l'ouverture, +0,25 ATR / −1 ATR
        r = last_trade("V13")
        D = r.day
        x = day_min(df, D)
        atr = bf.atr[bf.index < D].iloc[-1]
        o0 = x.open.iloc[0]
        tp, st = o0 + 0.25 * atr, o0 - atr
        res = None
        for j in range(len(x)):
            if x.low[j] <= st:
                res = ((st if j == 0 else min(x.open[j], st)) - o0) / atr; print("   stop", fmt(x.iloc[j])); break
            if x.high[j] >= tp:
                res = ((tp if j == 0 else max(x.open[j], tp)) - o0) / atr; print("   objectif", fmt(x.iloc[j])); break
        if res is None:
            res = (x.close.iloc[-1] - o0) / atr; print("   clôture", fmt(x.iloc[-1]))
        print(f"V13 ouverture {o0:.2f} ATR {atr:.2f} objectif {tp:.2f} stop {st:.2f}")
        show("V13", D, (res, cost / atr), r)

    # ---- V09 : gap 0,1-0,5 ATR joué vers la clôture de la veille
    r = last_trade("V09", inst)
    D = r.day
    x = day_min(df, D)
    pb = bf[bf.index < D].iloc[-1]
    gap = x.open.iloc[0] - pb.C
    d = -1 if gap > 0 else 1
    k = int(np.where(x.hm == 571)[0][0])
    entry, atr = x.open[k], pb.atr
    st, tp, res = entry - d * atr, pb.C, None
    for j in range(k, len(x)):
        if (x.low[j] <= st) if d == 1 else (x.high[j] >= st):
            res = ((st if j == k else (min(x.open[j], st) if d == 1 else max(x.open[j], st))) - entry) * d / atr
            print("   stop", fmt(x.iloc[j])); break
        if (x.high[j] >= tp) if d == 1 else (x.low[j] <= tp):
            res = ((tp if j == k else (max(x.open[j], tp) if d == 1 else min(x.open[j], tp))) - entry) * d / atr
            print("   objectif", fmt(x.iloc[j])); break
    if res is None:
        res = (x.close.iloc[-1] - entry) * d / atr; print("   clôture", fmt(x.iloc[-1]))
    print(f"V09 {inst} clôture veille ({pb.name.date()}) {pb.C:.2f} ouverture {x.open.iloc[0]:.2f} gap {gap / atr:+.2f} ATR "
          f"(ATR {atr:.2f}) → {'achat' if d == 1 else 'vente'} 09:31 à {entry:.2f}")
    show(f"V09 {inst}", D, (res, cost / atr), r)

    # ---- V07 : RSI2 H1 (barres H1 par resample ancré à 09:30, RSI2 ewm), sortie SMA5 H1
    r = last_trade("V07", inst)
    D = r.day
    S = lib.sessions_ny(df)
    full_days = sorted(S)
    rows = []
    for dd in full_days:
        hm, O, H, L, C = S[dd]
        s = pd.Series(C, index=dd + pd.to_timedelta(hm, unit="min"))
        h1 = s.resample("60min", origin=dd + pd.Timedelta(minutes=570)).last()
        rows.append(h1)
    h1 = pd.concat(rows).dropna()
    ch = h1.diff()
    up, dn = ch.clip(lower=0).ewm(alpha=0.5, adjust=False).mean(), (-ch).clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn)
    sma5 = h1.rolling(5).mean()
    sig_bar = r.t_in - pd.Timedelta(minutes=60)           # barre dont la clôture déclenche l'entrée
    pb = bf[bf.index < D].iloc[-1]
    trend = 1 if pb.C > pb.sma200 else -1
    x = day_min(df, D)
    k = int(np.where(x.hm == (r.t_in - D).total_seconds() // 60)[0][0])
    entry, atr, d = x.open[k], pb.atr, trend
    st, res = entry - d * atr, None
    bar_ends = {int((b - D).total_seconds() // 60) + 59: b for b in h1[(h1.index >= sig_bar + pd.Timedelta(minutes=60)) & (h1.index.normalize() == D)].index}
    for j in range(k, len(x)):
        if (x.low[j] <= st) if d == 1 else (x.high[j] >= st):
            res = ((st if j == k else (min(x.open[j], st) if d == 1 else max(x.open[j], st))) - entry) * d / atr; print("   stop", fmt(x.iloc[j])); break
        hmj = int(x.hm[j])
        if hmj in bar_ends and j < len(x) - 1:
            b = bar_ends[hmj]
            if (x.close[j] > sma5[b]) if d == 1 else (x.close[j] < sma5[b]):
                res = (x.open[j + 1] - entry) * d / atr
                print(f"   clôture H1 {x.close[j]:.2f} au-delà de la SMA5 {sma5[b]:.2f} → sortie", fmt(x.iloc[j + 1])); break
    if res is None:
        res = (x.close.iloc[-1] - entry) * d / atr; print("   clôture", fmt(x.iloc[-1]))
    print(f"V07 {inst} tendance {'haussière' if trend == 1 else 'baissière'} (C {pb.C:.2f} vs SMA200 {pb.sma200:.2f}), "
          f"RSI2 H1 à la clôture de la barre {sig_bar.strftime('%H:%M')} = {rsi[sig_bar]:.2f} (trades.csv {r.rsi2:.2f}), "
          f"entrée {entry:.2f}")
    show(f"V07 {inst}", D, (res, cost / atr), r)

    # ---- V15 : retour au TWAP
    r = last_trade("V15", inst)
    D = r.day
    x = day_min(df, D)
    atr = bf.atr[bf.index < D].iloc[-1]
    tw = x.close.expanding().mean()
    k = int(np.where(x.hm == (r.t_in - D).total_seconds() // 60)[0][0])
    dev = x.close[k - 1] - tw[k - 1]
    d = -1 if dev > 0 else 1
    entry = x.open[k]
    st, res = entry - d * atr, None
    for j in range(k, len(x)):
        if (x.low[j] <= st) if d == 1 else (x.high[j] >= st):
            res = ((st if j == k else (min(x.open[j], st) if d == 1 else max(x.open[j], st))) - entry) * d / atr; print("   stop", fmt(x.iloc[j])); break
        tg = tw[j - 1]
        if (x.high[j] >= tg) if d == 1 else (x.low[j] <= tg):
            res = ((tg if j == k else (max(x.open[j], tg) if d == 1 else min(x.open[j], tg))) - entry) * d / atr
            print(f"   TWAP {tg:.2f} touché", fmt(x.iloc[j])); break
    if res is None:
        res = (x.close.iloc[-1] - entry) * d / atr; print("   clôture", fmt(x.iloc[-1]))
    print(f"V15 {inst} écart au TWAP {dev / atr:+.2f} ATR à {fmt(x.iloc[k - 1])[:5]} (1er signal de la journée ? "
          f"{bool((np.abs(x.close - tw)[(x.hm >= 600) & (x.index < k - 1)] < 0.5 * atr).all())}) → "
          f"{'achat' if d == 1 else 'vente'} {entry:.2f}")
    show(f"V15 {inst}", D, (res, cost / atr), r)

    # ---- V16 : RSI2 15:55 < 10 et C > SMA200 → sortie 1re ouverture profitable (≤ 5 séances)
    r = last_trade("V16", inst)
    D = r.day
    b = b55.loc[D]
    nxt = [d for d in full_days if d > D][:5]
    opens = [S[d][1][0] for d in nxt]
    ex = next((i for i, o in enumerate(opens) if o > b.C), 4)
    nights = (nxt[ex] - D).days
    res = (opens[ex] - b.C) / b.atr
    cr = (cost + b.C * lib.SWAP[inst][0] * nights / 360) / b.atr
    print(f"V16 {inst} signal {D.date()} RSI2 {b.rsi2:.2f} C15:55 {b.C:.2f} SMA200 {b.sma200:.2f} ATR {b.atr:.2f} ; "
          f"ouvertures suivantes {[round(o, 2) for o in opens]} → sortie le {nxt[ex].date()} ({nights} nuits)")
    show(f"V16 {inst}", D, (res, cr), r)
    del df
