"""Pullback structurel M15 — la méthode appliquée en replay avec Anto (05/11/2026). Règles fixées AVANT calcul.

Marché : NASDAQ100 (CFD, M1 bid HistData corrigé UTC), barres M15 reconstruites, heure de Paris. 2011-2026.
Cadre : 100 € de risque fixe par trade (1 R), coût aller-retour lib.COST (1,5 pt), pas de position la nuit.

1. Swings : fractale 2/2 sur M15 (plus haut > 2 barres avant et ≥ 2 barres après ; idem plus bas),
   connue seulement 2 barres après (pas de regard vers le futur).
2. Structure : haussière si les 2 derniers sommets ET les 2 derniers creux confirmés sont croissants ; baissière si
   décroissants ; sinon range (pas de trade).
3. Cassure : structure haussière + clôture M15 au-dessus du dernier sommet → niveau L = ce sommet (inverse en vente).
4. Pullback : une barre revient toucher L + 0,25 ATR14(M15) (achat). Annulé si clôture < L − 0,5 ATR, ou si rien
   ne se déclenche dans les 16 barres (4 h) qui suivent la cassure.
5. Déclencheur (variante « confirmation ») : après le toucher, 1re barre M15 verte qui clôture au-dessus de L.
   Entrée à l'ouverture de la barre suivante. SL = plus bas depuis le toucher − 0,1 ATR. Risque entre 3× les frais
   et 3 ATR, sinon ignoré.
   Variante « limite aveugle » : ordre limite à L dès la cassure, SL = L − 0,75 ATR, sans attendre de bougie.
6. TP = RR × risque (RR 1,5 / 2 / 2,5). Stop prioritaire dans la même minute. Sortie forcée à 21:45 Paris
   (ou 08:45 pour la séance asiatique). Un seul trade à la fois.
7. Séances (heure de Paris, heure du déclencheur) :
   JOUR 08:00-20:00 · LONDRES 09:00-12:00 · US 15:30-18:00 · LDN+US · APREM 14:00-20:00 · ASIE 01:00-07:00.
8. Filtres testés sur JOUR RR 2 seulement : stochastique (14,3) pas en extrême (< 80 à l'achat, > 20 à la vente) ;
   tendance de fond (clôture du bon côté de l'EMA 200 M15).
9. Gestion du jour : tous les signaux, puis règle d'Anto (1 trade, 2e seulement si le 1er perd) via lib.regle_anto.
Critère : lib.evaluate (découverte 2011-2018 / validation 2019-2026, t ≥ 3, frais ×2, sans top 10, ≥ 60 % années +).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib import COST, evaluate, line, load, regle_anto, stats_jour, line_jour  # noqa: E402

INST = "NASDAQ100"
C = COST[INST]
SESS = {"JOUR": [(480, 1200)], "LONDRES": [(540, 720)], "US": [(930, 1080)], "LDN+US": [(540, 720), (930, 1080)],
        "APREM": [(840, 1200)], "ASIE": [(60, 420)]}


def m15(df):
    g = df.set_index("time")
    b = g.resample("15min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    b["t"] = b.index
    loc = b.index.tz_convert("Europe/Paris")
    b["hm"] = loc.hour * 60 + loc.minute
    b["day"] = loc.tz_localize(None).normalize()
    tr = np.maximum(b["high"] - b["low"], np.maximum(abs(b["high"] - b["close"].shift()), abs(b["low"] - b["close"].shift())))
    b["atr"] = tr.rolling(14).mean().shift(1)                     # connu avant la barre
    lo14, hi14 = b["low"].rolling(14).min(), b["high"].rolling(14).max()
    b["stoch"] = (100 * (b["close"] - lo14) / (hi14 - lo14)).rolling(3).mean()
    b["ema200"] = b["close"].ewm(span=200, adjust=False).mean()
    return b.reset_index(drop=True)


def signals(b):
    """Candidats (indépendants de la séance et du RR) : dict(side, kind, i_trig, t_entry, entry_ref, sl, L)."""
    o, h, l, c, a = (b[k].values for k in ("open", "high", "low", "close", "atr"))
    n = len(b)
    sh, sl_ = [], []                                              # (index, prix) des swings confirmés
    out, setup = [], None
    for j in range(4, n - 1):
        p = j - 2                                                  # candidat fractale confirmé à la clôture de j
        if h[p] > max(h[p - 2], h[p - 1]) and h[p] >= max(h[p + 1], h[p + 2]):
            sh.append((p, h[p]))
        if l[p] < min(l[p - 2], l[p - 1]) and l[p] <= min(l[p + 1], l[p + 2]):
            sl_.append((p, l[p]))
        if np.isnan(a[j]) or len(sh) < 2 or len(sl_) < 2:
            continue
        up = sh[-1][1] > sh[-2][1] and sl_[-1][1] > sl_[-2][1]
        dn = sh[-1][1] < sh[-2][1] and sl_[-1][1] < sl_[-2][1]
        # nouvelle cassure
        if up and c[j] > sh[-1][1] and (setup is None or setup["L"] != sh[-1][1]):
            setup = {"side": 1, "L": sh[-1][1], "j0": j, "touch": None, "ext": None}
            out.append({"side": 1, "kind": "limite", "i_trig": j, "L": sh[-1][1], "sl": sh[-1][1] - 0.75 * a[j]})
            continue
        if dn and c[j] < sl_[-1][1] and (setup is None or setup["L"] != sl_[-1][1]):
            setup = {"side": -1, "L": sl_[-1][1], "j0": j, "touch": None, "ext": None}
            out.append({"side": -1, "kind": "limite", "i_trig": j, "L": sl_[-1][1], "sl": sl_[-1][1] + 0.75 * a[j]})
            continue
        if setup is None:
            continue
        L, s = setup["L"], setup["side"]
        if j - setup["j0"] > 16 or (s == 1 and c[j] < L - 0.5 * a[j]) or (s == -1 and c[j] > L + 0.5 * a[j]):
            setup = None
            continue
        if setup["touch"] is None:
            if (s == 1 and l[j] <= L + 0.25 * a[j]) or (s == -1 and h[j] >= L - 0.25 * a[j]):
                setup["touch"], setup["ext"] = j, (l[j] if s == 1 else h[j])
        else:
            setup["ext"] = min(setup["ext"], l[j]) if s == 1 else max(setup["ext"], h[j])
        if setup["touch"] is not None:
            if s == 1 and c[j] > o[j] and c[j] > L:
                out.append({"side": 1, "kind": "conf", "i_trig": j, "L": L, "sl": setup["ext"] - 0.1 * a[j]})
                setup = None
            elif s == -1 and c[j] < o[j] and c[j] < L:
                out.append({"side": -1, "kind": "conf", "i_trig": j, "L": L, "sl": setup["ext"] + 0.1 * a[j]})
                setup = None
    return pd.DataFrame(out)


def in_sess(hm, wins):
    return any(a <= hm < z for a, z in wins)


def simulate(cand, b, m1, sess, rr, filt=None):
    """Exécute les candidats d'une variante sur M1. Retourne DataFrame de trades (day, t_in, t_out, gross_r, cost_r)."""
    T = m1["time"].values.astype("datetime64[m]").astype(np.int64)
    O, H, Lo, Cl = (m1[k].values for k in ("open", "high", "low", "close"))
    hm_m1 = m1["hm"].values
    m1_day = m1["day"].values
    wins = SESS[sess]
    exit_hm = 525 if sess == "ASIE" else 1305
    bt = b["t"].values.astype("datetime64[m]").astype(np.int64)
    trades, busy_until = [], -1
    for r in cand.itertuples():
        j = r.i_trig
        if not in_sess(b.at[j, "hm"], wins):
            continue
        if filt == "stoch" and ((r.side == 1 and b.at[j, "stoch"] >= 80) or (r.side == -1 and b.at[j, "stoch"] <= 20)):
            continue
        if filt == "ema" and ((r.side == 1 and b.at[j, "close"] < b.at[j, "ema200"]) or
                              (r.side == -1 and b.at[j, "close"] > b.at[j, "ema200"])):
            continue
        t0 = bt[j] + 15                                            # ouverture de la barre suivante
        k = np.searchsorted(T, t0)
        if k >= len(T) or k <= busy_until or T[k] - t0 > 60:
            continue
        day = b.at[j, "day"]
        # fenêtre de vie : jusqu'à l'heure de sortie forcée du même jour Paris
        horizon = k + 1500
        seg_hm = hm_m1[k:horizon]
        if seg_hm[0] >= exit_hm or m1_day[k] != day:
            continue
        newday = m1_day[k:horizon] != day                           # jamais de position la nuit
        stop_mask = (seg_hm >= exit_hm) | newday
        if stop_mask.any():
            f = int(np.argmax(stop_mask))
            stop_rel = f - 1 if newday[f] else f                   # clôture 21:45, ou dernière minute du jour
        else:
            stop_rel = len(seg_hm) - 1
        # gestion de passage de minuit (séance JOUR/US/... ne passe pas minuit : sortie 21:45 avant)
        end = k + stop_rel
        if r.kind == "limite":
            # remplissage de la limite à L pendant la vie du setup (16 barres) et avant la sortie forcée
            lim_end = min(end, np.searchsorted(T, bt[j] + 15 * 17))
            seg = Lo[k:lim_end] if r.side == 1 else H[k:lim_end]
            hit = np.nonzero(seg <= r.L)[0] if r.side == 1 else np.nonzero(seg >= r.L)[0]
            if len(hit) == 0:
                continue
            k = k + hit[0]
            entry = min(O[k], r.L) if r.side == 1 else max(O[k], r.L)
        else:
            entry = O[k]
        risk = (entry - r.sl) * r.side
        a = b.at[j, "atr"]
        if risk < 3 * C or risk > 3 * a:
            continue
        tp = entry + r.side * rr * risk
        hs, ls = H[k:end + 1], Lo[k:end + 1]
        if r.side == 1:
            sl_hit, tp_hit = np.nonzero(ls <= r.sl)[0], np.nonzero(hs >= tp)[0]
        else:
            sl_hit, tp_hit = np.nonzero(hs >= r.sl)[0], np.nonzero(ls <= tp)[0]
        i_sl = sl_hit[0] if len(sl_hit) else 10**9
        i_tp = tp_hit[0] if len(tp_hit) else 10**9
        if i_sl <= i_tp and i_sl < 10**9:
            px = r.sl if (O[k + i_sl] - r.sl) * r.side > 0 or i_sl == 0 else O[k + i_sl]   # gap au-delà du stop
            ex = k + i_sl
        elif i_tp < 10**9:
            px, ex = tp, k + i_tp
        else:
            px, ex = Cl[end], end
        g = (px - entry) * r.side / risk
        trades.append({"day": day, "t_in": int(T[k]), "t_out": int(T[ex]), "side": r.side, "gross_r": g,
                       "cost_r": C / risk, "risk_pts": risk})
        busy_until = ex
    return pd.DataFrame(trades)


def main():
    m1 = load(INST, tz="Europe/Paris")
    b = m15(m1)
    cand = signals(b)
    cand.to_csv(os.path.join(HERE, "candidats.csv.gz"), index=False)
    variants = []
    for sess in SESS:
        for rr in (1.5, 2.0, 2.5):
            variants.append((f"{sess} conf RR{rr}", sess, rr, "conf", None))
    variants += [("JOUR conf RR2 +stoch", "JOUR", 2.0, "conf", "stoch"),
                 ("JOUR conf RR2 +EMA200", "JOUR", 2.0, "conf", "ema"),
                 ("JOUR limite RR2", "JOUR", 2.0, "limite", None)]
    res, all_tr = [], []
    for lab, sess, rr, kind, filt in variants:
        t = simulate(cand[cand["kind"] == kind].sort_values("i_trig"), b, m1, sess, rr, filt)
        if len(t) == 0:
            continue
        r = evaluate(t, lab)
        ta = regle_anto(t)
        ra = evaluate(ta, lab + " [règle Anto]")
        r["regle_anto"] = {"eval": ra, "jour": stats_jour(ta)}
        r["risque_median_pts"] = float(t["risk_pts"].median())
        r["cout_median_r"] = float(t["cost_r"].median())
        res.append(r)
        print(line(r))
        print("   ", line(ra))
        print("   ", line_jour(r["regle_anto"]["jour"]))
        t["variante"] = lab
        all_tr.append(t)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False, default=float)
    pd.concat(all_tr).to_csv(os.path.join(HERE, "trades.csv.gz"), index=False)


if __name__ == "__main__":
    main()
