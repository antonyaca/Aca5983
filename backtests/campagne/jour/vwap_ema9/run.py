"""Stratégie « VWAP + EMA 9 » (captures d'Anto, 18/10/2026), transposée en CFD indices. Règles fixées AVANT calcul.

Marchés : NASDAQ100, SP500. Bougies M5 (construites depuis le M1, heure de New York).
VWAP : pas de volume dans les données → approximation par le prix moyen pondéré dans le temps (TWAP) du prix typique
(H+B+C)/3 depuis 09:30 NY, remis à zéro chaque séance. EMA 9 sur les clôtures M5 (calcul continu).
Signal : clôture d'une bougie M5 où l'EMA 9 croise le TWAP (vers le haut → achat ; vers le bas → vente) ; la bougie
précédente doit appartenir à la même séance (pas de signal sur la 1re bougie). Entrées de 09:35 à 12:00 NY
(15:35-18:00 Paris). Entrée à l'ouverture de la bougie M5 suivante.
Stop dur (équivalent du « −25-30 % » de l'option) : 0,25 × ATR14 journalier (séances précédentes) ; 1 R = cette distance.
Stop de la vidéo : sortie à l'ouverture de la bougie suivante dès qu'une bougie M5 CLÔTURE de l'autre côté de l'EMA 9.
Sorties testées : A = stop dur + clôture au-delà de l'EMA 9 (pas d'objectif) ; B = A + objectif 1:1.
Sortie forcée 16:00 NY. Un trade à la fois ; règle d'Anto (1er trade du jour, 2e seulement si le 1er perd) appliquée
par marché ET « 1er signal du jour tous indices ». Coûts : fixes lib.COST et proportionnels (1,25 pb Nasdaq, 2,1 pb S&P).
Critère : lib.evaluate. 2 sorties × 3 périmètres = 6 variantes.
"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa
PROP = {"NASDAQ100": 1.25e-4, "SP500": 2.1e-4}


def candidates(inst):
    df = lib.load(inst, "America/New_York")
    m5 = df.set_index("time")[["open", "high", "low", "close"]].resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    loc = m5.index.tz_convert("America/New_York")
    m5["day"] = loc.tz_localize(None).normalize(); m5["hm"] = loc.hour * 60 + loc.minute
    m5["ema"] = m5.close.ewm(span=9, adjust=False).mean()
    # ATR14 journalier sur la séance 09:30-16:00, décalé d'un jour
    s = df[(df.hm >= 570) & (df.hm < 960)].groupby("day").agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
    pc = s.c.shift()
    atr = pd.concat([s.h - s.l, (s.h - pc).abs(), (s.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    rows = []
    for day, g in m5[(m5.hm >= 570) & (m5.hm < 960)].groupby("day"):
        if day.dayofweek >= 5 or len(g) < 70 or g.hm.iloc[0] != 570 or day not in atr.index or not np.isfinite(atr[day]):
            continue
        O, H, L, C, E, hm = (g[c].values for c in ("open", "high", "low", "close", "ema", "hm"))
        tw = np.cumsum((H + L + C) / 3) / np.arange(1, len(C) + 1)
        R = 0.25 * atr[day]
        busy = -1
        for i in range(1, len(C) - 1):
            if hm[i] + 5 > 720 or i + 1 <= busy:
                continue
            up = E[i] > tw[i] and E[i - 1] <= tw[i - 1]
            dn = E[i] < tw[i] and E[i - 1] >= tw[i - 1]
            if not (up or dn):
                continue
            d = 1 if up else -1
            e = i + 1; entry = O[e]; stop = entry - d * R
            for ex in ("A", "B"):
                tp = entry + d * R if ex == "B" else None
                px, j = None, e
                while j < len(C):
                    if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                        px = O[j] if (j > e and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop; break
                    if tp is not None and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
                        px = O[j] if (j > e and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp; break
                    if ((C[j] < E[j]) if d == 1 else (C[j] > E[j])):
                        px = O[j + 1] if j + 1 < len(C) else C[j]; j = min(j + 1, len(C) - 1); break
                    j += 1
                if px is None:
                    px, j = C[-1], len(C) - 1
                rows.append({"instrument": inst, "sortie": ex, "day": day, "t_in": int(hm[e]), "t_out": int(hm[j]),
                             "d": d, "entry": entry, "exit": px, "risque": R, "gross_r": (px - entry) * d / R})
                if ex == "A":
                    jA = j
            busy = jA  # un trade à la fois (sortie A comme référence de l'enchaînement)
    return pd.DataFrame(rows)


def main():
    t = pd.concat([candidates(i) for i in ("NASDAQ100", "SP500")], ignore_index=True)
    t.to_csv(os.path.join(HERE, "candidats.csv.gz"), index=False, float_format="%.6f")
    out = []
    for ex in ("A", "B"):
        for per in ("NASDAQ100", "SP500", "2 indices"):
            g = t[t.sortie == ex] if per == "2 indices" else t[(t.sortie == ex) & (t.instrument == per)]
            for cname in ("fixe", "∝ prix"):
                c = g.instrument.map(lib.COST) / g.risque if cname == "fixe" else g.entry * g.instrument.map(PROP) / g.risque
                taken = lib.regle_anto(g.assign(cost_r=c.values))
                r = lib.evaluate(taken, f"{per} sortie {ex} · coût {cname}")
                s = lib.stats_jour(taken); r["jour"] = s; r["brut_candidats"] = float(g.gross_r.mean()); out.append(r)
                print(lib.line(r), f"| brut {taken.gross_r.mean():+.3f} coût méd {taken.cost_r.median():.2f}R |", lib.line_jour(s))
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
