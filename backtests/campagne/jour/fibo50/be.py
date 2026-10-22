"""Fibo 50 % + break-even (demande d'Anto 22/10/2026, capture or : le prix va vers 0,382 sans toucher l'objectif puis revient au stop).
Mêmes entrées que run.py (candidats.csv.gz). Règles fixées AVANT calcul :
dès que le prix atteint entrée + X·R (X ∈ {0,25 ; 0,5 ; 0,75}), le stop passe à l'entrée (actif à partir de la minute suivante).
Objectif inchangé (0 % = +1 R). Stop prioritaire ; dans la minute de remplissage seul le stop est testé ; sortie 22:00 Paris.
Sortie au break-even = 0 R brut, frais payés quand même. Critère lib.evaluate.
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import lib  # noqa
t = pd.read_csv(os.path.join(HERE, "candidats.csv.gz"), parse_dates=["day"])
out = []
for inst, g in t.groupby("instrument"):
    df = lib.load(inst)
    T = df["time"].values.astype("datetime64[m]").astype(np.int64)
    O, H, L, C = (df[c].values for c in ("open", "high", "low", "close"))
    for X in (None, 0.25, 0.5, 0.75):
        rows = []
        for r in g.itertuples():
            dd, en, tp, R = r.d, r.entry, r.tp, r.risque
            j = np.searchsorted(T, r.t_in)
            iend = np.searchsorted(T, int(pd.Timestamp(r.day.date()).tz_localize("Europe/Paris").replace(hour=22).tz_convert("UTC").value // 60_000_000_000))
            sl, trig, px, be = r.sl, (en + dd * X * R) if X else None, None, False
            for i in range(j, iend):
                if (L[i] <= sl) if dd == 1 else (H[i] >= sl):
                    px = O[i] if (i > j and ((O[i] < sl) if dd == 1 else (O[i] > sl))) else sl; break
                if i > j and ((H[i] >= tp) if dd == 1 else (L[i] <= tp)):
                    px = O[i] if ((O[i] > tp) if dd == 1 else (O[i] < tp)) else tp; break
                if trig is not None and not be and ((H[i] >= trig) if dd == 1 else (L[i] <= trig)):
                    sl, be = en, True
            if px is None:
                px = C[iend - 1]
            rows.append(r._asdict() | {"gross_r": (px - en) * dd / R})
        k = pd.DataFrame(rows).drop(columns="Index")
        lab = "sans BE" if X is None else f"BE à +{X} R"
        for var in ("A", "B"):
            kv = k[k.variante == var]
            for sess, ks in (("2 sessions + règle", lib.regle_anto(kv)), ("New York", kv[kv.session == "New York"])):
                res = lib.evaluate(ks, f"{inst} {var} {sess} {lab}")
                out.append(res)
                print(lib.line(res), f"| brut {ks.gross_r.mean():+.3f} gagnants {(ks.gross_r > 0.01).mean()*100:.0f}% BE {(ks.gross_r.abs() < 0.01).mean()*100:.0f}%", flush=True)
pd.DataFrame(out).to_csv(os.path.join(HERE, "be_results.csv"), index=False)
