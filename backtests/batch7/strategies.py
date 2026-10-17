"""Lot 7 — 5 stratégies M5/M15. Règles et critère fixés avant le test. DAX exclu.

1. Cassure du pré-marché (NASDAQ100, SP500) — heure de New York : range 04:00-09:30 ; entrée au 1er franchissement entre
   09:30 et 15:00 (au cours d'ouverture si l'ouverture est déjà au-delà) ; stop = bord opposé ; sortie 16:00.
   Variantes : deux sens / achats seuls.
2. ORB or ouverture COMEX (XAUUSD) — heure de New York : range 08:20-08:50 ; entrée jusqu'à 14:30 ; stop = bord opposé ;
   sortie 16:00 ou TP 1:2. Variantes : deux sens / achats seuls × sortie clôture / TP 1:2.
3. NR7 M15 (NASDAQ100 séance 09:30-16:00 NY ; XAUUSD séance 08:00-16:30 Londres) : bougie M15 de séance dont l'amplitude est
   la plus petite des 7 dernières → ordres stop au-dessus du plus haut et sous le plus bas, valables 4 bougies M15 ;
   1 trade max par jour ; stop = bord opposé de la NR7 (variante « stop NR7 ») ou 1 ATR M15 (variante « stop 1 ATR ») ;
   sortie en fin de séance.
4. Retour à la moyenne asiatique (EURUSD, XAUUSD) — heure de Paris : bandes de Bollinger M15 (20, 2,5). Entre 01:00 et 07:45,
   clôture M15 sous la bande basse → achat à l'ouverture suivante (au-dessus de la haute → vente) ; objectif = moyenne 20 au
   signal ; stop = 1 ATR M15 ; sortie forcée 08:00 ; 2 trades max par nuit. Coûts × 1,5 (spread de nuit).
5. Prix moyen de séance (NASDAQ100) — heure de New York : moyenne (H+B+C)/3 des minutes 09:30-11:00. À 11:00, clôture > moyenne
   et > ouverture → achat (inverse → vente) ; stop = moyenne ∓ 0,1 ATR journalier ; sortie 16:00. Variantes : deux sens / achats seuls.
Coûts aller-retour : XAUUSD 0,47 ; EURUSD 0,00015 ; SP500 0,75 ; NASDAQ100 1,5. 100 € par R.
Critère : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, E nette OOS > 0 avec coûts doublés.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402

COST = {"XAUUSD": 0.47, "EURUSD": 0.00015, "SP500": 0.75, "NASDAQ100": 1.5}


def days_of(df):
    out = {}
    for d, g in df.groupby("day"):
        if d.dayofweek < 5:
            out[d] = {k: g[k].values for k in ("hm", "open", "high", "low", "close")}
    return out


def run_trade(g, k, d, entry, stop, tp, end_hm):
    """Position ouverte à la minute k (indice dans la journée). Stop prioritaire. Sortie à la clôture de la dernière minute < end_hm."""
    hm, O, H, L, C = g["hm"], g["open"], g["high"], g["low"], g["close"]
    if (L[k] <= stop) if d == 1 else (H[k] >= stop):
        return stop
    last = None
    for j in range(k + 1, len(hm)):
        if hm[j] >= end_hm:
            break
        last = j
        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
            return O[j] if ((O[j] < stop) if d == 1 else (O[j] > stop)) else stop
        if tp is not None and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
            return O[j] if ((O[j] > tp) if d == 1 else (O[j] < tp)) else tp
    return C[last] if last is not None else C[k]


def breakout(g, hi, lo, start, last_entry, end_hm, stop_hi, stop_lo, rr=None):
    """Premier franchissement de hi / lo entre start et last_entry. Renvoie (d, entry, exit) ou None."""
    hm, O, H, L = g["hm"], g["open"], g["high"], g["low"]
    idx = np.where((hm >= start) & (hm < last_entry))[0]
    if len(idx) == 0:
        return None
    up, dn = H[idx] > hi, L[idx] < lo
    hit = up | dn
    if not hit.any():
        return None
    j = int(hit.argmax())
    if up[j] and dn[j]:
        return None
    k = idx[j]
    d = 1 if up[j] else -1
    entry = max(O[k], hi) if d == 1 else min(O[k], lo)
    stop = stop_hi if d == 1 else stop_lo
    risk = (entry - stop) * d
    if risk <= 0:
        return None
    tp = None if rr is None else entry + d * rr * risk
    return d, entry, run_trade(g, k, d, entry, stop, tp, end_hm), risk


def premarket(inst):
    D = days_of(load_m1(inst, "America/New_York"))
    rows = []
    for day, g in D.items():
        pm = (g["hm"] >= 240) & (g["hm"] < 570)
        if pm.sum() < 200:
            continue
        hi, lo = g["high"][pm].max(), g["low"][pm].min()
        r = breakout(g, hi, lo, 570, 900, 960, lo, hi)
        if r:
            d, e, x, risk = r
            for v in ("deux sens", "achats seuls"):
                if v == "achats seuls" and d == -1:
                    continue
                rows.append((inst, "Pré-marché", f"Pré-marché · {v}", day, d, e, x, risk, 1.0))
    return rows


def comex(inst="XAUUSD"):
    D = days_of(load_m1(inst, "America/New_York"))
    rows = []
    for day, g in D.items():
        rg = (g["hm"] >= 500) & (g["hm"] < 530)
        if rg.sum() < 27:
            continue
        hi, lo = g["high"][rg].max(), g["low"][rg].min()
        for rr, lab in ((None, "clôture"), (2, "TP 1:2")):
            r = breakout(g, hi, lo, 530, 870, 960, lo, hi, rr)
            if r:
                d, e, x, risk = r
                for v in ("deux sens", "achats seuls"):
                    if v == "achats seuls" and d == -1:
                        continue
                    rows.append((inst, "ORB COMEX", f"ORB COMEX · {v} · {lab}", day, d, e, x, risk, 1.0))
    return rows


def nr7(inst, tz, s0, s1):
    D = days_of(load_m1(inst, tz))
    rows = []
    for day, g in D.items():
        hm = g["hm"]
        sess = (hm >= s0) & (hm < s1)
        if sess.sum() < 0.9 * (s1 - s0):
            continue
        # bougies M15 de séance
        bins = (hm[sess] - s0) // 15
        Hs, Ls, Cs = g["high"][sess], g["low"][sess], g["close"][sess]
        nb = bins.max() + 1
        bh = np.array([Hs[bins == b].max() if (bins == b).any() else np.nan for b in range(nb)])
        bl = np.array([Ls[bins == b].min() if (bins == b).any() else np.nan for b in range(nb)])
        bc = np.array([Cs[bins == b][-1] if (bins == b).any() else np.nan for b in range(nb)])
        rng = bh - bl
        prevc = np.r_[np.nan, bc[:-1]]
        tr = np.nanmax(np.vstack([rng, abs(bh - prevc), abs(bl - prevc)]), axis=0)
        for b in range(7, nb - 5):
            if not (rng[b] > 0 and rng[b] == np.nanmin(rng[b - 6:b + 1]) and (rng[b - 6:b] > rng[b]).all()):
                continue
            atr = np.nanmean(tr[b - 6:b + 1])
            start, stop_ = s0 + (b + 1) * 15, s0 + (b + 5) * 15
            done = False
            for lab, sh, sl in (("stop NR7", bl[b], bh[b]), ("stop 1 ATR", bh[b] - atr, bl[b] + atr)):
                r = breakout(g, bh[b], bl[b], start, min(stop_, s1 - 30), s1, sh, sl)
                if r:
                    d, e, x, risk = r
                    rows.append((inst, "NR7", f"NR7 M15 · {lab}", day, d, e, x, risk, 1.0))
                    done = True
            if done:
                break
    return rows


def asian(inst):
    df = load_m1(inst, "Europe/Paris")
    m15 = df.set_index("time").resample("15min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    c = m15["close"]
    sma, sd = c.rolling(20).mean(), c.rolling(20).std()
    pc = c.shift(1)
    atr = pd.concat([m15["high"] - m15["low"], (m15["high"] - pc).abs(), (m15["low"] - pc).abs()], axis=1).max(axis=1).rolling(14).mean()
    loc = m15.index.tz_convert("Europe/Paris")
    m15 = m15.assign(sma=sma, up=sma + 2.5 * sd, dn=sma - 2.5 * sd, atr=atr, hm=loc.hour * 60 + loc.minute,
                     day=pd.to_datetime(loc.date))
    D = days_of(df)
    rows = []
    for day, g15 in m15.groupby("day"):
        if day.dayofweek >= 5 or day not in D:
            continue
        g = D[day]
        n = 0
        busy_until = -1
        for r in g15[(g15["hm"] >= 60) & (g15["hm"] < 465)].itertuples():
            if n >= 2 or r.hm < busy_until or np.isnan(r.up) or np.isnan(r.atr):
                continue
            d = 1 if r.close < r.dn else (-1 if r.close > r.up else 0)
            if d == 0:
                continue
            k_idx = np.where(g["hm"] >= r.hm + 15)[0]
            if len(k_idx) == 0:
                continue
            k = k_idx[0]
            if g["hm"][k] >= 480:
                continue
            entry = g["open"][k]
            stop, tp = entry - d * r.atr, r.sma
            if (tp - entry) * d <= 0:
                continue
            x = run_trade(g, k, d, entry, stop, tp, 480)
            rows.append((inst, "Asie retour moyenne", "Asie · Bollinger 2,5", day, d, entry, x, r.atr, 1.5))
            n += 1
            # position suivante seulement après la sortie (approximation : 15 min après l'entrée minimum)
            busy_until = r.hm + 30
    return rows


def twap(inst="NASDAQ100"):
    df = load_m1(inst, "America/New_York")
    D = days_of(df)
    keys = sorted(k for k in D if ((D[k]["hm"] >= 570) & (D[k]["hm"] < 960)).sum() > 300)
    hi = {k: D[k]["high"][(D[k]["hm"] >= 570) & (D[k]["hm"] < 960)].max() for k in keys}
    lo = {k: D[k]["low"][(D[k]["hm"] >= 570) & (D[k]["hm"] < 960)].min() for k in keys}
    tr = pd.Series({k: hi[k] - lo[k] for k in keys})
    atr = tr.rolling(14).mean().shift(1)
    rows = []
    for day in keys:
        g = D[day]
        hm = g["hm"]
        m = (hm >= 570) & (hm < 660)
        if m.sum() < 85 or np.isnan(atr.get(day, np.nan)):
            continue
        tw = ((g["high"][m] + g["low"][m] + g["close"][m]) / 3).mean()
        o = g["open"][m][0]
        k_idx = np.where(hm >= 660)[0]
        if len(k_idx) == 0:
            continue
        k = k_idx[0]
        c = g["close"][k - 1]
        d = 1 if (c > tw and c > o) else (-1 if (c < tw and c < o) else 0)
        if d == 0:
            continue
        entry = g["open"][k]
        stop = tw - d * 0.1 * atr[day]
        risk = (entry - stop) * d
        if risk <= 0:
            continue
        x = run_trade(g, k, d, entry, stop, None, 960)
        for v in ("deux sens", "achats seuls"):
            if v == "achats seuls" and d == -1:
                continue
            rows.append((inst, "Prix moyen", f"Prix moyen 11:00 · {v}", day, d, entry, x, risk, 1.0))
    return rows


def main():
    rows = []
    jobs = [("pré-marché NASDAQ100", lambda: premarket("NASDAQ100")), ("pré-marché SP500", lambda: premarket("SP500")),
            ("COMEX", comex),
            ("NR7 NASDAQ100", lambda: nr7("NASDAQ100", "America/New_York", 570, 960)),
            ("NR7 XAUUSD", lambda: nr7("XAUUSD", "Europe/London", 480, 990)),
            ("Asie EURUSD", lambda: asian("EURUSD")), ("Asie XAUUSD", lambda: asian("XAUUSD")),
            ("Prix moyen", twap)]
    for name, f in jobs:
        rows += f()
        print("ok", name, flush=True)
    t = pd.DataFrame(rows, columns=["instrument", "strategie", "reglage", "day", "d", "entry", "exit", "risque", "cost_mult"])
    t = t[t["day"] >= "2020-01-01"]
    t["gross_r"] = (t["exit"] - t["entry"]) * t["d"] / t["risque"]
    t["cost_r"] = t["instrument"].map(COST) * t["cost_mult"] / t["risque"]
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (inst, reg), g in t.groupby(["instrument", "reglage"]):
        g = g.sort_values("day")
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        x = g["net_r"]
        top = x.nlargest(5).index
        wk = g.groupby(g["day"].dt.to_period("W"))["net_r"].sum()
        r = {"instrument": inst, "reglage": reg, "brut": st(g["gross_r"].values), "net": st(x.values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "sans_top5": float(x.drop(top).mean()),
             "semaines_positives": float((wk > 0).mean() * 100), "trades_par_an": float(len(g) / 6.75)}
        r["valide"] = bool(r["is"] and r["oos"] and r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0
                           and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {inst:9} {reg:38} n{r['net']['trades']:>5} WR{r['net']['win_rate']:5.1f} "
              f"Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} "
              f"OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} sansTop5{r['sans_top5']:+.3f} "
              f"{r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€ sem+{r['semaines_positives']:.0f}%")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
