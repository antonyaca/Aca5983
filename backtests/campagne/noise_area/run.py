"""Noise area (Zarattini, Aziz & Barbon 2024) — re-test sur données à l'heure corrigée (27/10/2026).

Règles identiques au lot 4 (16/10/2026), fixées avant calcul :
- Séance 09:30-16:00 New York, Nasdaq 100. Jours avec < 90 % des minutes écartés ; minutes manquantes = dernier cours connu.
- sigma(m) = moyenne sur les 14 séances précédentes de |cours à la minute m / ouverture - 1|.
- Borne haute = max(ouverture, clôture veille) x (1 + sigma(m)) ; borne basse = min(ouverture, clôture veille) x (1 - sigma(m)).
- Contrôle toutes les 30 min (10:00 -> 15:30) : au-dessus de la borne haute -> achat ; sous la borne basse -> vente.
- Position coupée au contrôle suivant si le cours repasse sous la borne haute (achat) / au-dessus de la borne basse (vente).
- Sortie 16:00. 1 R = 0,5 ATR14 journalier (jours précédents). Coût lib.COST (1,5 pt aller-retour) par trade.
Variantes (4, aucune autre) :
  V1 deux sens, tous les trades ; V2 achats seuls, tous les trades ;
  V3 deux sens + règle d'Anto (1er trade, 2e seulement si perdant) ; V4 achats seuls + règle d'Anto.
Critère : lib.evaluate (PROTOCOLE.md). Découverte 2011-2018 / validation 2019-2026.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib import load, evaluate, line, regle_anto, stats_jour, COST  # noqa: E402

INST = "NASDAQ100"
A, B = 570, 960
N = B - A


def matrix():
    df = load(INST)
    s = df[(df["hm"] >= A) & (df["hm"] < B)]
    s = s[s["day"].dt.dayofweek < 5]
    cnt = s.groupby("day").size()
    first = s.groupby("day")["hm"].first()
    ok = cnt[(cnt >= 0.9 * N) & (first == A)].index
    s = s[s["day"].isin(ok)]
    days = list(ok)
    idx = {d: i for i, d in enumerate(days)}
    C = np.full((len(days), N), np.nan)
    C[s["day"].map(idx).values, (s["hm"] - A).values] = s["close"].values
    C = pd.DataFrame(C).T.ffill().T.values
    O = s.groupby("day")["open"].first().loc[days].values
    H = s.groupby("day")["high"].max().loc[days].values
    L = s.groupby("day")["low"].min().loc[days].values
    return days, O, H, L, C


def run():
    days, O, H, L, C = matrix()
    last = C[:, -1]
    prevc = np.r_[np.nan, last[:-1]]
    move = np.abs(C / O[:, None] - 1)
    tr = np.nanmax(np.vstack([H - L, np.abs(H - prevc), np.abs(L - prevc)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    checks = list(range(30, N - 29, 30))            # 10:00 ... 15:30 (indice minute = m-1 -> cours de clôture de la minute)
    rows = []
    for i in range(15, len(days)):
        if np.isnan(atr[i]) or np.isnan(prevc[i]):
            continue
        sigma = move[i - 14:i].mean(axis=0)
        ub = max(O[i], prevc[i]) * (1 + sigma)
        lb = min(O[i], prevc[i]) * (1 - sigma)
        c = C[i]
        R = 0.5 * atr[i]
        for long_only in (False, True):
            pos, entry, t_in = 0, None, None
            for m in checks:
                px = c[m - 1]
                if (pos == 1 and px < ub[m - 1]) or (pos == -1 and px > lb[m - 1]):
                    rows.append((long_only, days[i], t_in, m, pos, entry, px, R))
                    pos = 0
                if pos == 0:
                    if px > ub[m - 1]:
                        pos, entry, t_in = 1, px, m
                    elif px < lb[m - 1] and not long_only:
                        pos, entry, t_in = -1, px, m
            if pos:
                rows.append((long_only, days[i], t_in, N, pos, entry, c[-1], R))
    t = pd.DataFrame(rows, columns=["long_only", "day", "t_in", "t_out", "side", "entry", "exit", "R"])
    t["gross_r"] = t["side"] * (t["exit"] - t["entry"]) / t["R"]
    t["cost_r"] = COST[INST] / t["R"]
    return t


if __name__ == "__main__":
    t = run()
    out = {}
    for name, lo, anto in [("V1 deux sens", False, False), ("V2 achats seuls", True, False),
                           ("V3 deux sens + règle Anto", False, True), ("V4 achats seuls + règle Anto", True, True)]:
        x = t[t["long_only"] == lo].copy()
        if anto:
            x = regle_anto(x)
        r = evaluate(x, name)
        r["jour"] = stats_jour(x)
        out[name] = r
        print(line(r))
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, default=str)
    t.to_csv(os.path.join(HERE, "trades.csv.gz"), index=False)
