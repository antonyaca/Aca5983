"""Flèches de l'indicateur JustUncleL (captures d'Anto, or M1, 18/10/2026) avec stop au dernier plus haut / plus bas.
Règles fixées AVANT calcul.

Signal : alerte BUY/SELL du script (fonction signals() de ../scalp_pullback/run.py, Heikin Ashi activé comme par défaut).
Stop : vente = dernier plus haut de fractale CONFIRMÉE (fractale « BW » du script, triangle rouge, connue 2 bougies
après le sommet) ; achat = dernier plus bas de fractale confirmée. Pas de trade si le stop n'est pas au-delà de l'entrée.
Entrée : ouverture réelle de la bougie suivant la flèche. Sorties : A = 1 R, B = 2 R, C = fin de l'état du script
(haC repasse la ligne centrale du PAC) à l'ouverture suivante. Stop prioritaire. Frais lib.COST déduits. 100 € par R.
Heures de Paris : entrées 09:00-20:00 (Londres + US), sortie forcée 22:00. Un trade à la fois par marché/réglage.
Marchés : XAUUSD, NASDAQ100, SP500, EURUSD. Unité principale : M1 (demandée). Analyse statistique ensuite :
M5, M15, H1 (mêmes règles), et découpages du M1 (heure, taille du stop / frais, sens), fixés avant lecture,
jugés sur découverte 2011-2018 PUIS confirmés sur 2019-2026.
"""
import importlib.util, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(HERE)
sys.path.insert(0, CAMP)
import lib  # noqa
_s = importlib.util.spec_from_file_location("sp", os.path.join(CAMP, "scalp_pullback", "run.py"))
sp = importlib.util.module_from_spec(_s); _s.loader.exec_module(sp)
MARKETS = ["XAUUSD", "NASDAQ100", "SP500", "EURUSD"]
T0, T1, TC = 540, 1200, 1320


def fractals(H, L):
    """Dernier sommet / creux de fractale BW confirmé, connu à la clôture de la bougie i (centre en i-2)."""
    h4, h3, h2, h1, h0 = H[:-4], H[1:-3], H[2:-2], H[3:-1], H[4:]
    top = np.r_[[False] * 4, (h4 < h2) & (h3 <= h2) & (h2 >= h1) & (h2 > h0)]
    l4, l3, l2, l1, l0 = L[:-4], L[1:-3], L[2:-2], L[3:-1], L[4:]
    bot = np.r_[[False] * 4, (l4 > l2) & (l3 >= l2) & (l2 <= l1) & (l2 < l0)]
    lt = pd.Series(np.where(top, np.r_[np.nan, np.nan, H[:-2]], np.nan)).ffill().values
    lb = pd.Series(np.where(bot, np.r_[np.nan, np.nan, L[:-2]], np.nan)).ffill().values
    return lt, lb


def bars(inst, tf):
    df = lib.load(inst)
    s = df.set_index("time")[["open", "high", "low", "close"]]
    if tf == 1:
        return s
    return s.resample(f"{tf}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def simulate(inst, b, tf):
    loc = b.index.tz_convert("Europe/Paris")
    hm = (loc.hour * 60 + loc.minute).values
    day = loc.tz_localize(None).normalize().values
    O, H, L, C = (b[c].values for c in ("open", "high", "low", "close"))
    sig, td, _, _ = sp.signals(b)
    lt, lb = fractals(H, L)
    n = len(O); cost = lib.COST[inst]
    # fin de journée (22:00 Paris) pour chaque bougie
    dchg = np.r_[np.flatnonzero(day[1:] != day[:-1]) + 1, n]
    dayend = np.repeat(dchg, np.diff(np.r_[0, dchg]))
    cut = dayend.copy()
    for a, z in zip(np.r_[0, dchg[:-1]], dchg):
        cut[a:z] = a + np.searchsorted(hm[a:z], TC)
    rows = []
    cand = np.flatnonzero(sig != 0)
    for ex in ("A 1R", "B 2R", "C fin PAC"):
        busy = -1
        for i in cand:
            e = i + 1; end = cut[i]
            if e <= busy or e >= end or not (T0 <= hm[e] < T1):
                continue
            d = int(sig[i]); stop = lb[i] if d == 1 else lt[i]
            entry = O[e]; risk = (entry - stop) * d
            if not np.isfinite(risk) or risk <= 0:
                continue
            hs, ls, os_ = H[e:end], L[e:end], O[e:end]
            m = len(hs)
            hit_s = (ls <= stop) if d == 1 else (hs >= stop)
            ks = int(np.argmax(hit_s)) if hit_s.any() else m
            if ex == "C fin PAC":
                z = np.flatnonzero(td[e:end] == 0)
                kx = int(z[0]) + 1 if len(z) else m          # sortie à l'ouverture suivante
                kt = m
            else:
                tp = entry + d * risk * (1 if ex == "A 1R" else 2)
                hit_t = (hs >= tp) if d == 1 else (ls <= tp)
                kt = int(np.argmax(hit_t)) if hit_t.any() else m
                kx = m
            k = min(ks, kt, kx)
            if k >= m:
                px, k = C[end - 1], m - 1
            elif k == ks:
                px = os_[k] if (k > 0 and ((os_[k] < stop) if d == 1 else (os_[k] > stop))) else stop
            elif k == kt:
                px = os_[k] if (k > 0 and ((os_[k] > tp) if d == 1 else (os_[k] < tp))) else tp
            else:
                px = os_[k]
            busy = e + k
            rows.append({"instrument": inst, "tf": f"M{tf}" if tf < 60 else "H1", "sortie": ex, "day": pd.Timestamp(day[e]),
                         "hm": int(hm[e]), "d": d, "risque": risk, "gross_r": (px - entry) * d / risk, "cost_r": cost / risk})
    return rows


def main():
    rows = []
    for inst in MARKETS:
        for tf in (1, 5, 15, 60):
            rows += simulate(inst, bars(inst, tf), tf)
        print(inst, "ok", flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (tf, ex), g in t.groupby(["tf", "sortie"]):
        for inst, gi in [("4 marchés", g)] + list(g.groupby("instrument")):
            r = lib.evaluate(gi, f"{tf} {ex} {inst}"); r["brut"] = float(gi.gross_r.mean())
            r["cout_median_r"] = float(gi.cost_r.median()); res.append(r)
            print(lib.line(r), f"brut {gi.gross_r.mean():+.3f} coût méd {gi.cost_r.median():.2f}R")
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
