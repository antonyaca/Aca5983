"""Optimisation TP/SL de la stratégie VWAP + EMA 9 (demande d'Anto, 18/10/2026) — protocole fixé AVANT calcul.

Signal identique à run.py (croisement EMA 9 / TWAP, M5, entrées 09:35-12:00 NY, entrée à l'ouverture suivante).
Grille : stop dur ∈ {0,15 ; 0,25 ; 0,5 ; 0,75 ; 1,0} × ATR14 journalier ; objectif ∈ {0,5 ; 1 ; 1,5 ; 2 ; 3 R ; aucun} ;
sortie sur clôture au-delà de l'EMA 9 ∈ {oui, non} → 60 réglages par marché (Nasdaq, S&P), 120 au total.
Sortie forcée 16:00 NY ; un trade à la fois ; règle d'Anto (1er trade + 2e si perte).
Coût proportionnel au prix (1,25 pb Nasdaq, 2,1 pb S&P) : l'hypothèse la plus favorable, pour laisser toutes ses
chances à la stratégie.
MÉTHODE (anti sur-optimisation) : 1) classement des 120 réglages sur 2011-2018 UNIQUEMENT (espérance nette, ≥ 300 trades) ;
2) le meilleur réglage de chaque marché est jugé UNE fois sur 2019-2026 ; 3) on rapporte aussi la part des 120 réglages
positifs en 2019-2026 et la corrélation de rang découverte → validation.
"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa
PROP = {"NASDAQ100": 1.25e-4, "SP500": 2.1e-4}
SLS, TPS, EMAX = (0.15, 0.25, 0.5, 0.75, 1.0), (0.5, 1, 1.5, 2, 3, None), (True, False)


def sessions(inst):
    df = lib.load(inst, "America/New_York")
    m5 = df.set_index("time")[["open", "high", "low", "close"]].resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    loc = m5.index.tz_convert("America/New_York")
    m5["day"] = loc.tz_localize(None).normalize(); m5["hm"] = loc.hour * 60 + loc.minute
    m5["ema"] = m5.close.ewm(span=9, adjust=False).mean()
    s = df[(df.hm >= 570) & (df.hm < 960)].groupby("day").agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
    pc = s.c.shift()
    atr = pd.concat([s.h - s.l, (s.h - pc).abs(), (s.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    out = []
    for day, g in m5[(m5.hm >= 570) & (m5.hm < 960)].groupby("day"):
        if day.dayofweek >= 5 or len(g) < 70 or g.hm.iloc[0] != 570 or day not in atr.index or not np.isfinite(atr[day]):
            continue
        O, H, L, C, E, hm = (g[c].values for c in ("open", "high", "low", "close", "ema", "hm"))
        tw = np.cumsum((H + L + C) / 3) / np.arange(1, len(C) + 1)
        up = np.r_[False, (E[1:] > tw[1:]) & (E[:-1] <= tw[:-1])]
        dn = np.r_[False, (E[1:] < tw[1:]) & (E[:-1] >= tw[:-1])]
        sig = np.where(up, 1, np.where(dn, -1, 0)); sig[(hm + 5 > 720)] = 0; sig[-1] = 0
        if sig.any():
            out.append((day, atr[day], O, H, L, C, E, hm, sig))
    return out


def run_combo(S, inst, slm, tpm, emax):
    rows = []
    for day, atr, O, H, L, C, E, hm, sig in S:
        R = slm * atr; busy = -1; n = len(C)
        for i in np.flatnonzero(sig):
            e = i + 1
            if e <= busy:
                continue
            d = int(sig[i]); entry = O[e]; stop = entry - d * R
            tp = entry + d * tpm * R if tpm else None
            px, j = None, e
            while j < n:
                if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                    px = O[j] if (j > e and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop; break
                if tp is not None and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
                    px = O[j] if (j > e and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp; break
                if emax and ((C[j] < E[j]) if d == 1 else (C[j] > E[j])) and j + 1 < n:
                    j += 1; px = O[j]; break
                j += 1
            if px is None:
                px, j = C[-1], n - 1
            busy = j
            rows.append((day, int(hm[e]), int(hm[j]), (px - entry) * d / R, entry * PROP[inst] / R))
    t = pd.DataFrame(rows, columns=["day", "t_in", "t_out", "gross_r", "cost_r"])
    return lib.regle_anto(t)


def main():
    res = []
    for inst in ("NASDAQ100", "SP500"):
        S = sessions(inst)
        for slm in SLS:
            for tpm in TPS:
                for emax in EMAX:
                    t = run_combo(S, inst, slm, tpm, emax)
                    x = t.gross_r - t.cost_r
                    dsc, val = x[t.day < lib.SPLIT], x[t.day >= lib.SPLIT]
                    res.append({"instrument": inst, "sl_atr": slm, "tp_r": tpm, "sortie_ema9": emax,
                                "n_dec": len(dsc), "e_dec": float(dsc.mean()), "n_val": len(val), "e_val": float(val.mean()),
                                "t_val": float(val.mean() / val.std() * np.sqrt(len(val))),
                                "jours_pos_val": float((x[t.day >= lib.SPLIT].groupby(t.day).sum() > 0).mean() * 100)})
        print(inst, "ok", flush=True)
    r = pd.DataFrame(res)
    r.to_csv(os.path.join(HERE, "optimisation.csv"), index=False, float_format="%.4f")
    print("\nTop 5 sur la DÉCOUVERTE 2011-2018 (ce qu'un optimiseur choisirait), puis leur VALIDATION 2019-2026 :")
    for inst, g in r[r.n_dec >= 300].groupby("instrument"):
        print(g.sort_values("e_dec", ascending=False).head(5)[["instrument", "sl_atr", "tp_r", "sortie_ema9", "n_dec", "e_dec",
              "n_val", "e_val", "t_val", "jours_pos_val"]].round(3).to_string(index=False))
    print(f"\nRéglages positifs en découverte : {(r.e_dec > 0).sum()}/{len(r)} ; en validation : {(r.e_val > 0).sum()}/{len(r)} ;"
          f" positifs sur les deux : {((r.e_dec > 0) & (r.e_val > 0)).sum()}")
    print("Corrélation de rang découverte → validation :", round(r.e_dec.rank().corr(r.e_val.rank()), 2))
    print("Meilleur réglage en validation (connu seulement après coup) :")
    print(r.sort_values("e_val", ascending=False).head(3).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
