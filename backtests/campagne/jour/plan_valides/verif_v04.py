"""Recodage indépendant (Claude, 18/10/2026) de V04 de l'agent « jours positifs » :
Williams k=0,5 Nasdaq ; 50 % de la position sort à entrée + 0,5 R ; le reste garde le stop d'origine jusqu'au gain
partiel, puis stop ramené au prix d'entrée À PARTIR DE LA MINUTE SUIVANTE ; sortie 16:00. 2e trade (règle d'Anto) :
si le 1er est stoppé en perte, niveau opposé touché ensuite → même gestion dans l'autre sens.
Priorité prudente dans une minute : stop avant objectif. Coût aller-retour compté une fois pour toute la position.
Comparaison trade par trade avec jours_positifs/trades.csv.gz (variante V04).
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa
OP, CL = 570, 960


def manage(hm, O, H, L, C, k, d, entry, stop):
    """Retourne (gross_r, minute de sortie finale ou None=clôture, perdant_total?)."""
    risk = (entry - stop) * d
    tp = entry + d * 0.5 * risk
    half_done, half_r, st = False, 0.0, stop
    last = k
    for j in range(k, len(hm)):
        if hm[j] >= CL:
            break
        last = j
        if (L[j] <= st) if d == 1 else (H[j] >= st):
            px = O[j] if (j > k and ((O[j] < st) if d == 1 else (O[j] > st))) else st
            r = (px - entry) * d / risk
            return (half_r + 0.5 * r if half_done else r), j
        if not half_done and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
            px = O[j] if (j > k and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp
            half_done, half_r = True, 0.5 * (px - entry) * d / risk
            st_next = entry                      # appliqué à partir de la minute suivante
            st = st_next if True else st
            # la minute du gain partiel n'est pas re-testée pour le nouveau stop
            continue
    r = (C[last] - entry) * d / risk
    return (half_r + 0.5 * r if half_done else r), None


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
                j0 = int(hit.argmax())
                if not (hu[j0] and hd[j0]):
                    k, d = idx[j0], (1 if hu[j0] else -1)
                    entry = max(O[k], up) if d == 1 else min(O[k], dn)
                    if (entry - op) * d > 0:
                        gr, kx = manage(hm, O, H, L, C, k, d, entry, op)
                        rows.append({"day": day, "n": 1, "t_in": int(hm[k]), "entry": entry, "risque": (entry - op) * d,
                                     "gross_r": gr})
                        if gr < 0 and kx is not None:   # stoppé en perte → 2e chance
                            d2, lvl = -d, (dn if d == 1 else up)
                            idx2 = np.where(s & (np.arange(len(hm)) > kx))[0]
                            h2 = (L[idx2] <= lvl) if d2 == -1 else (H[idx2] >= lvl)
                            if h2.any():
                                k2 = idx2[int(h2.argmax())]
                                e2 = min(O[k2], lvl) if d2 == -1 else max(O[k2], lvl)
                                if (e2 - op) * d2 > 0:
                                    gr2, _ = manage(hm, O, H, L, C, k2, d2, e2, op)
                                    rows.append({"day": day, "n": 2, "t_in": int(hm[k2]), "entry": e2,
                                                 "risque": (e2 - op) * d2, "gross_r": gr2})
        prev_range = H[s].max() - L[s].min()
    t = pd.DataFrame(rows)
    a = pd.read_csv(os.path.join(os.path.dirname(HERE), "jours_positifs", "trades.csv.gz"), parse_dates=["day", "t_in"])
    a = a[a.variante == "V04"].copy()
    a["hm"] = a.t_in.dt.hour * 60 + a.t_in.dt.minute
    m = t.merge(a[["day", "hm", "gross_r", "entry"]], left_on=["day", "t_in"], right_on=["day", "hm"], how="outer",
                suffixes=("_moi", "_agent"), indicator=True)
    both = m[m._merge == "both"]
    print(f"trades : moi {len(t)}, agent {len(a)}, communs {len(both)}, seulement moi {int((m._merge=='left_only').sum())}, "
          f"seulement agent {int((m._merge=='right_only').sum())}")
    diff = (both.gross_r_moi - both.gross_r_agent).abs()
    print(f"écart gross_r : max {diff.max():.6f}, trades avec écart > 0,001 R : {int((diff > 1e-3).sum())}")
    for cname, cost in (("fixe 1,5 pt", 1.5 / t.risque), ("∝ prix 1,25 pb", t.entry * 1.25e-4 / t.risque)):
        u = t.assign(cost_r=cost, t_out=0)
        for lab, sub in (("trade 1", u[u.n == 1]), ("règle Anto", u)):
            r = lib.evaluate(sub, f"V04 recodé {lab} · {cname}")
            print(lib.line(r), "|", lib.line_jour(lib.stats_jour(sub)))
    t.to_csv(os.path.join(HERE, "verif_v04_trades.csv.gz"), index=False, float_format="%.6f")


if __name__ == "__main__":
    main()
