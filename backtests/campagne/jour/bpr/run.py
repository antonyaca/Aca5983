"""BPR (Balanced Price Range, ICT) à l'ouverture de Londres / New York + retest M1 (captures d'Anto, 18/10/2026).
Règles fixées AVANT calcul.

Marchés : XAUUSD (exemples d'Anto), EURUSD, NASDAQ100, SP500. 2011-2026, données corrigées.
Ouvertures : Londres 08:00 heure de Londres ; New York 09:30 heure de New York (15:30 Paris, comme sur les captures).
1. Bougies M5 des 90 premières minutes après l'ouverture.
   FVG haussier en i : bas[i] > haut[i-2] → zone [haut[i-2], bas[i]] ; FVG baissier : haut[i] < bas[i-2] → zone [haut[i], bas[i-2]].
2. BPR = 1er FVG suivi d'un FVG de sens OPPOSÉ dont la zone chevauche la sienne ; zone BPR = intersection.
   Sens du trade = sens du 2e FVG (2e baissier → vente, 2e haussier → achat). Un seul BPR par session (le 1er).
3. Retest M1, dans les 3 h qui suivent la clôture de la bougie M5 qui complète le BPR :
   L « limite » : entrée au bord proche de la zone dès qu'une bougie M1 le touche (vente : haut M1 ≥ bas de zone) ;
   C « confirmation » : après ce contact, 1re bougie M1 qui reclôture hors de la zone côté trade (vente : clôture < bas de
     zone) → entrée à l'ouverture de la bougie M1 suivante.
4. Stop : au-delà de l'extrême du mouvement (vente : plus haut depuis l'ouverture jusqu'à la complétion du BPR ;
   achat : plus bas). Pas de trade si le stop n'est pas au-delà de l'entrée.
5. Objectif 1:2 (standard ICT) ou 1:1. Stop prioritaire. Sortie forcée 16:00 New York.
6. Règle d'Anto : 1er trade du jour (Londres puis New York), 2e seulement si le 1er perd.
Coûts lib.COST (or 0,47 $, EURUSD 1,5 pip, Nasdaq 1,5 pt, S&P 0,75 pt). 100 € par R. Critère : lib.evaluate.
VARIANTE M15 (ajoutée le 18/10/2026 à la demande d'Anto, avant calcul) : `python3 run.py M15` → BPR en M15 dans
les 3 h après l'ouverture (12 bougies), retest M1 dans les 4 h, le reste inchangé.
Variantes : 2 entrées × 2 objectifs × 4 marchés (jugement par marché ; l'or est la question d'Anto).
"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa
MARKETS = ["XAUUSD", "EURUSD", "NASDAQ100", "SP500"]
SESS = [("Londres", "Europe/London", 8, 0), ("New York", "America/New_York", 9, 30)]


def minutes(ts):
    return ts.values.astype("datetime64[m]").astype(np.int64)


def bpr_trades(inst, tf=5, win=90, ret=180):
    df = lib.load(inst, "America/New_York")
    T = minutes(df["time"]); O, H, L, C = (df[c].values for c in ("open", "high", "low", "close"))
    days = pd.bdate_range("2011-01-01", lib.DATA_END)
    rows = []
    for d in days:
        end_ny = int(minutes(pd.Series([pd.Timestamp(d.date()).tz_localize("America/New_York") + pd.Timedelta(hours=16)]).dt.tz_convert("UTC"))[0])
        for sname, tz, hh, mm in SESS:
            t0 = int(minutes(pd.Series([pd.Timestamp(d.date()).tz_localize(tz) + pd.Timedelta(hours=hh, minutes=mm)]).dt.tz_convert("UTC"))[0])
            a, z = np.searchsorted(T, t0), np.searchsorted(T, t0 + win)
            if z - a < 0.85 * win:
                continue
            k = (T[a:z] - t0) // tf
            nb = int(k.max()) + 1
            h5 = np.full(nb, -np.inf); l5 = np.full(nb, np.inf)
            np.maximum.at(h5, k, H[a:z]); np.minimum.at(l5, k, L[a:z])
            if not (np.isfinite(h5).all() and np.isfinite(l5).all()):
                continue
            fv = []  # (bar, dir, lo, hi)
            for i in range(2, nb):
                if l5[i] > h5[i - 2]:
                    fv.append((i, 1, h5[i - 2], l5[i]))
                elif h5[i] < l5[i - 2]:
                    fv.append((i, -1, h5[i], l5[i - 2]))
            found = None
            for x in range(len(fv)):
                for y in range(x + 1, len(fv)):
                    if fv[y][1] != fv[x][1]:
                        lo, hi = max(fv[x][2], fv[y][2]), min(fv[x][3], fv[y][3])
                        if lo < hi:
                            found = (fv[y][0], fv[y][1], lo, hi); break
                if found:
                    break
            if not found:
                continue
            ib, d_, lo, hi = found
            tc = t0 + tf * (ib + 1)                        # clôture de la bougie M5 qui complète le BPR
            ext_hi, ext_lo = h5[:ib + 1].max(), l5[:ib + 1].min()
            stop = ext_hi if d_ == -1 else ext_lo
            near = lo if d_ == -1 else hi                 # bord proche (vente : bas de zone ; achat : haut de zone)
            s, e_lim = np.searchsorted(T, tc), np.searchsorted(T, min(tc + ret, end_ny))
            iend = np.searchsorted(T, end_ny)
            if s >= e_lim:
                continue
            touch = (H[s:e_lim] >= near) if d_ == -1 else (L[s:e_lim] <= near)
            if not touch.any():
                continue
            kt = s + int(np.argmax(touch))
            for mode in ("L", "C"):
                if mode == "L":
                    ke, entry = kt, (max(O[kt], near) if d_ == -1 else min(O[kt], near))
                else:
                    conf = (C[kt:e_lim] < lo) if d_ == -1 else (C[kt:e_lim] > hi)
                    stopped = (H[kt:e_lim] >= stop) if d_ == -1 else (L[kt:e_lim] <= stop)
                    if not conf.any():
                        continue
                    kc = kt + int(np.argmax(conf))
                    if stopped.any() and kt + int(np.argmax(stopped)) <= kc:
                        continue
                    ke = kc + 1
                    if ke >= iend:
                        continue
                    entry = O[ke]
                risk = (stop - entry) * (-d_) if d_ == -1 else (entry - stop)
                risk = (entry - stop) * d_
                if risk <= 0 or ke >= iend:
                    continue
                for tpm in (2, 1):
                    tp = entry + d_ * tpm * risk
                    hs, ls, os_ = H[ke:iend], L[ke:iend], O[ke:iend]
                    hs_s = (ls <= stop) if d_ == 1 else (hs >= stop)
                    hs_t = (hs >= tp) if d_ == 1 else (ls <= tp)
                    if mode == "L":
                        hs_t = hs_t.copy(); hs_t[0] = False   # pas d'objectif dans la minute du remplissage limite
                    ks = int(np.argmax(hs_s)) if hs_s.any() else len(hs)
                    ktp = int(np.argmax(hs_t)) if hs_t.any() else len(hs)
                    if ks == len(hs) and ktp == len(hs):
                        px, kx = C[iend - 1], iend - 1
                    elif ks <= ktp:
                        px = os_[ks] if (ks > 0 and ((os_[ks] < stop) if d_ == 1 else (os_[ks] > stop))) else stop; kx = ke + ks
                    else:
                        px = os_[ktp] if (ktp > 0 and ((os_[ktp] > tp) if d_ == 1 else (os_[ktp] < tp))) else tp; kx = ke + ktp
                    rows.append({"instrument": inst, "session": sname, "entree": mode, "tp": tpm, "day": d,
                                 "t_in": int(T[ke]), "t_out": int(T[kx]), "d": d_, "entry": entry, "stop": stop,
                                 "zone_lo": lo, "zone_hi": hi, "risque": risk, "gross_r": (px - entry) * d_ / risk,
                                 "cost_r": lib.COST[inst] / risk})
    return pd.DataFrame(rows)


def main():
    m15 = len(sys.argv) > 1 and sys.argv[1] == "M15"
    t = pd.concat([bpr_trades(i, 15, 180, 240) if m15 else bpr_trades(i) for i in MARKETS], ignore_index=True)
    t.to_csv(os.path.join(HERE, "candidats_M15.csv.gz" if m15 else "candidats.csv.gz"), index=False, float_format="%.6f")
    out = []
    for (inst, mode, tpm), g in t.groupby(["instrument", "entree", "tp"]):
        taken = lib.regle_anto(g)
        r = lib.evaluate(taken, f"{inst} entrée {mode} TP 1:{tpm}"); s = lib.stats_jour(taken)
        r["jour"] = s; r["brut"] = float(taken.gross_r.mean()); r["cout_median_r"] = float(taken.cost_r.median()); out.append(r)
        print(lib.line(r), f"| brut {taken.gross_r.mean():+.3f} coût méd {taken.cost_r.median():.2f}R |", lib.line_jour(s))
    json.dump(out, open(os.path.join(HERE, "results_M15.json" if m15 else "results.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
