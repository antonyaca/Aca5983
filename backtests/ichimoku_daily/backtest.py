"""Ichimoku journalier en portefeuille (suivi de tendance) — règles fixées avant le test.

Marchés : NASDAQ100, SP500, FTSE100, NIKKEI225, XAUUSD, XAGUSD, EURUSD, GBPUSD, USDJPY, AUDUSD (DAX et WTI exclus : données).
Barres journalières construites depuis le M1, journée de 17:00 à 17:00 heure de New York (convention des CFD / du forex).
Ichimoku 9/26/52 standard. Signal à la clôture, entrée à l'ouverture de la barre suivante.
Setups : 1. Croisement TK au-dessus (sous) du nuage. 2. Cassure du nuage (clôture sort du nuage, nuage futur dans le même sens,
Chikou libre). Deux sens. Stop initial : setup 1 = Kijun ∓ 0,25 ATR20 ; setup 2 = bord opposé du nuage ∓ 0,25 ATR20.
Sortie : clôture repasse sous (au-dessus de) la Kijun → sortie à l'ouverture suivante ; stop initial actif en intrajournalier.
Une position par marché et par setup. 100 € de risque par trade (positions simultanées possibles sur plusieurs marchés).
Coûts : spread + slippage aller-retour par marché ; swap par nuit calendaire : indices et métaux achat 6 %/an, vente 1 %/an
du nominal ; devises 2,5 %/an dans les deux sens (hypothèse moyenne).
Périodes : IS 2010-2017, OOS 2018-2026.
Critère (portefeuille, par setup) : E nette > 0 en IS et OOS, PF ≥ 1,10, OOS > 0 avec coûts doublés, t ≥ 2.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MARKETS = {  # coût aller-retour (unités de prix), type
    "NASDAQ100": (1.5, "indice"), "SP500": (0.75, "indice"), "FTSE100": (1.5, "indice"), "NIKKEI225": (12.0, "indice"),
    "XAUUSD": (0.47, "metal"), "XAGUSD": (0.04, "metal"),
    "EURUSD": (0.00015, "fx"), "GBPUSD": (0.0002, "fx"), "USDJPY": (0.02, "fx"), "AUDUSD": (0.00015, "fx"),
}
SWAP = {"indice": (0.06, 0.01), "metal": (0.06, 0.01), "fx": (0.025, 0.025)}
IS_END = pd.Timestamp("2018-01-01")


def daily(inst):
    files = sorted(glob.glob(os.path.join(ROOT, "data", inst, f"{inst}_M1_*.csv.gz")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates("time").sort_values("time")
    ny = df["time"].dt.tz_convert("America/New_York")
    # journée de trading = date New York décalée de 7 h (17:00 → minuit)
    df["d"] = (ny + pd.Timedelta(hours=7)).dt.tz_localize(None).dt.normalize()
    g = df.groupby("d")
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "n": g["open"].count()})
    b = b[(b.index.dayofweek < 5) & (b["n"] >= 300)]
    return b


def ichimoku(b):
    h, l, c = b["high"], b["low"], b["close"]
    mid = lambda n: (h.rolling(n).max() + l.rolling(n).min()) / 2
    x = pd.DataFrame(index=b.index)
    x["t"], x["k"] = mid(9), mid(26)
    ssa, ssb = (x["t"] + x["k"]) / 2, mid(52)
    x["top"], x["bot"] = np.maximum(ssa.shift(26), ssb.shift(26)), np.minimum(ssa.shift(26), ssb.shift(26))
    x["fut_up"], x["fut_dn"] = ssa > ssb, ssa < ssb
    x["chik_up"], x["chik_dn"] = c > h.shift(26), c < l.shift(26)
    pc = c.shift(1)
    x["atr"] = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1).rolling(20).mean()
    return x


def simulate(inst, b, x):
    cost, kind = MARKETS[inst]
    sl_long, sl_short = SWAP[kind]
    O, H, L, C = (b[c].values for c in ("open", "high", "low", "close"))
    T = b.index
    t, k, top, bot, atr = (x[c].values for c in ("t", "k", "top", "bot", "atr"))
    above, below = C > top, C < bot
    prev = lambda a: np.r_[np.nan, a[:-1]]
    sig = {
        "Croisement TK": ((t > k) & (prev(t) <= prev(k)) & above, (t < k) & (prev(t) >= prev(k)) & below,
                          k - 0.25 * atr, k + 0.25 * atr),
        "Cassure du nuage": (above & (prev(C) <= prev(top)) & x["fut_up"].values & x["chik_up"].values,
                             below & (prev(C) >= prev(bot)) & x["fut_dn"].values & x["chik_dn"].values,
                             bot - 0.25 * atr, top + 0.25 * atr),
    }
    rows = []
    for name, (lg, sh, stl, sts) in sig.items():
        i, n = 80, len(C)
        while i < n - 1:
            d = 1 if lg[i] else (-1 if sh[i] else 0)
            if d == 0:
                i += 1; continue
            stop = stl[i] if d == 1 else sts[i]
            e = i + 1
            entry = O[e]
            risk = (entry - stop) * d
            if not np.isfinite(risk) or risk <= 0:
                i += 1; continue
            j, px = e, None
            while j < n:
                if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                    px = O[j] if (j > e and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop; break
                if j + 1 < n and ((C[j] < k[j]) if d == 1 else (C[j] > k[j])):
                    j += 1; px = O[j]; break
                j += 1
            if px is None:
                break
            nights = (T[j] - T[e]).days
            swap = entry * (sl_long if d == 1 else sl_short) * nights / 360
            rows.append((inst, name, T[e], T[j], d, risk, nights, (px - entry) * d / risk, (cost + swap) / risk))
            i = j
    return rows


def st(r):
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    cum = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max())
    return {"trades": int(len(r)), "win_rate": float((r > 0).mean() * 100), "pf": float(pos / neg) if neg else None,
            "e_r": float(r.mean()), "resultat_eur": float(r.sum() * 100), "max_dd_eur": dd * 100}


def main():
    rows, cover = [], {}
    for inst in MARKETS:
        b = daily(inst)
        cover[inst] = (str(b.index.min().date()), str(b.index.max().date()), len(b))
        rows += simulate(inst, b, ichimoku(b))
    print("couverture (début, fin, séances) :", json.dumps(cover, ensure_ascii=False))
    t = pd.DataFrame(rows, columns=["instrument", "setup", "t_in", "t_out", "d", "risque", "nuits", "gross_r", "cost_r"])
    t["net_r"], t["net2_r"] = t["gross_r"] - t["cost_r"], t["gross_r"] - 2 * t["cost_r"]
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    t.to_csv(os.path.join(out, "trades.csv.gz"), index=False, float_format="%.6f")
    res = {}
    for setup, g in t.groupby("setup"):
        g = g.sort_values("t_out")
        is_, oos = g[g["t_in"] < IS_END], g[g["t_in"] >= IS_END]
        x = g["net_r"]
        daily_pnl = g.groupby("t_out")["net_r"].sum().sort_index()
        cum = daily_pnl.cumsum()
        r = {"total": st(x.values), "brut": st(g["gross_r"].values), "is": st(is_["net_r"].values), "oos": st(oos["net_r"].values),
             "oos_x2": float(oos["net2_r"].mean()), "t_stat": float(x.mean() / x.std() * np.sqrt(len(x))),
             "dd_portefeuille_eur": float((cum.cummax().clip(lower=0) - cum).max() * 100),
             "sans_top10": float(x.drop(x.nlargest(10).index).mean()),
             "achats_e": float(g[g["d"] == 1]["net_r"].mean()), "ventes_e": float(g[g["d"] == -1]["net_r"].mean()),
             "par_marche": {m: [int(len(v)), round(float(v["net_r"].mean()), 3), round(float(v["net_r"].sum() * 100))] for m, v in g.groupby("instrument")},
             "par_annee": {str(y): round(float(v["net_r"].sum() * 100)) for y, v in g.groupby(g["t_out"].dt.year)}}
        r["valide"] = bool(r["is"]["e_r"] > 0 and r["oos"]["e_r"] > 0 and (r["total"]["pf"] or 0) >= 1.10 and r["oos_x2"] > 0 and r["t_stat"] >= 2)
        res[setup] = r
        print(f"\n{'✔' if r['valide'] else '✘'} {setup} : {r['total']['trades']} trades, brut {r['brut']['e_r']:+.3f} R, net {r['total']['e_r']:+.3f} R, "
              f"PF {r['total']['pf']:.2f}, IS {r['is']['e_r']:+.3f} ({r['is']['trades']}), OOS {r['oos']['e_r']:+.3f} ({r['oos']['trades']}), "
              f"frais x2 OOS {r['oos_x2']:+.3f}, t {r['t_stat']:+.2f}, total {r['total']['resultat_eur']:,.0f} €, DD portefeuille "
              f"{r['dd_portefeuille_eur']:,.0f} €, sans top 10 {r['sans_top10']:+.3f}, achats {r['achats_e']:+.3f} / ventes {r['ventes_e']:+.3f}")
        print("   par marché [trades, E nette, €] :", r["par_marche"])
        print("   par année (€) :", r["par_annee"])
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump({"couverture": cover, "resultats": res}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
