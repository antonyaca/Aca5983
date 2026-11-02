"""Cassure ATR depuis l'ouverture façon Andrea Unger — Nasdaq 100 (02/11/2026). Règles fixées AVANT calcul.

Source de l'idée : Unger Academy, stratégie S&P intraday (2017) — deux niveaux d'ordres placés à une distance de
l'ouverture calculée avec l'ATR ; position fermée au plus tard en fin de séance.

Règles communes (même moteur que le Williams validé, jour/plan_valides/williams_2e_chance.py, trade 1) :
- Séance 09:30-16:00 NY ; jours incomplets écartés (lib : >= 90 % des minutes et minute 09:30 présente).
- ATR14 = moyenne des 14 « true ranges » des séances PRÉCÉDENTES (H/L de séance, clôture de la séance d'avant).
- Niveaux = ouverture 09:30 ± k × ATR14 ; 1er niveau touché ; si les deux dans la même minute → pas de trade.
- Entrée au niveau (ou à l'ouverture de la minute si gap au-delà) ; stop = ouverture du jour ; sortie 16:00.
- 1 trade max par jour. 1 R = distance entrée-stop ; 100 € par R.

Variantes (5, paramètres ronds, pas d'optimisation) :
  U1 k = 0,5 achat + vente   U2 k = 0,25   U3 k = 1,0   U4 k = 0,5 achat seul   U5 k = 0,5 vente seule
  + référence W : Williams validé (k = 0,5 × amplitude de la VEILLE) recalculé avec le même moteur.

Coûts aller-retour (recherche du 02/11/2026), en points au niveau actuel du Nasdaq puis PROPORTIONNELS au prix
(un écart en points n'avait pas la même taille quand le Nasdaq valait 2 300 en 2011) :
- CFD Pepperstone US Tech 100 : spread moyen 1,2 pt (tradingbeasts) + glissement 0,5 pt = 1,7 pt.
- MNQ (micro future, 2 $/pt) : frais ~0,92-1,04 $ A/R (Topstep) ≈ 0,5 pt + 1 tick de spread (0,25) + 0,5 pt de
  glissement sur ordres stop = 1,25 pt.
- NQ (future standard, 20 $/pt) : frais ~3,86 $ A/R ≈ 0,2 pt + 0,25 + 0,5 = 0,95 pt.
Critère : lib.evaluate (découverte 2011-2018 / validation 2019-2026, t ≥ 3, frais ×2, etc.).
"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(HERE)
sys.path.insert(0, CAMP)
import lib  # noqa

OP, CL = 570, 960
COSTS_PT = {"CFD Pepperstone": 1.7, "MNQ": 1.25, "NQ": 0.95}


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


def sessions(df):
    out = []
    for day, g in df.groupby("day"):
        if day.dayofweek >= 5:
            continue
        hm, O, H, L, C = (g[c].values for c in ("hm", "open", "high", "low", "close"))
        s = (hm >= OP) & (hm < CL)
        if not (s.sum() >= 0.9 * (CL - OP) and (hm == OP).any()):
            continue
        out.append((day, hm, O, H, L, C, s))
    return out


def run(sess, dist_fn, sides):
    rows = []
    for i, (day, hm, O, H, L, C, s) in enumerate(sess):
        dist = dist_fn(i)
        if dist is None or not np.isfinite(dist) or dist <= 0:
            continue
        k0 = int(np.where(hm == OP)[0][0]); op = O[k0]
        up, dn = op + dist, op - dist
        idx = np.where(s)[0]
        hu, hd = H[idx] >= up, L[idx] <= dn
        if 1 not in sides: hu[:] = False
        if -1 not in sides: hd[:] = False
        hit = hu | hd
        if not hit.any():
            continue
        j = int(hit.argmax())
        if hu[j] and hd[j]:
            continue
        k, d = idx[j], (1 if hu[j] else -1)
        entry = max(O[k], up) if d == 1 else min(O[k], dn)
        risk = (entry - op) * d
        if risk <= 0:
            continue
        px, _ = exit_price(hm, O, H, L, C, k, d, op)
        rows.append({"day": day, "d": d, "entry": entry, "exit": px, "risque": risk, "gross_r": (px - entry) * d / risk})
    return pd.DataFrame(rows)


def main():
    df = lib.load("NASDAQ100", "America/New_York")
    sess = sessions(df)
    # séance : H, L, C ; true range sur séances
    SH = np.array([H[s].max() for (_, _, _, H, _, _, s) in sess])
    SL = np.array([L[s].min() for (_, _, _, _, L, _, s) in sess])
    SC = np.array([C[np.where(s)[0][-1]] for (_, _, _, _, _, C, s) in sess])
    pc = np.r_[np.nan, SC[:-1]]
    tr = np.nanmax(np.c_[SH - SL, np.abs(SH - pc), np.abs(SL - pc)], axis=1)
    atr14 = pd.Series(tr).rolling(14).mean().shift(1).values      # séances précédentes uniquement
    rng_prev = np.r_[np.nan, (SH - SL)[:-1]]
    price_now = SC[-1]
    variants = {
        "W  Williams k0,5 (réf.)": (lambda i: 0.5 * rng_prev[i], (1, -1)),
        "U1 ATR k0,5 achat+vente": (lambda i: 0.5 * atr14[i], (1, -1)),
        "U2 ATR k0,25 achat+vente": (lambda i: 0.25 * atr14[i], (1, -1)),
        "U3 ATR k1,0 achat+vente": (lambda i: 1.0 * atr14[i], (1, -1)),
        "U4 ATR k0,5 achat seul": (lambda i: 0.5 * atr14[i], (1,)),
        "U5 ATR k0,5 vente seule": (lambda i: 0.5 * atr14[i], (-1,)),
    }
    out = {"prix_nasdaq_fin_donnees": float(price_now), "couts_pt": COSTS_PT, "resultats": []}
    print(f"Nasdaq fin des données : {price_now:.0f} — coûts proportionnels au prix\n")
    for name, (fn, sides) in variants.items():
        t = run(sess, fn, sides)
        for cname, cpt in COSTS_PT.items():
            u = t.assign(cost_r=(t.entry * cpt / price_now / t.risque).values)
            r = lib.evaluate(u, f"{name} · {cname}")
            r["stats_jour"] = lib.stats_jour(u)
            out["resultats"].append(r)
            print(lib.line(r))
        print()
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
