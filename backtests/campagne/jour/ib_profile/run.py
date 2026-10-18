"""Initial Balance + profil (captures « Invest Louis », 18/10/2026). Règles fixées AVANT calcul.

Marchés : SP500 (captures) et NASDAQ100. IB = 09:30-10:00 New York (15:30-16:00 Paris).
Profil de l'IB : pas de volume dans les données → profil en TEMPS passé à chaque prix (Market Profile / TPO) :
40 tranches de prix sur l'amplitude de l'IB, chaque bougie M1 répartit 1 unité sur les tranches qu'elle couvre.
POC = tranche la plus fournie ; zone de valeur = 70 % autour du POC (extension vers le côté le plus fourni) → VAL / VAH.
Après 10:00, signaux sur clôtures M5, entrées jusqu'à 14:00 NY, sortie forcée 16:00 NY.
S1 BREAK & RETEST : clôture M5 sous la VAL (cassure) → vente limite au retour sur la VAL (M1 haut ≥ VAL) ;
   stop = POC. Miroir à l'achat : clôture M5 au-dessus de la VAH → achat limite au retour sur la VAH, stop = POC.
   Objectifs testés : 1:1 et 1:2.
S2 FADE : une clôture M5 au-dessus de la VAH puis une clôture M5 revenue SOUS la VAH → vente à l'ouverture suivante ;
   stop = plus haut atteint depuis 10:00 ; objectif = POC (et variante 1:1). Miroir sous la VAL.
1 setup à la fois ; règle d'Anto (1er trade, 2e seulement si perte). Coûts : fixes lib.COST et proportionnels
(1,25 pb Nasdaq, 2,1 pb S&P). Critère lib.evaluate. 4 variantes × 2 marchés.
"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa
PROP = {"NASDAQ100": 1.25e-4, "SP500": 2.1e-4}


def profile(H, L):
    lo, hi = L.min(), H.max()
    if hi <= lo:
        return None
    edges = np.linspace(lo, hi, 41); w = np.zeros(40)
    for h, l in zip(H, L):
        a, b = np.searchsorted(edges, l, "right") - 1, np.searchsorted(edges, h, "left")
        a = min(max(a, 0), 39); b = min(max(b, a + 1), 40)
        w[a:b] += 1.0 / (b - a)
    poc = int(w.argmax()); i = j = poc; tot = w[poc]
    while tot < 0.7 * w.sum():
        up = w[j + 1] if j + 1 < 40 else -1; dn = w[i - 1] if i > 0 else -1
        if up >= dn: j += 1; tot += up
        else: i -= 1; tot += dn
    return (edges[poc] + edges[poc + 1]) / 2, edges[i], edges[j + 1]   # POC, VAL, VAH


def walk(O, H, L, C, hm, e, d, stop, tp, limit):
    for j in range(e, len(C)):
        if hm[j] >= 960:
            return C[j - 1], j - 1
        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
            return (O[j] if (j > e and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop), j
        if not (limit and j == e) and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
            return (O[j] if (j > e and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp), j
    return C[-1], len(C) - 1


def run(inst):
    df = lib.load(inst, "America/New_York")
    rows = []
    for day, g in df[(df.hm >= 570) & (df.hm < 960)].groupby("day"):
        hm, O, H, L, C = (g[c].values for c in ("hm", "open", "high", "low", "close"))
        if day.dayofweek >= 5 or len(hm) < 0.9 * 390 or hm[0] != 570:
            continue
        ib = hm < 600
        if ib.sum() < 27:
            continue
        pr = profile(H[ib], L[ib])
        if pr is None:
            continue
        poc, val, vah = pr
        k10 = int(np.argmax(hm >= 600))
        # clôtures M5 après 10:00 : indices des minutes de fin de bloc
        ends = [j for j in range(k10, len(hm)) if (hm[j] + 1) % 5 == 0 and hm[j] < 840]
        for setup in ("S1", "S2"):
            for tpv in (("1:1", 1), ("1:2", 2)) if setup == "S1" else (("POC", None), ("1:1", 1)):
                busy = -1; brk = 0; above = below = False; hi_run = H[k10:].max() if False else None
                for j in ends:
                    if j <= busy:
                        continue
                    if setup == "S1":
                        if brk == 0:
                            brk = -1 if C[j] < val else (1 if C[j] > vah else 0)
                            continue
                        lvl = val if brk == -1 else vah; d = brk
                        nxt = np.arange(j + 1, len(hm)); nxt = nxt[hm[nxt] < 840]
                        if len(nxt) == 0:
                            break
                        tch = (H[nxt] >= lvl) if d == -1 else (L[nxt] <= lvl)
                        if not tch.any():
                            break
                        e = nxt[int(np.argmax(tch))]; entry = (max(O[e], lvl) if d == -1 else min(O[e], lvl))
                        stop = poc; risk = (entry - stop) * d
                        if risk <= 0:
                            break
                        tp = entry + d * tpv[1] * risk
                        px, x = walk(O, H, L, C, hm, e, d, stop, tp, True)
                    else:
                        if C[j] > vah: above = True
                        if C[j] < val: below = True
                        d = -1 if (above and C[j] < vah) else (1 if (below and C[j] > val) else 0)
                        if d == 0 or j + 1 >= len(hm):
                            continue
                        e = j + 1; entry = O[e]
                        stop = H[k10:e].max() if d == -1 else L[k10:e].min()
                        risk = (entry - stop) * d
                        if risk <= 0:
                            above = below = False; continue
                        tp = poc if tpv[1] is None else entry + d * tpv[1] * risk
                        if (tp - entry) * d <= 0:
                            above = below = False; continue
                        px, x = walk(O, H, L, C, hm, e, d, stop, tp, False)
                    rows.append({"instrument": inst, "setup": setup, "objectif": tpv[0], "day": day, "t_in": int(hm[e]),
                                 "t_out": int(hm[x]), "d": d, "entry": entry, "risque": risk, "gross_r": (px - entry) * d / risk})
                    busy = x
                    if setup == "S1":
                        break            # une cassure-retest par jour et par sens initial
                    above = below = False
    return pd.DataFrame(rows)


def main():
    t = pd.concat([run(i) for i in ("SP500", "NASDAQ100")], ignore_index=True)
    t.to_csv(os.path.join(HERE, "candidats.csv.gz"), index=False, float_format="%.6f")
    out = []
    for (inst, st, ob), g in t.groupby(["instrument", "setup", "objectif"]):
        for cname in ("fixe", "∝ prix"):
            c = lib.COST[inst] / g.risque if cname == "fixe" else g.entry * PROP[inst] / g.risque
            k = lib.regle_anto(g.assign(cost_r=c.values))
            r = lib.evaluate(k, f"{inst} {st} obj {ob} coût {cname}"); s = lib.stats_jour(k); r["jour"] = s; out.append(r)
            print(lib.line(r), f"| brut {k.gross_r.mean():+.3f} coût méd {k.cost_r.median():.2f}R | jours+ {s['jours_positifs_pct_jours_trades']:.0f}%")
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
