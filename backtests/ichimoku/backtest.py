"""Ichimoku (9/26/52) — positions de plusieurs jours autorisées. Règles et critère fixés avant le test.

Marchés : NASDAQ100, SP500, DAX, XAUUSD, EURUSD. Unités de temps : M15, H1, H4 (barres UTC continues).
Calculs : Tenkan = milieu 9 barres, Kijun = milieu 26, SSA = (Tenkan+Kijun)/2, SSB = milieu 52 ; nuage courant = SSA/SSB
décalés de 26 barres ; nuage futur = SSA/SSB non décalés ; Chikou libre = clôture > plus haut d'il y a 26 barres (achat).
ATR = ATR 14 barres de l'unité de temps. Tampon des stops = 0,25 ATR.

Setups (achat ; vente symétrique) — signal à la clôture, entrée à l'ouverture de la barre suivante :
 1. Croisement TK : Tenkan croise au-dessus de la Kijun, clôture au-dessus du nuage. Stop = Kijun − tampon.
 2. Cassure du nuage : clôture passe au-dessus du nuage, nuage futur haussier, Chikou libre. Stop = bas du nuage − tampon.
 3. Pullback Kijun : clôture au-dessus du nuage, plus bas ≤ Kijun < clôture, clôture précédente au-dessus de sa Kijun.
    Stop = plus bas des 3 dernières barres − tampon.
 4. Cinq conditions : au-dessus du nuage, Tenkan > Kijun, Chikou libre, nuage futur haussier, clôture > plus haut des
    10 barres précédentes. Stop = Kijun − tampon.
Sorties : « Kijun » = stop initial + sortie à l'ouverture suivante dès qu'une clôture repasse sous la Kijun ;
          « TP 1:2 » = stop initial + objectif à 2 R.
Une position à la fois par variante. Si l'ouverture d'entrée est déjà au-delà du stop : pas de trade.
Si stop et objectif sont touchés dans la même barre : stop (prudent). Gap au-delà d'un niveau : sortie à l'ouverture.
Coûts : spread + slippage + commission aller-retour, plus swap par nuit calendaire (achat 6 %/an, vente 1 %/an du nominal).
Critère : E nette > 0 en IS (entrées 2020-2023) et en OOS (2024+), PF net ≥ 1,10, E nette OOS > 0 avec coûts doublés.
100 € par R, capital 10 000 €.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
COST = {"XAUUSD": 0.47, "EURUSD": 0.00015, "SP500": 0.75, "NASDAQ100": 1.5, "DAX": 1.5}
SWAP_LONG, SWAP_SHORT = 0.06, 0.01
IS_END = pd.Timestamp("2024-01-01", tz="UTC")
TFS = {"M15": "15min", "H1": "1h", "H4": "4h"}
SETUPS = {1: "Croisement TK", 2: "Cassure du nuage", 3: "Pullback Kijun", 4: "Cinq conditions"}


def load(inst):
    files = sorted(glob.glob(os.path.join(ROOT, "data", inst, f"{inst}_M1_*.csv.gz")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    return df.drop_duplicates("time").sort_values("time").set_index("time")


def bars(m1, rule):
    b = m1.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return b[b.index >= "2019-06-01"]


def mid(h, l, n):
    return (h.rolling(n).max() + l.rolling(n).min()) / 2


def indicators(b):
    h, l, c = b["high"], b["low"], b["close"]
    x = pd.DataFrame(index=b.index)
    x["tenkan"], x["kijun"] = mid(h, l, 9), mid(h, l, 26)
    ssa, ssb = (x["tenkan"] + x["kijun"]) / 2, mid(h, l, 52)
    x["fut_bull"], x["fut_bear"] = ssa > ssb, ssa < ssb
    a26, b26 = ssa.shift(26), ssb.shift(26)
    x["top"], x["bot"] = np.maximum(a26, b26), np.minimum(a26, b26)
    x["chik_up"], x["chik_dn"] = c > h.shift(26), c < l.shift(26)
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    x["atr"] = tr.rolling(14).mean()
    x["hh10"], x["ll10"] = h.shift(1).rolling(10).max(), l.shift(1).rolling(10).min()
    x["ll3"], x["hh3"] = l.rolling(3).min(), h.rolling(3).max()
    return x


def signals(b, x):
    """Renvoie {setup: (sig_long, sig_short, stop_long, stop_short)} en tableaux numpy."""
    c, h, l = b["close"], b["high"], b["low"]
    t, k, buf = x["tenkan"], x["kijun"], 0.25 * x["atr"]
    above, below = c > x["top"], c < x["bot"]
    out = {}
    cu = (t > k) & (t.shift(1) <= k.shift(1)); cd = (t < k) & (t.shift(1) >= k.shift(1))
    out[1] = (cu & above, cd & below, k - buf, k + buf)
    bu = above & (c.shift(1) <= x["top"].shift(1)) & x["fut_bull"] & x["chik_up"]
    bd = below & (c.shift(1) >= x["bot"].shift(1)) & x["fut_bear"] & x["chik_dn"]
    out[2] = (bu, bd, x["bot"] - buf, x["top"] + buf)
    pu = above & (l <= k) & (c > k) & (c.shift(1) > k.shift(1))
    pd_ = below & (h >= k) & (c < k) & (c.shift(1) < k.shift(1))
    out[3] = (pu, pd_, x["ll3"] - buf, x["hh3"] + buf)
    fu = above & (t > k) & x["chik_up"] & x["fut_bull"] & (c > x["hh10"])
    fd = below & (t < k) & x["chik_dn"] & x["fut_bear"] & (c < x["ll10"])
    out[4] = (fu, fd, k - buf, k + buf)
    return {s: tuple(np.nan_to_num(v.values.astype(float), nan=0.0) if v.dtype == bool else v.values for v in vals)
            for s, vals in out.items()}


def simulate(b, x, sig, exit_mode, inst):
    O, H, L, C = (b[c].values for c in ("open", "high", "low", "close"))
    K = x["kijun"].values
    T = b.index
    sl_, ss_, stl, sts = sig
    n = len(O)
    rows = []
    i = 60
    while i < n - 1:
        d = 1 if sl_[i] else (-1 if ss_[i] else 0)
        if d == 0:
            i += 1
            continue
        stop = stl[i] if d == 1 else sts[i]
        e = i + 1
        entry = O[e]
        risk = (entry - stop) * d
        if not np.isfinite(risk) or risk <= 0:
            i += 1
            continue
        tp = entry + 2 * d * risk if exit_mode == "TP 1:2" else None
        px, j = None, e
        while j < n:
            if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                px = O[j] if (j > e and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop
                break
            if tp is not None and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
                px = O[j] if (j > e and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp
                break
            if tp is None and j + 1 < n and ((C[j] < K[j]) if d == 1 else (C[j] > K[j])):
                j += 1
                px = O[j]
                break
            j += 1
        if px is None:
            break
        nights = (T[j].normalize() - T[e].normalize()).days
        swap = entry * (SWAP_LONG if d == 1 else SWAP_SHORT) * nights / 360
        rows.append((T[e], T[j], d, entry, px, risk, nights, (px - entry) * d / risk, (COST[inst] + swap) / risk))
        i = j
    return rows


def st(r):
    if len(r) == 0:
        return None
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    cum = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max())
    s = b = 0
    for v in r:
        s = s + 1 if v < 0 else 0
        b = max(b, s)
    return {"trades": int(len(r)), "win_rate": float((r > 0).mean() * 100), "pf": float(pos / neg) if neg else None,
            "e_r": float(r.mean()), "resultat_eur": float(r.sum() * 100), "max_dd_eur": dd * 100, "pire_serie": b}


def main():
    allt = []
    for inst in COST:
        m1 = load(inst)
        for tf, rule in TFS.items():
            b = bars(m1, rule)
            x = indicators(b)
            sigs = signals(b, x)
            for s, sig in sigs.items():
                for ex in ("Kijun", "TP 1:2"):
                    rows = simulate(b, x, sig, ex, inst)
                    t = pd.DataFrame(rows, columns=["t_in", "t_out", "d", "entry", "exit", "risque", "nuits", "gross_r", "cost_r"])
                    t["instrument"], t["tf"], t["setup"], t["sortie"] = inst, tf, SETUPS[s], ex
                    allt.append(t)
        print("ok", inst, flush=True)
    t = pd.concat(allt)
    t = t[t["t_in"] >= pd.Timestamp("2020-01-01", tz="UTC")]
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for key, g in t.groupby(["instrument", "tf", "setup", "sortie"]):
        g = g.sort_values("t_out")
        is_, oos = g[g["t_in"] < IS_END], g[g["t_in"] >= IS_END]
        x = g["net_r"]
        r = {"instrument": key[0], "tf": key[1], "setup": key[2], "sortie": key[3],
             "brut": st(g["gross_r"].values), "net": st(x.values), "is": st(is_["net_r"].values),
             "oos": st(oos["net_r"].values), "oos_x2": float(oos["net2_r"].mean()) if len(oos) else None,
             "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 2 else 0.0,
             "achats_e": float(g[g["d"] == 1]["net_r"].mean()), "ventes_e": float(g[g["d"] == -1]["net_r"].mean()),
             "nuits_moy": float(g["nuits"].mean()),
             "par_annee": {str(y): round(float(v["net_r"].mean()), 3) for y, v in g.groupby(g["t_in"].dt.year)}}
        r["valide"] = bool(r["is"] and r["oos"] and r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0
                           and (r["net"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0)
        res.append(r)
    res.sort(key=lambda r: -r["net"]["e_r"])
    for r in res:
        print(f"{'✔' if r['valide'] else ' '} {r['instrument']:9} {r['tf']:3} {r['setup']:17} {r['sortie']:6} n{r['net']['trades']:>5} "
              f"WR{r['net']['win_rate']:5.1f} Eb{r['brut']['e_r']:+.3f} En{r['net']['e_r']:+.3f} PF{(r['net']['pf'] or 0):.2f} "
              f"IS{r['is']['e_r'] if r['is'] else 0:+.3f} OOS{r['oos']['e_r'] if r['oos'] else 0:+.3f} x2{(r['oos_x2'] or 0):+.3f} "
              f"t{r['t_stat']:+.2f} {r['net']['resultat_eur']:>7.0f}€ DD{r['net']['max_dd_eur']:>6.0f}€ "
              f"A{r['achats_e']:+.2f} V{r['ventes_e']:+.2f} nuits{r['nuits_moy']:.1f}")
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
