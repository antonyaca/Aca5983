"""Fibonacci OTE — retracement dans la zone 61,8-78,6 % après une impulsion. Règles fixées avant le test.

Impulsion : jambe entre deux swings alternés (fractales 2 bougies de chaque côté) en M5 ou M15,
            d'amplitude ≥ 0,3 ATR journalier (M5) ou ≥ 0,5 ATR (M15). Active dès la confirmation du swing final.
Entrée    : ordre limite au retracement 61,8 % dans le sens de l'impulsion (achat après une impulsion haussière).
            Valable 4 h ; annulé si le prix dépasse l'extrême de l'impulsion avant d'être rempli.
Stop      : au-delà du 78,6 % + spread.
Objectif  : « ext −0,5 » = extrême + 50 % de l'impulsion (RR ≈ 6,6) ; « retour à l'extrême » = niveau 0 % (RR ≈ 3,7).
Gestion   : une position à la fois ; arrêt pour la journée dès qu'un trade finit positif ; 2 trades maximum par jour.
            Sortie forcée en fin de fenêtre horaire.
Horaires  : « séance » = or et EURUSD 08:00-17:00 Londres, Nasdaq et S&P 500 09:30-16:00 New York, DAX 09:00-17:30 Paris ;
            « 24 h » = toute la journée (heure locale du marché), sortie forcée à 23:55.
Coûts     : spread + slippage + commission aller-retour (comme les lots précédents), déduits en R. 100 € par R.
Critère   : E nette > 0 en IS (2020-2023) et OOS (2024+), PF ≥ 1,10, OOS > 0 avec frais doublés.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "batch3"))
from strategies import load_m1, IS_END, st  # noqa: E402

MARKETS = {  # tz, séance (début, fin) en minutes locales, spread (marge du stop), coût aller-retour total
    "XAUUSD":    ("Europe/London",    (480, 1020), 0.30,    0.47),
    "EURUSD":    ("Europe/London",    (480, 1020), 0.00006, 0.00015),
    "NASDAQ100": ("America/New_York", (570, 960),  1.0,     1.5),
    "SP500":     ("America/New_York", (570, 960),  0.5,     0.75),
    "DAX":       ("Europe/Paris",     (540, 1050), 1.0,     1.5),
}
TFS = {"M5": (5, 0.3), "M15": (15, 0.5)}
VALID_MIN = 240


def prepare(inst):
    tz, sess, spread, cost = MARKETS[inst]
    df = load_m1(inst, tz)
    df["tmin"] = (df["time"].astype("int64") // 60_000_000_000).astype(np.int64)
    # ATR journalier (journée locale complète), jours précédents uniquement
    g = df.groupby("day")
    d = pd.DataFrame({"h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last()})
    d = d[d.index.dayofweek < 5]
    pc = d["c"].shift(1)
    tr = pd.concat([d["h"] - d["l"], (d["h"] - pc).abs(), (d["l"] - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)
    df["atr"] = df["day"].map(atr)
    return df


def swings(bars):
    H, L = bars["high"].values, bars["low"].values
    n = len(H)
    fh = np.zeros(n, bool); fl = np.zeros(n, bool)
    fh[2:-2] = (H[2:-2] > H[1:-3]) & (H[2:-2] > H[:-4]) & (H[2:-2] >= H[3:-1]) & (H[2:-2] >= H[4:])
    fl[2:-2] = (L[2:-2] < L[1:-3]) & (L[2:-2] < L[:-4]) & (L[2:-2] <= L[3:-1]) & (L[2:-2] <= L[4:])
    piv = []                                    # (index, type, prix) alternés, extrême gardé si répétition
    for i in range(n):
        for typ, ok, px in ((1, fh[i], H[i]), (-1, fl[i], L[i])):
            if not ok:
                continue
            if piv and piv[-1][1] == typ:
                if (typ == 1 and px > piv[-1][2]) or (typ == -1 and px < piv[-1][2]):
                    piv[-1] = (i, typ, px)
            else:
                piv.append((i, typ, px))
    return piv


def candidates(inst, df, tf, horaires):
    tz, sess, spread, cost = MARKETS[inst]
    step, kmin = TFS[tf]
    win = sess if horaires == "séance" else (0, 1435)
    b = df.set_index("time").resample(f"{step}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "tmin": "first"}).dropna().reset_index()
    piv = swings(b)
    bt = b["tmin"].values.astype(np.int64)
    t1 = df["tmin"].values; H1, L1, O1, C1 = df["high"].values, df["low"].values, df["open"].values, df["close"].values
    hm1 = df["hm"].values; day1 = df["day"].values; atr1 = df["atr"].values
    rows = []
    n1 = len(t1)
    inwin = (hm1 >= win[0]) & (hm1 < win[1] - 60)
    # pour chaque minute : indice de la 1re minute suivante hors fenêtre (changement de jour ou fin de séance)
    stop_cond = np.r_[False, day1[1:] != day1[:-1]] | (hm1 >= win[1])
    idx = np.where(stop_cond, np.arange(n1), n1)
    next_stop = np.minimum.accumulate(idx[::-1])[::-1]
    for (ia, ta, pa), (ib, tb, pb) in zip(piv[:-1], piv[1:]):
        d = 1 if tb == 1 else -1
        size = (pb - pa) * d
        act_bar = ib + 2
        if act_bar + 1 >= len(bt):
            continue
        start = int(np.searchsorted(t1, bt[act_bar] + step))
        if start >= n1 or np.isnan(atr1[start]) or size < kmin * atr1[start]:
            continue
        entry = pb - d * 0.618 * size
        stop = pb - d * 0.786 * size - d * spread
        stop_ = int(np.searchsorted(t1, t1[start] + VALID_MIN, side="right"))
        h, l = H1[start:stop_], L1[start:stop_]
        cancel = (h > pb) if d == 1 else (l < pb)
        hit = ((l <= entry) if d == 1 else (h >= entry)) & inwin[start:stop_]
        if not hit.any():
            continue
        f = int(hit.argmax())
        if cancel.any() and int(cancel.argmax()) <= f:
            continue
        k = start + f
        fill = min(O1[k], entry) if d == 1 else max(O1[k], entry)
        risk_f = (fill - stop) * d
        if risk_f <= 0:
            continue
        e = int(next_stop[k + 1]) if k + 1 < n1 else n1
        for name, tp in (("ext −0,5", pb + d * 0.5 * size), ("retour à l'extrême", pb)):
            if (L1[k] <= stop) if d == 1 else (H1[k] >= stop):
                px, kx = stop, k
            else:
                hh, ll, oo = H1[k + 1:e], L1[k + 1:e], O1[k + 1:e]
                sl = (ll <= stop) if d == 1 else (hh >= stop)
                tpm = (hh >= tp) if d == 1 else (ll <= tp)
                i_sl = int(sl.argmax()) if sl.any() else 10 ** 9
                i_tp = int(tpm.argmax()) if tpm.any() else 10 ** 9
                if i_sl == 10 ** 9 and i_tp == 10 ** 9:
                    if e - 1 <= k:
                        continue
                    px, kx = C1[e - 1], e - 1
                elif i_sl <= i_tp:
                    o = oo[i_sl]
                    px, kx = (o if ((o < stop) if d == 1 else (o > stop)) else stop), k + 1 + i_sl
                else:
                    o = oo[i_tp]
                    px, kx = (o if ((o > tp) if d == 1 else (o < tp)) else tp), k + 1 + i_tp
            rows.append({"instrument": inst, "tf": tf, "horaires": horaires, "objectif": name,
                         "day": pd.Timestamp(day1[k]), "t_in": t1[k], "t_out": t1[kx], "d": d,
                         "gross_r": (px - fill) * d / risk_f, "cost_r": cost / risk_f})
    return rows


def daily_rule(t):
    """Une position à la fois ; stop après un trade positif ; 2 trades max par jour."""
    keep = []
    for _, g in t.sort_values("t_in").groupby("day"):
        last_out, n, won = -1, 0, False
        for r in g.itertuples():
            if won or n >= 2:
                break
            if r.t_in < last_out:
                continue
            keep.append(r.Index)
            n += 1
            last_out = r.t_out
            if r.gross_r - r.cost_r > 0:
                won = True
    return t.loc[keep]


def build(inst, tf):
    """Calcule les trades candidats d'un marché / unité de temps et les enregistre."""
    df = prepare(inst)
    rows = []
    for horaires in ("séance", "24 h"):
        rows += candidates(inst, df, tf, horaires)
    out = os.path.join(HERE, "results", "raw"); os.makedirs(out, exist_ok=True)
    pd.DataFrame(rows).to_pickle(os.path.join(out, f"{inst}_{tf}.pkl"))
    print("ok", inst, tf, len(rows), flush=True)


def main():
    import glob
    raw = pd.concat([pd.read_pickle(f) for f in sorted(glob.glob(os.path.join(HERE, "results", "raw", "*.pkl")))])
    raw = raw[raw["day"] >= "2020-01-01"]
    raw["net_r"] = raw["gross_r"] - raw["cost_r"]
    raw["net2_r"] = raw["gross_r"] - 2 * raw["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    res, sel = [], []
    for key, g in raw.groupby(["instrument", "tf", "horaires", "objectif"]):
        t = daily_rule(g)
        sel.append(t)
        is_, oos = t[t["day"] < IS_END], t[t["day"] >= IS_END]
        x = t["net_r"]
        r = {"instrument": key[0], "tf": key[1], "horaires": key[2], "objectif": key[3],
             "brut": st(t["gross_r"].values), "net": st(x.values), "is": st(is_["net_r"].values),
             "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()),
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))), "candidats_sans_regle": int(len(g)),
             "sans_regle_e_net": float(g["net_r"].mean())}
        r["valide"] = bool(r["is"] and r["oos"] and r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0
                           and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
        print(f"{'✔' if r['valide'] else ' '} {key[0]:9} {key[1]:3} {key[2]:6} {key[3]:18} n{r['net']['trades']:>5} "
              f"WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} PF{r['net']['pf']:.2f} "
              f"IS{r['is']['e_r']:+.3f} OOS{r['oos']['e_r']:+.3f} x2{r['oos_x2']:+.3f} t{r['t_stat']:+.2f} "
              f"{r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€ | sans règle E{r['sans_regle_e_net']:+.3f}")
    pd.concat(sel).to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.5f")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        build(sys.argv[1], sys.argv[2])
    else:
        main()
