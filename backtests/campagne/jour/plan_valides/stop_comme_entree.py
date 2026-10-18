"""« Ton point d'entrée doit être ton stop » (Anto, 18/10/2026) appliqué au Williams. Règles fixées AVANT calcul.

Rappel Williams : niveaux haut/bas = ouverture 09:30 NY ± 0,5 × amplitude de la séance précédente (R = 0,5 × amplitude).
Le stop du Williams est l'ouverture. Deux lectures de l'idée, testées toutes les deux :

I1 « RETEST DE L'OUVERTURE » : le 1er niveau touché donne le SENS ; on n'entre PAS sur la cassure mais avec un ordre
   limite À L'OUVERTURE (l'ancien stop) dans ce sens, valable de la bougie suivante jusqu'à 15:30.
   Stop = niveau opposé (ouverture ∓ R) ; objectif = niveau cassé (ouverture ± R) → ratio 1:1 ; sinon sortie 16:00.
   Si stoppé, le niveau opposé vient d'être touché : 2e trade possible en miroir (limite à l'ouverture, sens inverse)
   — règle d'Anto (2e trade seulement après une perte).
I2 « STOP ET RETOURNEMENT À L'OUVERTURE » : trade 1 = Williams classique (entrée au niveau, stop à l'ouverture).
   S'il est stoppé, on se retourne IMMÉDIATEMENT au prix du stop (l'ouverture), sens inverse ; stop = niveau d'entrée
   du trade 1 ; objectif 1:1 = niveau opposé ; sinon sortie 16:00.
Deux sorties pour chaque lecture : objectif 1:1 et clôture 16:00 (pour I1 et I2 on garde le même stop).
Ordre des événements dans une même minute : prudent (le stop est supposé touché avant l'objectif ; pas d'objectif
dans la minute d'entrée d'un ordre limite).
Coûts : proportionnel 1,25 pb (≈ 1,5 pt à Nasdaq 12 000) et fixe 1,5 pt. Marché principal Nasdaq ; S&P en contrôle.
"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa
OP, CL, LIM_END = 570, 960, 930


def walk(hm, O, H, L, C, k, d, stop, tp, skip_tp_first):
    """Depuis la minute k (entrée déjà faite), stop prioritaire, objectif (ou None), sortie 16:00.
    Retourne (prix, minute de sortie ou None si clôture, stoppé?)."""
    last = k
    for j in range(k, len(hm)):
        if hm[j] >= CL:
            break
        last = j
        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
            px = O[j] if (j > k and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop
            return px, j, True
        if tp is not None and not (skip_tp_first and j == k) and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
            px = O[j] if (j > k and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp
            return px, j, False
    return C[last], None, False


def run(inst):
    df = lib.load(inst, "America/New_York")
    rows, prev_range = [], None
    for day, g in df.groupby("day"):
        if day.dayofweek >= 5:
            continue
        hm, O, H, L, C = (g[c].values for c in ("hm", "open", "high", "low", "close"))
        s = (hm >= OP) & (hm < CL)
        if not (s.sum() >= 0.9 * (CL - OP) and (hm == OP).any()):
            continue
        k0 = int(np.where(hm == OP)[0][0]); op = O[k0]
        if prev_range and prev_range > 0:
            R = 0.5 * prev_range
            up, dn = op + R, op - R
            idx = np.where(s)[0]
            hu, hd = H[idx] >= up, L[idx] <= dn
            hit = hu | hd
            if hit.any():
                j0 = int(hit.argmax())
                if not (hu[j0] and hd[j0]):
                    k, d = idx[j0], (1 if hu[j0] else -1)
                    for ex in ("TP 1:1", "clôture 16:00"):
                        # ---------- I1 : retest de l'ouverture, jusqu'à 2 trades
                        start, dd, n = k + 1, d, 1
                        while n <= 2:
                            cand = np.where((np.arange(len(hm)) >= start) & (hm < LIM_END) & (hm >= OP))[0]
                            fill = (L[cand] <= op) if dd == 1 else (H[cand] >= op)
                            if not fill.any():
                                break
                            kf = cand[int(fill.argmax())]
                            entry = min(O[kf], op) if dd == 1 else max(O[kf], op)
                            stop = op - dd * R
                            risk = (entry - stop) * dd
                            if risk <= 0:
                                break
                            tp = (op + dd * R) if ex == "TP 1:1" else None
                            px, kx, stopped = walk(hm, O, H, L, C, kf, dd, stop, tp, True)
                            rows.append({"instrument": inst, "lecture": "I1 retest ouverture", "sortie": ex, "day": day,
                                         "n": n, "d": dd, "entry": entry, "exit": px, "risque": risk,
                                         "t_in": int(hm[kf]), "t_out": int(hm[kx]) if kx is not None else CL})
                            if not stopped:
                                break
                            start, dd, n = kx + 1, -dd, n + 1
                        # ---------- I2 : Williams classique puis retournement au stop
                        entry = max(O[k], up) if d == 1 else min(O[k], dn)
                        risk = (entry - op) * d
                        if risk > 0:
                            tp1 = (entry + d * risk) if ex == "TP 1:1" else None
                            px, kx, stopped = walk(hm, O, H, L, C, k, d, op, tp1, False)
                            rows.append({"instrument": inst, "lecture": "I2 retournement au stop", "sortie": ex, "day": day,
                                         "n": 1, "d": d, "entry": entry, "exit": px, "risque": risk,
                                         "t_in": int(hm[k]), "t_out": int(hm[kx]) if kx is not None else CL})
                            if stopped and kx is not None:
                                e2 = op if px == op else px          # retournement au prix de sortie réel
                                st2 = entry                          # stop = niveau d'entrée du trade 1
                                r2 = (st2 - e2) * d                  # sens inverse : -d
                                if r2 > 0:
                                    tp2 = (e2 - d * r2) if ex == "TP 1:1" else None
                                    px2, kx2, _ = walk(hm, O, H, L, C, kx, -d, st2, tp2, True)
                                    rows.append({"instrument": inst, "lecture": "I2 retournement au stop", "sortie": ex,
                                                 "day": day, "n": 2, "d": -d, "entry": e2, "exit": px2, "risque": r2,
                                                 "t_in": int(hm[kx]), "t_out": int(hm[kx2]) if kx2 is not None else CL})
        prev_range = H[s].max() - L[s].min()
    t = pd.DataFrame(rows)
    t["gross_r"] = (t.exit - t.entry) * t.d / t.risque
    return t


def main():
    out = []
    allt = []
    for inst in ("NASDAQ100", "SP500"):
        t = run(inst); allt.append(t)
        for (lec, ex), g in t.groupby(["lecture", "sortie"]):
            for cname, cost in (("∝ prix", g.entry * (1.25e-4 if inst == "NASDAQ100" else 2.1e-4) / g.risque),
                                ("fixe", lib.COST[inst] / g.risque)):
                g = g.assign(cost_r=cost)
                for lab, sub in (("trade 1", g[g.n == 1]), ("règle Anto (1 + 2e si perte)", g)):
                    r = lib.evaluate(sub, f"{inst[:6]} {lec[:2]} {ex} {lab[:7]} {cname}")
                    s = lib.stats_jour(sub)
                    r.update({"instrument": inst, "lecture": lec, "sortie": ex, "trades": lab, "cout": cname, "jour": s})
                    out.append(r)
                    print(lib.line(r), "|", lib.line_jour(s))
    pd.concat(allt).to_csv(os.path.join(HERE, "stop_comme_entree_trades.csv.gz"), index=False, float_format="%.6f")
    json.dump(out, open(os.path.join(HERE, "stop_comme_entree.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
