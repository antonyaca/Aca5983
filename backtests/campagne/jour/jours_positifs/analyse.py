"""Analyse descriptive des 16 variantes de run.py (aucune nouvelle variante, aucun nouveau signal).

1. Par variante : gain moyen / perte moyenne (nets), taux de réussite d'équilibre p* = perte / (gain + perte),
   marge = taux observé − p*, espérance brute.
2. Relation jours positifs ↔ espérance : corrélation de rang de Spearman sur les 16 variantes.
3. Information (hors verdict) : V01 et V04 avec un coût proportionnel au prix (1,25 pb aller-retour, l'hypothèse de
   hors_echantillon/README.md) puis avec un coût fixe de 0,75 pt (≈ contrat future NQ : 1 tick + commission) au lieu
   du coût fixe lib.COST de 1,5 pt. Même trades, seul le coût change.
4. Références hors budget (trades EXISTANTS des stratégies swing déjà validées, verification/verif_swing.py) :
   taux de réussite et jours positifs du RSI2 et des 3 baisses après lib.regle_anto (1 trade par jour).
Sortie : analyse.txt.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa: E402

T = pd.read_csv(os.path.join(HERE, "trades.csv.gz"), parse_dates=["day", "t_in", "t_out"])
R = json.load(open(os.path.join(HERE, "results.json")))
out = []


def p(s=""):
    print(s)
    out.append(s)


p("1. Structure gain / perte (trades pris, 2011-2026, nets de frais)")
p(f"{'var':4} {'réussite':>8} {'jours+':>7} {'gain moy':>9} {'perte moy':>10} {'p* équil.':>9} {'marge':>7} {'E brute':>8} {'E nette':>8} {'t':>6}")
rows = []
for v in sorted(R):
    t = T[(T.variante == v) & (T.day >= lib.START)]
    x = (t.gross_r - t.cost_r).values
    w, l = x[x > 0].mean(), -x[x < 0].mean()
    ps = l / (w + l)
    r = R[v]
    rows.append((v, r["taux_reussite"], r["jour"]["jours_positifs_pct_jours_trades"], r["net"]["e_r"], r["t_stat"]))
    p(f"{v:4} {r['taux_reussite']:7.1f}% {r['jour']['jours_positifs_pct_jours_trades']:6.1f}% {w:+9.3f} {-l:+10.3f} "
      f"{ps * 100:8.1f}% {r['taux_reussite'] - ps * 100:+6.1f} {r['brut']['e_r']:+8.3f} {r['net']['e_r']:+8.3f} {r['t_stat']:+6.2f}")
d = pd.DataFrame(rows, columns=["v", "reussite", "jours", "e", "t"])
p()
p("2. Relation jours positifs ↔ espérance nette (16 variantes)")
p(f"   Spearman(jours positifs %, E nette) = {d['jours'].rank().corr(d['e'].rank()):+.2f} ; "
  f"Spearman(taux de réussite, E nette) = {d['reussite'].rank().corr(d['e'].rank()):+.2f}")
for lo, hi in ((0, 55), (55, 65), (65, 101)):
    g = d[(d.jours >= lo) & (d.jours < hi)]
    p(f"   jours positifs {lo:>2}-{min(hi, 100)} % : {len(g):2d} variantes, E nette médiane {g.e.median():+.3f} R, "
      f"E > 0 : {', '.join(g[g.e > 0].v) or 'aucune'}")
p("   Même signal Williams, sorties différentes : " + " ; ".join(
    f"{v} jours+ {R[v]['jour']['jours_positifs_pct_jours_trades']:.0f} % E {R[v]['net']['e_r']:+.3f} DD {R[v]['net']['max_dd_eur']:.0f} € "
    f"pire série {R[v]['jour']['pire_serie_jours_perdants']} j" for v in ("V01", "V03", "V02", "V04")))

p()
p("3. Information hors verdict — coût proportionnel au prix (1,25 pb aller-retour) au lieu de 1,5 pt fixe")
for v in ("V01", "V04"):
    t = T[T.variante == v].copy()
    t["cost_r"] = 1.25e-4 * t["entry"] / t["risque"]
    r = lib.evaluate(t, f"{v} coût ∝ prix (info)")
    p("   " + lib.line(r))
    t["cost_r"] = 0.75 / t["risque"]
    r = lib.evaluate(t, f"{v} coût fixe 0,75 pt (info)")
    s = lib.stats_jour(t)
    p("   " + lib.line(r) + f" | jours+ {s['jours_positifs_pct_jours_trades']} % | {s['eur_par_an']} €/an")
    t2 = T[(T.variante == v) & (T.day >= lib.SPLIT)]
    x = t2.gross_r - t2.cost_r
    p(f"   {v} coût fixe, 2019-2026 seul : n {len(x)} E {x.mean():+.3f} t {x.mean() / x.std() * np.sqrt(len(x)):+.2f}")

p()
p("4. Références hors budget : stratégies swing DÉJÀ validées (trades existants), 1 trade par jour (lib.regle_anto)")
for name in ("RSI2", "3_baisses"):
    f = os.path.join(CAMP, "verification", f"trades_{name}.csv.gz")
    t = pd.read_csv(f, parse_dates=["day"])
    t["t_in"], t["t_out"] = t["day"], t["day"] + pd.Timedelta(days=1)   # exécution 15:55 ; 2e trade impossible le même jour
    t["ordre"] = t["instrument"].map({"NASDAQ100": 0, "SP500": 1})
    t = t.sort_values(["day", "t_in", "ordre"], kind="mergesort").reset_index(drop=True)
    k = lib.regle_anto(t)
    r = lib.evaluate(k, f"réf. {name} (swing validé)")
    s = lib.stats_jour(k)
    x = (k[k.day >= lib.START].gross_r - k[k.day >= lib.START].cost_r)
    p("   " + lib.line(r))
    p(f"     réussite {(x > 0).mean() * 100:.1f} % | " + lib.line_jour(s) + f" | pire jour {s['pire_jour_eur']} €")
open(os.path.join(HERE, "analyse.txt"), "w").write("\n".join(out) + "\n")
