"""Réintégration M1 dans la tendance (idée d'Anto, 17/10/2026). Règles fixées AVANT tout calcul.

Marchés : XAUUSD, NASDAQ100, SP500, EURUSD. Bougies M1 réelles (pas de Heikin Ashi), indicateurs en continu.
Moyennes (celles de l'outil JustUncleL) : EMA34(clôture), EMA89, EMA200 ; canal pacL = EMA34(bas), pacU = EMA34(haut).
Tendance : verte si EMA89 > EMA200 et pacL > EMA200 → achats seulement ; rouge si EMA89 < EMA200 et pacU < EMA200 → ventes.
Signal achat (vert) : clôture > max(EMA34, EMA89, EMA200) alors que la clôture précédente ne l'était pas (réintégration).
Vente : miroir (clôture < min des 3, précédente non).
Trade : entrée à l'ouverture de la minute suivante ; stop = bas (haut) de la bougie signal ; objectif = 1 R ;
stop prioritaire dans la minute ; coûts lib.COST aller-retour (spread + slippage) déduits ; 100 € par R.
Heures de Paris : session Londres = entrées 09:00-12:59 ; session US = entrées à partir de 15:30 ;
aucune entrée après 20:00 ; position encore ouverte à 22:00 fermée au prix du marché. Un trade à la fois.
Gestion du jour (4 trades max) :
 A « stop si Londres gagne » : 1er signal Londres ; s'il est positif → fin de journée. Sinon 1er signal US (≥ 15:30),
   puis tant que le résultat du jour ≤ 0 : signal suivant, jusqu'à 4 trades ou 20:00.
 B « toujours 2 trades » : 1er signal Londres + 1er signal US ; puis tant que le jour ≤ 0 : signal suivant (4 max, 20:00).
 C « 2 trades seulement » (référence) : 1er signal Londres + 1er signal US, rien d'autre.
 D « tous les signaux » (diagnostic du signal brut) : chaque signal dans les deux sessions, un trade à la fois, sans gestion.
Critère : lib.evaluate (trades) + statistiques journalières (jours positifs, pire jour, € par an, drawdown).
"""
import json, os, sys
import numpy as np, pandas as pd
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import lib  # noqa
MARKETS = ["XAUUSD", "NASDAQ100", "SP500", "EURUSD"]
LON = (540, 780); US0, LAST, CLOSE = 930, 1200, 1320; MAXT = 4


def ema(x, n):
    a = 2 / (n + 1)
    return lfilter([a], [1, -(1 - a)], x, zi=[x[0] * (1 - a)])[0]


def prepare(inst):
    df = lib.load(inst, "Europe/Paris")
    O, H, L, C = (df[c].values for c in ("open", "high", "low", "close"))
    e34, e89, e200 = ema(C, 34), ema(C, 89), ema(C, 200)
    pl, pu = ema(L, 34), ema(H, 34)
    green = (e89 > e200) & (pl > e200); red = (e89 < e200) & (pu < e200)
    hi3, lo3 = np.maximum.reduce([e34, e89, e200]), np.minimum.reduce([e34, e89, e200])
    ab, be = C > hi3, C < lo3
    sig = np.zeros(len(C), np.int8)
    sig[1:][(green[1:] & ab[1:] & ~ab[:-1])] = 1
    sig[1:][(red[1:] & be[1:] & ~be[:-1])] = -1
    return df["day"].values, df["hm"].values, O, H, L, C, sig


def trade(i, d, O, H, L, C, hm, end):
    """Signal en i ; entrée i+1. end = index exclu de fin de journée (22:00). Retourne (sortie_idx, gross_r, risque)."""
    e = i + 1
    if e >= end:
        return None
    stop = L[i] if d == 1 else H[i]
    entry = O[e]; risk = (entry - stop) * d
    if risk <= 0:
        return None
    tp = entry + d * risk
    hs, ls, os_ = H[e:end], L[e:end], O[e:end]
    hit_s = (ls <= stop) if d == 1 else (hs >= stop)
    hit_t = (hs >= tp) if d == 1 else (ls <= tp)
    ks = np.argmax(hit_s) if hit_s.any() else len(hs); kt = np.argmax(hit_t) if hit_t.any() else len(hs)
    if ks == len(hs) and kt == len(hs):
        return end - 1, (C[end - 1] - entry) * d / risk, risk, entry
    if ks <= kt:
        px = os_[ks] if (ks > 0 and ((os_[ks] < stop) if d == 1 else (os_[ks] > stop))) else stop
        return e + ks, (px - entry) * d / risk, risk, entry
    px = os_[kt] if (kt > 0 and ((os_[kt] > tp) if d == 1 else (os_[kt] < tp))) else tp
    return e + kt, (px - entry) * d / risk, risk, entry


def run(inst):
    day, hm, O, H, L, C, sig = prepare(inst)
    cuts = np.flatnonzero(day[1:] != day[:-1]) + 1
    starts, ends = np.r_[0, cuts], np.r_[cuts, len(day)]
    cost = lib.COST[inst]
    out = {k: [] for k in "ABCD"}
    for s, z in zip(starts, ends):
        if pd.Timestamp(day[s]).dayofweek >= 5:
            continue
        h = hm[s:z]
        endi = s + int(np.searchsorted(h, CLOSE))
        sigi = np.flatnonzero(sig[s:endi]) + s
        if len(sigi) == 0:
            continue

        def next_sig(after, lo, hi):
            for k in sigi:
                if k > after and lo <= hm[k] < hi and hm[k] < LAST:
                    return k
            return None

        def take(k):
            r = trade(k, int(sig[k]), O, H, L, C, hm, endi)
            if r is None:
                return None, k
            x, g, risk, entry = r
            return {"instrument": inst, "day": pd.Timestamp(day[s]), "hm": int(hm[k]), "d": int(sig[k]),
                    "risque": risk, "gross_r": g, "cost_r": cost / risk}, x

        # D : tous les signaux des deux sessions
        last = -1
        for k in sigi:
            if k > last and (LON[0] <= hm[k] < LON[1] or US0 <= hm[k] < LAST):
                t, x = take(k)
                if t: out["D"].append(t); last = x
        # A, B, C
        for mode in "ABC":
            trades, last, pnl = [], -1, 0.0
            k = next_sig(last, *LON)
            while k is not None:
                t, x = take(k)
                if t: trades.append(t); last = x; pnl += t["gross_r"] - t["cost_r"]; break
                k = next_sig(k, *LON)
            if not (mode == "A" and trades and pnl > 0):
                k = next_sig(last, US0, LAST)
                while k is not None:
                    t, x = take(k)
                    if t: trades.append(t); last = x; pnl += t["gross_r"] - t["cost_r"]; break
                    k = next_sig(k, US0, LAST)
                if mode != "C":
                    while pnl <= 0 and len(trades) < MAXT:
                        k = next_sig(last, LON[0], LAST)
                        if k is None: break
                        t, x = take(k)
                        if t: trades.append(t); last = x; pnl += t["gross_r"] - t["cost_r"]
                        else: last = k
            out[mode] += trades
    return out


def day_stats(t):
    t = t[t.day >= lib.START]
    p = ((t.gross_r - t.cost_r) * 100).groupby(t.day).sum()
    cum = p.cumsum(); dd = (cum.cummax().clip(lower=0) - cum).max()
    return {"jours": int(len(p)), "jours_positifs_pct": round(float((p > 0).mean() * 100), 1), "pire_jour": round(float(p.min())),
            "eur_par_an": round(float(p.sum() / 15.77)), "total": round(float(p.sum())), "dd": round(float(dd))}


def main():
    allt = {k: [] for k in "ABCD"}
    for inst in MARKETS:
        o = run(inst)
        for k in o: allt[k] += o[k]
        print(inst, {k: len(v) for k, v in o.items()}, flush=True)
    names = {"A": "A stop si Londres gagne", "B": "B toujours 2 trades", "C": "C 2 trades seulement", "D": "D tous les signaux"}
    res = []
    rows = []
    for k in "DCAB":
        t = pd.DataFrame(allt[k]); t["mode"] = k; rows.append(t)
        for inst, g in [("4 marchés", t)] + list(t.groupby("instrument")):
            r = lib.evaluate(g, f"{names[k]} · {inst}"); r["jour"] = day_stats(g); r["brut_moyen"] = float(g.gross_r.mean())
            r["cout_median_r"] = float(g.cost_r.median()); res.append(r)
            print(lib.line(r), f"brut {g.gross_r.mean():+.3f} coût méd {g.cost_r.median():.2f}R |", r["jour"])
    pd.concat(rows).to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6f")
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
