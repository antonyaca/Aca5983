"""Lot 3 — stratégies simples. Règles et critère fixés avant les tests.

Critère (identique aux lots précédents) : E nette > 0 en IS (2020-2023) ET en OOS (2024+), PF net ≥ 1,10,
E nette OOS > 0 avec frais doublés.

1. ORB 30 min Europe (DAX, CAC40, EUROSTOXX50) — heure de Paris : range 09:00-09:30, entrée au 1er franchissement
   jusqu'à 16:00, stop au bord opposé, sortie 17:30. Variantes : achats seuls / deux sens. (Mêmes règles que l'ORB Nasdaq.)
2. RSI 2 (SP500, NASDAQ100) : achat à la clôture si RSI(2) < 10 et clôture > SMA 200 ; vente à la clôture dès que clôture > SMA 5.
3. Fin / début de mois (SP500, NASDAQ100) : achat à la clôture de l'avant-dernière séance du mois, vente à la clôture
   de la 3e séance du mois suivant.
4. Rendement de nuit (SP500, NASDAQ100) : achat à la clôture 16:00, vente à l'ouverture 09:30 suivante.
5. Cassure 20 jours (XAUUSD, NASDAQ100) : achat (vente) à la clôture au-dessus du plus haut (sous le plus bas) des
   20 clôtures précédentes ; sortie à la clôture sous le plus bas (au-dessus du plus haut) des 10 clôtures précédentes.
   Variantes : deux sens / achats seuls.
6. Inside day (XAUUSD, SP500, NASDAQ100) : si le jour J est contenu dans J-1, le jour J+1 on entre à la cassure du haut
   ou du bas de J, stop au bord opposé, sortie à la clôture de J+1. Intraday.

Taille des positions : 1 R = 100 €. Stratégies 1, 5, 6 : R = distance au stop. Stratégies 2, 3, 4 (sans stop) :
R = ATR 14 jours à l'entrée (une perte d'un ATR coûte 100 €).
Coûts : spread + slippage aller-retour, plus financement de nuit (swap) pour les positions gardées la nuit :
6 %/an du nominal pour un achat, 1 %/an pour une vente, par nuit calendaire (base 360).
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
COST = {"XAUUSD": 0.47, "SP500": 0.75, "NASDAQ100": 1.5, "DAX": 1.5, "CAC40": 1.5, "EUROSTOXX50": 2.0}
SWAP_LONG, SWAP_SHORT = 0.06, 0.01
IS_END = pd.Timestamp("2024-01-01")
RISK_EUR = 100


def load_m1(inst, tz):
    files = sorted(glob.glob(os.path.join(ROOT, "data", inst, f"{inst}_M1_*.csv.gz")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates("time").sort_values("time")
    df = df[df["time"] >= "2019-09-01"].reset_index(drop=True)
    loc = df["time"].dt.tz_convert(tz)
    df["day"] = pd.to_datetime(loc.dt.date)
    df["hm"] = loc.dt.hour * 60 + loc.dt.minute
    return df


def daily_bars(df, start_hm, end_hm, min_bars):
    """Barres journalières sur la fenêtre [start_hm, end_hm) heure locale."""
    s = df[(df["hm"] >= start_hm) & (df["hm"] < end_hm)]
    g = s.groupby("day")
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "n": g["open"].count(),
                      "first_hm": g["hm"].first()})
    d = d[(d["n"] >= min_bars) & (d.index.dayofweek < 5) & (d["first_hm"] == start_hm)]
    prev = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - prev).abs(), (d["low"] - prev).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    return d


def rsi(c, n=2):
    delta = c.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def trade(inst, strat, reg, t_in, t_out, d, entry, exit_, risk, nights):
    gross = (exit_ - entry) * d / risk
    swap = entry * (SWAP_LONG if d == 1 else SWAP_SHORT) * nights / 360 / risk
    return {"instrument": inst, "strategie": strat, "reglage": reg, "day": t_in, "exit_day": t_out,
            "direction": "BUY" if d == 1 else "SELL", "risque": risk, "nuits": nights,
            "gross_r": gross, "cost_r": COST[inst] / risk + swap}


def walk(bars, d, stop):
    for i, (o, h, l) in enumerate(bars[["open", "high", "low"]].itertuples(index=False)):
        if (l <= stop) if d == 1 else (h >= stop):
            return (o if i > 0 and ((o < stop) if d == 1 else (o > stop)) else stop), "SL"
    return bars["close"].iloc[-1], "Clôture"


# ---------- 1. ORB Europe
def orb_europe(inst):
    df = load_m1(inst, "Europe/Paris")
    rows = []
    for day, g in df.groupby("day"):
        if day.dayofweek >= 5:
            continue
        rng = g[(g["hm"] >= 540) & (g["hm"] < 570)]
        if len(rng) < 28:
            continue
        rh, rl = rng["high"].max(), rng["low"].min()
        after = g[(g["hm"] >= 570) & (g["hm"] < 960)]
        up, dn = (after["high"] > rh).values, (after["low"] < rl).values
        hit = up | dn
        if not hit.any():
            continue
        j = hit.argmax()
        if up[j] and dn[j]:
            continue
        bar = after.iloc[j]
        d = 1 if up[j] else -1
        entry = max(bar["open"], rh) if d == 1 else min(bar["open"], rl)
        stop = rl if d == 1 else rh
        risk = (entry - stop) * d
        if risk <= 0:
            continue
        if (d == 1 and bar["low"] <= stop) or (d == -1 and bar["high"] >= stop):
            px = stop
        else:
            rest = g[(g["hm"] > bar["hm"]) & (g["hm"] < 1050)]
            if rest.empty:
                continue
            px, _ = walk(rest, d, stop)
        for reg in ("ORB 30 min Europe · deux sens", "ORB 30 min Europe · achats seuls"):
            if reg.endswith("achats seuls") and d == -1:
                continue
            rows.append(trade(inst, "ORB Europe", reg, day, day, d, entry, px, risk, 0))
    return rows


# ---------- 2-5 sur barres journalières
def swing(inst, tz, rth, min_bars):
    df = load_m1(inst, tz)
    d = daily_bars(df, rth[0], rth[1], min_bars)
    c = d["close"]
    d["rsi2"], d["sma5"], d["sma200"] = rsi(c), c.rolling(5).mean(), c.rolling(200).mean()
    d["hh20"], d["ll20"] = c.shift(1).rolling(20).max(), c.shift(1).rolling(20).min()
    d["hh10"], d["ll10"] = c.shift(1).rolling(10).max(), c.shift(1).rolling(10).min()
    idx = list(d.index)
    rows = []
    nights = lambda a, b: (b - a).days

    if inst in ("SP500", "NASDAQ100"):
        # 2. RSI 2
        i = 0
        while i < len(idx):
            r = d.iloc[i]
            if not np.isnan(r["sma200"]) and r["rsi2"] < 10 and r["close"] > r["sma200"] and r["atr"] > 0:
                for j in range(i + 1, len(idx)):
                    if d.iloc[j]["close"] > d.iloc[j]["sma5"]:
                        rows.append(trade(inst, "RSI 2", "RSI 2 · achat < 10 / sortie > SMA 5", idx[i], idx[j], 1,
                                          r["close"], d.iloc[j]["close"], r["atr"], nights(idx[i], idx[j])))
                        i = j
                        break
                else:
                    break
            i += 1
        # 3. Fin / début de mois
        months = pd.Series(idx, index=idx).groupby([pd.Index(idx).year, pd.Index(idx).month])
        mlist = [list(v) for _, v in months]
        for a, b in zip(mlist[:-1], mlist[1:]):
            if len(a) >= 2 and len(b) >= 3:
                t_in, t_out = a[-2], b[2]
                r = d.loc[t_in]
                if r["atr"] > 0:
                    rows.append(trade(inst, "Fin de mois", "Fin/début de mois · J-2 → J+3", t_in, t_out, 1,
                                      r["close"], d.loc[t_out]["close"], r["atr"], nights(t_in, t_out)))
        # 4. Nuit
        for a, b in zip(idx[:-1], idx[1:]):
            r = d.loc[a]
            if r["atr"] > 0 and (b - a).days <= 4:
                rows.append(trade(inst, "Nuit", "Nuit · clôture → ouverture", a, b, 1, r["close"], d.loc[b]["open"],
                                  r["atr"], nights(a, b)))

    if inst in ("XAUUSD", "NASDAQ100"):
        # 5. Cassure 20 jours
        for long_only in (False, True):
            reg = "Cassure 20 j · " + ("achats seuls" if long_only else "deux sens")
            pos, t_in, entry, risk = 0, None, None, None
            for k in idx:
                r = d.loc[k]
                if np.isnan(r["hh20"]):
                    continue
                if pos == 1 and r["close"] < r["ll10"] or pos == -1 and r["close"] > r["hh10"]:
                    rows.append(trade(inst, "Cassure 20 j", reg, t_in, k, pos, entry, r["close"], risk, nights(t_in, k)))
                    pos = 0
                if pos == 0:
                    if r["close"] > r["hh20"]:
                        pos, t_in, entry = 1, k, r["close"]
                        risk = entry - r["ll10"]
                    elif r["close"] < r["ll20"] and not long_only:
                        pos, t_in, entry = -1, k, r["close"]
                        risk = r["hh10"] - entry
                    if pos and risk <= 0:
                        pos = 0

    # 6. Inside day (intraday le lendemain)
    if inst in ("XAUUSD", "SP500", "NASDAQ100"):
        days = {k: g for k, g in df[(df["hm"] >= rth[0]) & (df["hm"] < rth[1])].groupby("day")}
        for a, b, c_ in zip(idx[:-2], idx[1:-1], idx[2:]):
            pa, pb = d.loc[a], d.loc[b]
            if not (pb["high"] < pa["high"] and pb["low"] > pa["low"]):
                continue
            g = days.get(c_)
            if g is None:
                continue
            up, dn = (g["high"] > pb["high"]).values, (g["low"] < pb["low"]).values
            hit = up | dn
            if not hit.any():
                continue
            j = hit.argmax()
            if up[j] and dn[j]:
                continue
            bar = g.iloc[j]
            dd = 1 if up[j] else -1
            entry = max(bar["open"], pb["high"]) if dd == 1 else min(bar["open"], pb["low"])
            stop = pb["low"] if dd == 1 else pb["high"]
            risk = (entry - stop) * dd
            if risk <= 0:
                continue
            if (dd == 1 and bar["low"] <= stop) or (dd == -1 and bar["high"] >= stop):
                px = stop
            else:
                rest = g[g["hm"] > bar["hm"]]
                if rest.empty:
                    continue
                px, _ = walk(rest, dd, stop)
            rows.append(trade(inst, "Inside day", "Inside day · cassure J+1, sortie clôture", c_, c_, dd, entry, px, risk, 0))
    return rows


def st(r):
    if len(r) == 0:
        return None
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    cum = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max())
    return {"trades": int(len(r)), "win_rate": float((r > 0).mean() * 100), "pf": float(pos / neg) if neg else None,
            "e_r": float(r.mean()), "resultat_eur": float(r.sum() * RISK_EUR), "max_dd_eur": dd * RISK_EUR}


def main(which):
    rows = []
    for inst in which:
        if inst in ("DAX", "CAC40", "EUROSTOXX50"):
            rows += orb_europe(inst)
        elif inst == "XAUUSD":
            rows += swing(inst, "America/New_York", (0, 1020), 600)     # jour de 00:00 à 17:00 New York
        else:
            rows += swing(inst, "America/New_York", (570, 960), 360)
    t = pd.DataFrame(rows)
    t = t[t["day"] >= "2020-01-01"]
    t["net_r"] = t["gross_r"] - t["cost_r"]
    t["net2_r"] = t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    tag = "_".join(which)
    t.to_csv(os.path.join(out, f"trades_{tag}.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (inst, reg), g in t.groupby(["instrument", "reglage"]):
        g = g.sort_values("exit_day")
        is_, oos = g[g["day"] < IS_END], g[g["day"] >= IS_END]
        r = {"instrument": inst, "reglage": reg, "brut": st(g["gross_r"].values), "net": st(g["net_r"].values),
             "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values),
             "oos_x2": float(oos["net2_r"].mean()) if len(oos) else None,
             "par_annee": {str(y): round(float(x["net_r"].mean()), 3) for y, x in g.groupby(g["day"].dt.year)}}
        r["valide"] = bool(r["is"] and r["oos"] and r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0
                           and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {inst:11} {reg:42} n{r['net']['trades']:>5} Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} "
              f"PF{r['net']['pf']:.2f} IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} "
              f"{r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€")
    with open(os.path.join(out, f"summary_{tag}.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
