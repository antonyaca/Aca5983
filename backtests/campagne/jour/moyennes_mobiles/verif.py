"""Vérifications indépendantes de run.py (code séparé, écrit autrement) :
1. Trades recalculés « à la main » : M1 TRONQUÉES strictement avant l'instant d'entrée (aucune donnée future possible),
   bougies refaites avec pandas.resample, indicateurs recodés en boucles Python (EMA, Wilder, RSI, MACD, Supertrend selon
   le code Pine de ta.supertrend), sortie rejouée minute par minute. Écart toléré : 1e-6 en prix relatif.
2. Règle du jour (lib.regle_anto) : au plus 2 trades/jour, 2e seulement si le 1er perd, 2e entré après la sortie du 1er,
   1er = 1er candidat du jour.
3. Trades par an et par marché, coût médian par marché, heures locales d'entrée.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402

lib = run.lib


def ema_loop(x, n):
    a, out, y = 2.0 / (n + 1), np.empty(len(x)), None
    for i, v in enumerate(x):
        y = v if y is None else y + a * (v - y)
        out[i] = y
    return out


def wilder_loop(x, n):
    out, y = np.empty(len(x)), None
    for i, v in enumerate(x):
        y = v if y is None else y + (v - y) / n
        out[i] = y
    return out


def tr_loop(h, l, c):
    out = np.empty(len(h))
    for i in range(len(h)):
        out[i] = h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    return out


def rsi_loop(c, n=14):
    g = [0.0] + [max(c[i] - c[i - 1], 0.0) for i in range(1, len(c))]
    lo = [0.0] + [max(c[i - 1] - c[i], 0.0) for i in range(1, len(c))]
    ag, al = wilder_loop(np.array(g), n), wilder_loop(np.array(lo), n)
    return np.array([100.0 if b == 0 else 100 - 100 / (1 + a / b) for a, b in zip(ag, al)])


def supertrend_pine(h, l, c, n=10, f=3.0):
    """Traduction ligne à ligne de ta.supertrend (Pine v5) ; direction Pine : -1 = haussier."""
    atr = wilder_loop(tr_loop(h, l, c), n)
    up_prev = lo_prev = st_prev = None
    lines, dirs = [], []
    for i in range(len(c)):
        src = (h[i] + l[i]) / 2
        upper, lower = src + f * atr[i], src - f * atr[i]
        if i > 0:
            lower = lower if (lower > lo_prev or c[i - 1] < lo_prev) else lo_prev
            upper = upper if (upper < up_prev or c[i - 1] > up_prev) else up_prev
        if i == 0:
            direction = 1
        elif st_prev == up_prev:
            direction = -1 if c[i] > upper else 1
        else:
            direction = 1 if c[i] < lower else -1
        st = lower if direction == -1 else upper
        lines.append(st)
        dirs.append(-direction)                      # converti : +1 = haussier
        up_prev, lo_prev, st_prev = upper, lower, st
    return np.array(lines), np.array(dirs)


def resample(m1, rule):
    b = m1.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return b


def recompute(full, tr, v):
    """Recalcule un trade candidat à partir des M1 tronquées avant t_in. Renvoie dict des valeurs attendues."""
    cfg = run.RULES[v]
    inst = tr["instrument"]
    tz, o_hm, e_hm = run.SESS[inst]
    t_in = pd.Timestamp(tr["t_in"]).tz_localize("UTC")
    past = full[full.index < t_in]                  # <-- troncature : rien après l'instant d'entrée
    entry = full.loc[t_in, "open"]
    loc_in = t_in.tz_convert(tz)
    sess_end = (loc_in.normalize() + pd.Timedelta(minutes=e_hm))
    out = {"entry": entry}
    # journalier (clôture 17:00 NY), journées complètes AVANT la journée de trading de l'entrée
    nyk = (past.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)).normalize()
    g = past.groupby(nyk)
    dd = pd.DataFrame({"h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last(), "n": g.size()})
    td_in = (t_in.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)).normalize()
    dd = dd[(dd["n"] >= 600) & (dd.index < td_in)]
    atr_d = wilder_loop(tr_loop(dd["h"].values, dd["l"].values, dd["c"].values), 14)[-1]
    tkey = cfg.get("trend")
    if tkey and tkey.startswith("sma"):
        n = int(tkey[3:])
        trend = np.sign(dd["c"].iloc[-1] - dd["c"].iloc[-n:].mean())
    elif tkey == "long":
        trend = 1
    else:
        trend = None
    # H1 (heures pleines), bougies closes au plus tard à t_in
    h1 = resample(past, "60min")
    h1 = h1[h1.index + pd.Timedelta(minutes=60) <= t_in]
    H, L, C = h1["high"].values, h1["low"].values, h1["close"].values
    atr_h1 = wilder_loop(tr_loop(H, L, C), 14)
    if tkey == "ema200h1":
        trend = np.sign(C[-1] - ema_loop(C, 200)[-1])
    d = None
    if cfg["kind"] == "open":
        first = full[(full.index >= t_in - pd.Timedelta(minutes=6))]
        o_utc = (loc_in.normalize() + pd.Timedelta(minutes=o_hm)).tz_convert("UTC")
        assert o_utc <= t_in <= o_utc + pd.Timedelta(minutes=5), "entrée pas à l'ouverture"
        assert not ((full.index >= o_utc) & (full.index < t_in)).any(), "une minute plus tôt existait"
        del first
        d = int(trend)
    else:
        sig_close = h1.index[-1] + pd.Timedelta(minutes=60)
        if cfg["kind"] == "m15":
            q = resample(past, "15min")
            q = q[q.index + pd.Timedelta(minutes=15) <= t_in]
            e9, e21 = ema_loop(q["close"].values, 9), ema_loop(q["close"].values, 21)
            sig_close = q.index[-1] + pd.Timedelta(minutes=15)
            s = 1 if (e9[-1] > e21[-1] and e9[-2] <= e21[-2]) else (-1 if (e9[-1] < e21[-1] and e9[-2] >= e21[-2]) else 0)
        elif cfg["sig"] == "st":
            line, dirs = supertrend_pine(H, L, C, 10, 3.0)
            s = int(dirs[-1]) if dirs[-1] != dirs[-2] else 0
            out["stop_attendu_st"] = line[-1]
        elif cfg["sig"] == "macd":
            mac = ema_loop(C, 12) - ema_loop(C, 26)
            sg = ema_loop(mac, 9)
            s = 1 if (mac[-1] > sg[-1] and mac[-2] <= sg[-2]) else (-1 if (mac[-1] < sg[-1] and mac[-2] >= sg[-2]) else 0)
        elif cfg["sig"] in ("rsi_zone", "rsi_mom"):
            r = rsi_loop(C, 14)
            lvl_up, lvl_dn = (30, 70) if cfg["sig"] == "rsi_zone" else (70, 30)
            s = 1 if (r[-2] < lvl_up <= r[-1]) else (-1 if (r[-2] > lvl_dn >= r[-1]) else 0)
        elif cfg["sig"] == "pullback20":
            e20, e200 = ema_loop(C, 20)[-1], ema_loop(C, 200)[-1]
            s = 1 if (C[-1] > e200 and e20 > e200 and L[-1] <= e20 and C[-1] > e20) else \
                (-1 if (C[-1] < e200 and e20 < e200 and H[-1] >= e20 and C[-1] < e20) else 0)
        elif cfg["sig"] == "cross20":
            e20 = ema_loop(C, 20)
            s = 1 if (C[-1] > e20[-1] and C[-2] <= e20[-2]) else (-1 if (C[-1] < e20[-1] and C[-2] >= e20[-2]) else 0)
        assert t_in - pd.Timedelta(minutes=5) <= sig_close <= t_in, "bougie signal non close juste avant l'entrée"
        assert s != 0, "pas de signal sur la dernière bougie close"
        if trend is not None:
            assert s == trend, "signal contre la tendance"
        d = s
    out["d"] = d
    if cfg["sl"] == "atrd05":
        stop = entry - d * 0.5 * atr_d
    elif cfg["sl"] == "atrh1":
        stop = entry - d * atr_h1[-1]
    else:
        stop = out["stop_attendu_st"]
    risk = (entry - stop) * d
    tp = entry + d * cfg["tp"] * risk if cfg["tp"] else None
    out.update(stop=stop, R=risk, tp=tp)
    # sortie minute par minute
    fut = full[(full.index >= t_in) & (full.index < sess_end.tz_convert("UTC"))]
    px = t_out = None
    for k, (ts, row) in enumerate(fut.iterrows()):
        hit_sl = row["low"] <= stop if d == 1 else row["high"] >= stop
        hit_tp = tp is not None and (row["high"] >= tp if d == 1 else row["low"] <= tp)
        if hit_sl:
            gap = k > 0 and ((row["open"] < stop) if d == 1 else (row["open"] > stop))
            px, t_out = (row["open"] if gap else stop), ts
            break
        if hit_tp:
            px, t_out = tp, ts
            break
    if px is None:
        px, t_out = fut["close"].iloc[-1], fut.index[-1]
    mult = 2.0 if int((t_in.tz_convert("America/New_York").tz_localize(None).normalize()
                       - pd.Timestamp("1970-01-01")).days) in run.MACRO else 1.0
    out.update(exit=px, t_out=(t_out + pd.Timedelta(minutes=1)).tz_localize(None), gross_r=d * (px - entry) / risk,
               cost_r=lib.COST[inst] * mult / risk)
    return out


def close(a, b, ref):
    return abs(a - b) <= 1e-6 * max(abs(ref), 1.0)


def check_trades():
    plan = [("V03", "NASDAQ100"), ("V09", "SP500"), ("V05", "EURUSD"), ("V01", "NIKKEI225"), ("V10", "XAUUSD"),
            ("V11", "AUDUSD"), ("V12", "GBPUSD"), ("V13", "FTSE100"), ("V14", "NASDAQ100"), ("V15", "USDJPY"),
            ("V17", "NIKKEI225"), ("V18", "XAGUSD"), ("V19", "EURUSD")]
    rng = np.random.default_rng(2026)
    cache = {v: pd.read_csv(os.path.join(HERE, "trades", f"{v}.csv.gz"), parse_dates=["day", "t_in", "t_out"])
             for v in sorted({p[0] for p in plan})}
    by_inst = {}
    for v, inst in plan:
        by_inst.setdefault(inst, []).append(v)
    n_ok = n_tot = 0
    for inst, vs in by_inst.items():
        df = lib.load(inst, "UTC")
        full = df.set_index("time")[["open", "high", "low", "close"]]
        del df
        for v in vs:
            c = cache[v]
            c = c[(c["instrument"] == inst) & (c["day"] >= "2011-01-01")]
            for i in rng.choice(len(c), size=2, replace=False):
                tr = c.iloc[i]
                n_tot += 1
                try:
                    e = recompute(full, tr, v)
                    ok = (e["d"] == tr["d"] and close(e["entry"], tr["entry"], tr["entry"])
                          and close(e["stop"], tr["stop"], tr["entry"]) and close(e["exit"], tr["exit"], tr["entry"])
                          and e["t_out"] == tr["t_out"] and abs(e["gross_r"] - tr["gross_r"]) < 1e-6
                          and abs(e["cost_r"] - tr["cost_r"]) < 1e-9)
                    msg = (f"sens {e['d']:+d} entrée {e['entry']:.5f} stop {e['stop']:.5f}/{tr['stop']:.5f} "
                           f"sortie {e['exit']:.5f}/{tr['exit']:.5f} ({tr['sortie']}) brut {e['gross_r']:+.3f}/{tr['gross_r']:+.3f} "
                           f"coût {e['cost_r']:.3f}/{tr['cost_r']:.3f}")
                except AssertionError as err:
                    ok, msg = False, f"ÉCHEC : {err}"
                n_ok += ok
                print(f"{'OK ' if ok else 'ÉCART'} {v} {inst:9} {tr['t_in']} UTC  {msg}", flush=True)
        del full
    print(f"=> {n_ok}/{n_tot} trades recalculés à l'identique (données tronquées à l'entrée)\n")


def check_rule():
    pb = 0
    for v in ("V03", "V11", "V13"):
        c = pd.read_csv(os.path.join(HERE, "trades", f"{v}.csv.gz"), parse_dates=["day", "t_in", "t_out"])
        c["rang"] = c["instrument"].map(run.RANK)
        c = c.sort_values(["day", "t_in", "rang"], kind="stable").reset_index(drop=True)
        for scope in ("PORTEFEUILLE", "NASDAQ100", "EURUSD"):
            cc = c if scope == "PORTEFEUILLE" else c[c["instrument"] == scope]
            tk = lib.regle_anto(cc)
            net = tk["gross_r"] - tk["cost_r"]
            for day, g in tk.groupby("day"):
                cand = cc[cc["day"] == day]
                if len(g) > 2 or g.index[0] != cand.index[0]:
                    pb += 1
                if len(g) == 2 and not (net.loc[g.index[0]] < 0 and g["t_in"].iloc[1] >= g["t_out"].iloc[0]):
                    pb += 1
            n2 = (tk.groupby("day").size() == 2).sum()
            print(f"{v} {scope:12} jours {tk['day'].nunique():5d}  jours à 2 trades {n2:5d}  "
                  f"candidats {len(cc):6d} -> pris {len(tk):5d}", flush=True)
    print(f"=> anomalies de la règle du jour : {pb}\n")


def check_counts():
    for v in ("V03", "V10", "V13"):
        c = pd.read_csv(os.path.join(HERE, "trades", f"{v}.csv.gz"), parse_dates=["day", "t_in", "t_out"])
        c = c[c["day"] >= "2011-01-01"]
        print(f"{v} candidats par an et par marché :")
        print(c.groupby([c["instrument"], c["day"].dt.year]).size().unstack(fill_value=0).to_string())
        print("coût médian (R) :", c.groupby("instrument")["cost_r"].median().round(3).to_dict())
        hh = {}
        for inst, g in c.groupby("instrument"):
            loc = pd.DatetimeIndex(g["t_in"]).tz_localize("UTC").tz_convert(run.SESS[inst][0])
            hm = loc.hour * 60 + loc.minute
            hh[inst] = f"{hm.min() // 60:02d}:{hm.min() % 60:02d}-{hm.max() // 60:02d}:{hm.max() % 60:02d}"
        print("heures locales d'entrée (min-max) :", hh, "\n", flush=True)


if __name__ == "__main__":
    check_trades()
    check_rule()
    check_counts()
