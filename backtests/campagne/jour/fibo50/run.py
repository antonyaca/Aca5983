"""Cassure de la 1re bougie M15 + retour au 50 % du Fibonacci (captures d'Anto, 22/10/2026). Règles fixées AVANT calcul.

Marchés : XAUUSD (exemples), NASDAQ100, SP500, EURUSD. 2011-2026, données corrigées.
Bougie de référence M15 : Londres 09:00-09:15 Paris (= 08:00 Londres) ; New York 09:30-09:45 heure de NY (15:30 Paris).
Cassure : 1re bougie M15 suivante qui CLÔTURE au-dessus du haut (achat) ou sous le bas (vente) de la référence.
Fibonacci : de l'extrémité OPPOSÉE de la référence (100 % = stop) à l'extrême de la cassure (0 % = objectif).
  A « 0 = extrême de la bougie de cassure » ; B « 0 = extrême atteint jusqu'au retour au 50 % » (le niveau d'entrée suit
  le nouvel extrême tant que l'ordre n'est pas rempli).
Entrée : ordre limite au 50 % (ratio 1:1), surveillé en M1 à partir de la clôture de la bougie de cassure ; annulé si le prix
atteint l'objectif avant (variante A) ou à l'échéance : 14:00 Paris (Londres), 21:00 Paris (New York).
Gestion : stop au 100 %, objectif au 0 % ; stop prioritaire ; dans la minute de remplissage seul le stop est testé ;
sortie forcée 22:00 Paris. Une cassure par session ; règle d'Anto par marché (Londres puis New York, 2e trade si perte).
Coûts lib.COST (or 0,47 $, Nasdaq 1,5 pt, S&P 0,75 pt, EURUSD 1,5 pip). Critère lib.evaluate.
"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa
MARKETS = ["XAUUSD", "NASDAQ100", "SP500", "EURUSD"]


def utc_min(d, tz, h, m):
    ts = pd.Timestamp(d.date()).tz_localize(tz) + pd.Timedelta(hours=h, minutes=m)
    return int(ts.tz_convert("UTC").value // 60_000_000_000)


def run(inst):
    df = lib.load(inst)
    T = df["time"].values.astype("datetime64[m]").astype(np.int64)
    O, H, L, C = (df[c].values for c in ("open", "high", "low", "close"))
    rows = []
    for d in pd.bdate_range("2011-01-01", lib.DATA_END):
        end = utc_min(d, "Europe/Paris", 22, 0)
        for sname, t0, deadline in (("Londres", utc_min(d, "Europe/Paris", 9, 0), utc_min(d, "Europe/Paris", 14, 0)),
                                    ("New York", utc_min(d, "America/New_York", 9, 30), utc_min(d, "Europe/Paris", 21, 0))):
            a, z = np.searchsorted(T, t0), np.searchsorted(T, t0 + 15)
            if z - a < 12:
                continue
            rh, rl = H[a:z].max(), L[a:z].min()
            # cassure : clôture d'une bougie M15 suivante hors du range
            brk = None; k = z
            while True:
                b0 = T[k] if k < len(T) else None
                if b0 is None or b0 >= deadline:
                    break
                bstart = t0 + ((b0 - t0) // 15) * 15
                kz = np.searchsorted(T, bstart + 15)
                if kz <= k or kz - k < 5:
                    k = kz if kz > k else k + 1; continue
                cl = C[kz - 1]
                if cl > rh: brk = (1, k, kz); break
                if cl < rl: brk = (-1, k, kz); break
                k = kz
            if brk is None:
                continue
            dd, kb, ke = brk
            sl = rl if dd == 1 else rh
            x0 = H[kb:ke].max() if dd == 1 else L[kb:ke].min()
            iend, idl = np.searchsorted(T, end), np.searchsorted(T, deadline)
            for var in ("A", "B"):
                x = x0; fill = None
                for j in range(ke, idl):
                    entry = (sl + x) / 2
                    hit = (L[j] <= entry) if dd == 1 else (H[j] >= entry)
                    if hit:
                        fill = (j, min(O[j], entry) if dd == 1 else max(O[j], entry), x); break
                    if var == "A" and ((H[j] >= x) if dd == 1 else (L[j] <= x)):
                        break                                   # objectif atteint avant l'entrée → annulé
                    if var == "B":
                        x = max(x, H[j]) if dd == 1 else min(x, L[j])
                if fill is None:
                    continue
                j, en, tp = fill
                risk = (en - sl) * dd
                if risk <= 0:
                    continue
                px, kx = None, iend - 1
                for i in range(j, iend):
                    if (L[i] <= sl) if dd == 1 else (H[i] >= sl):
                        px = O[i] if (i > j and ((O[i] < sl) if dd == 1 else (O[i] > sl))) else sl; kx = i; break
                    if i > j and ((H[i] >= tp) if dd == 1 else (L[i] <= tp)):
                        px = O[i] if ((O[i] > tp) if dd == 1 else (O[i] < tp)) else tp; kx = i; break
                if px is None:
                    px = C[iend - 1]
                rows.append({"instrument": inst, "session": sname, "variante": var, "day": d, "t_in": int(T[j]),
                             "t_out": int(T[kx]), "d": dd, "entry": en, "sl": sl, "tp": tp, "risque": risk,
                             "gross_r": (px - en) * dd / risk, "cost_r": lib.COST[inst] / risk})
    print(inst, len(rows), flush=True)
    return pd.DataFrame(rows)


def main():
    t = pd.concat([run(i) for i in MARKETS], ignore_index=True)
    t.to_csv(os.path.join(HERE, "candidats.csv.gz"), index=False, float_format="%.6f")
    out = []
    for (inst, var), g in t.groupby(["instrument", "variante"]):
        for sess, gs in [("2 sessions + règle d'Anto", None), ("Londres", g[g.session == "Londres"]), ("New York", g[g.session == "New York"])]:
            k = lib.regle_anto(g) if gs is None else gs
            r = lib.evaluate(k, f"{inst} {var} {sess}"); s = lib.stats_jour(k); r["jour"] = s; out.append(r)
            print(lib.line(r), f"| brut {k.gross_r.mean():+.3f} coût méd {k.cost_r.median():.2f}R réussite {(k.gross_r > 0).mean()*100:.0f}%")
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
