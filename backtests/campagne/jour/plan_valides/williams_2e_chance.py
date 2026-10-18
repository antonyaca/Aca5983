"""Règle d'Anto appliquée au Williams Nasdaq validé (18/10/2026). Règles fixées AVANT calcul.

Trade 1 = Williams k=0,5 (identique à robustesse/three_strats.py) : niveaux = ouverture 09:30 ± 0,5 × amplitude de la
séance précédente ; 1er niveau touché ; stop = ouverture ; sortie 16:00 NY.
Trade 2 (seulement si le trade 1 est STOPPÉ, donc perdant) : si le niveau OPPOSÉ est touché après la bougie du stop,
entrée dans l'autre sens, même stop (ouverture), même sortie 16:00. Sinon rien. Max 2 trades par jour.
Coûts : 1,5 pt fixe (hypothèse du dépôt) ET proportionnel au prix 1,25 pb (≈ 1,5 pt à Nasdaq 12 000) ; 100 € par R.
Contrôle : le trade 1 doit retrouver exactement les trades Williams de hors_echantillon/trades_NASDAQ100.csv.gz.
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa

OP, CL = 570, 960


def exit_price(hm, O, H, L, C, k, d, stop):
    if (L[k] <= stop) if d == 1 else (H[k] >= stop):
        return stop, k
    last = k
    for j in range(k + 1, len(hm)):
        if hm[j] >= CL:
            break
        last = j
        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
            return (O[j] if ((O[j] < stop) if d == 1 else (O[j] > stop)) else stop), j
    return C[last], None


def main():
    df = lib.load("NASDAQ100", "America/New_York")
    rows, prev_range = [], None
    for day, g in df.groupby("day"):
        if day.dayofweek >= 5:
            continue
        hm, O, H, L, C = (g[c].values for c in ("hm", "open", "high", "low", "close"))
        s = (hm >= OP) & (hm < CL)
        if not (s.sum() >= 0.9 * (CL - OP) and (hm == OP).any()):
            continue
        k0 = int(np.where(hm == OP)[0][0]); op = O[k0]
        if prev_range:
            up, dn = op + 0.5 * prev_range, op - 0.5 * prev_range
            idx = np.where(s)[0]
            hu, hd = H[idx] >= up, L[idx] <= dn
            hit = hu | hd
            if hit.any():
                j = int(hit.argmax())
                if not (hu[j] and hd[j]):
                    k, d = idx[j], (1 if hu[j] else -1)
                    entry = max(O[k], up) if d == 1 else min(O[k], dn)
                    risk = (entry - op) * d
                    if risk > 0:
                        px, ks = exit_price(hm, O, H, L, C, k, d, op)
                        rows.append({"day": day, "n": 1, "d": d, "entry": entry, "exit": px, "risque": risk,
                                     "t_in": int(hm[k]), "t_out": int(hm[ks]) if ks is not None else CL})
                        if ks is not None:  # stoppé → 2e chance sur le niveau opposé
                            d2, lvl = -d, (dn if d == 1 else up)
                            idx2 = np.where(s & (np.arange(len(hm)) > ks))[0]
                            h2 = (L[idx2] <= lvl) if d2 == -1 else (H[idx2] >= lvl)
                            if h2.any():
                                k2 = idx2[int(h2.argmax())]
                                e2 = min(O[k2], lvl) if d2 == -1 else max(O[k2], lvl)
                                r2 = (e2 - op) * d2
                                if r2 > 0:
                                    px2, ks2 = exit_price(hm, O, H, L, C, k2, d2, op)
                                    rows.append({"day": day, "n": 2, "d": d2, "entry": e2, "exit": px2, "risque": r2,
                                                 "t_in": int(hm[k2]), "t_out": int(hm[ks2]) if ks2 is not None else CL})
        prev_range = H[s].max() - L[s].min()
    t = pd.DataFrame(rows)
    t["gross_r"] = (t.exit - t.entry) * t.d / t.risque
    ref = pd.read_csv(os.path.join(CAMP, "hors_echantillon", "trades_NASDAQ100.csv.gz"), parse_dates=["day"])
    ref = ref[ref.strategie == "Williams"].set_index("day")
    t1 = t[t.n == 1].set_index("day")
    common = t1.index.intersection(ref.index)
    print(f"contrôle trade 1 vs référence : {len(t1)} vs {len(ref)} trades, écart max gross_r sur {len(common)} jours communs :",
          float((t1.loc[common, 'gross_r'] - ref.loc[common, 'gross_r']).abs().max()))
    out = []
    for cname, cost in (("coût fixe 1,5 pt", 1.5 / t.risque), ("coût ∝ prix 1,25 pb", t.entry * 1.25e-4 / t.risque)):
        t["cost_r"] = cost
        for lab, sub in (("trade 1 seul", t[t.n == 1]), ("trade 1 + 2e chance", t)):
            r = lib.evaluate(sub, f"Williams {lab} · {cname}"); s = lib.stats_jour(sub)
            print(lib.line(r)); print("    ", lib.line_jour(s))
            out.append({"evaluate": r, "jour": s})
        t2 = t[t.n == 2]
        r = lib.evaluate(t2, f"2e chance seule · {cname}"); print(lib.line(r))
    t.to_csv(os.path.join(HERE, "williams_2e_chance_trades.csv.gz"), index=False, float_format="%.6f")
    import json
    json.dump(out, open(os.path.join(HERE, "williams_2e_chance.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
