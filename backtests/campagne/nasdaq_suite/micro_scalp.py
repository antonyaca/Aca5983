"""Micro-scalping « +2 / −1 » d'Anto (22/10/2026) : objectif = 2 u, stop = u, rejoué en boucle, pour chaque heure (Paris).
Règles fixées AVANT calcul.
Nasdaq, 2011-2026. Entrées échantillonnées toutes les 10 minutes de chaque heure (minutes 0, 10, ..., 50), à l'ouverture
de la minute ; sens = celui de la minute précédente (« momentum ») ou l'inverse (« retour ») ; u ∈ {5, 10, 20} points.
Sortie au 1er niveau touché (stop prioritaire dans la même minute), au plus 240 minutes après.
Coût aller-retour : 1,5 pt (hypothèse du dépôt) et 1,0 pt (optimiste). Résultat en unités de risque (1 u = 1 R).
Puis : la meilleure combinaison choisie sur 2011-2018 est jugée sur 2019-2026, et on calcule la probabilité de finir
une journée à +100 € avant −100 € en enchaînant les trades (simulation sur les trades réels, 1 R = 1 €... converti).
"""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); sys.path.insert(0, C)
import lib  # noqa
df = lib.load("NASDAQ100", "Europe/Paris")
df = df[df.day >= "2010-12-01"].reset_index(drop=True)
T = df["time"].values.astype("datetime64[m]").astype(np.int64)
O, Hh, L, Cc, hm = (df[c].values for c in ("open", "high", "low", "close", "hm"))
day = df["day"].values
idx = np.flatnonzero((hm % 10 == 0) & (np.r_[0, np.diff(T)] == 1))    # minute précédente présente
idx = idx[idx + 241 < len(T)]
rows = []
for u in (5, 10, 20):
    for i in idx:
        prev = Cc[i - 1] - O[i - 1]
        if prev == 0:
            continue
        for mode, d in (("momentum", 1 if prev > 0 else -1), ("retour", -1 if prev > 0 else 1)):
            e = O[i]; stop = e - d * u; tp = e + d * 2 * u
            hs, ls = Hh[i:i + 240], L[i:i + 240]
            if T[i + 239] - T[i] > 300:      # trou de cotation (week-end, pause) → on ignore
                break
            s_hit = (ls <= stop) if d == 1 else (hs >= stop)
            t_hit = (hs >= tp) if d == 1 else (ls <= tp)
            ks = np.argmax(s_hit) if s_hit.any() else 999; kt = np.argmax(t_hit) if t_hit.any() else 999
            if ks == 999 and kt == 999:
                g = (Cc[i + 239] - e) * d / u
            else:
                g = -1.0 if ks <= kt else 2.0
            rows.append((u, mode, int(hm[i] // 60), day[i], g))
t = pd.DataFrame(rows, columns=["u", "mode", "heure", "day", "gross_r"])
t["day"] = pd.to_datetime(t["day"])
t.to_csv(os.path.join(H, "micro_scalp.csv.gz"), index=False, float_format="%.4f")
for cost in (1.5, 1.0):
    t["net"] = t.gross_r - cost / t.u
    g = t.groupby(["u", "mode", "heure"]).net.mean().unstack("heure")
    print(f"\n== Espérance nette par trade (R), coût {cost} pt — lignes : stop u (pts) / sens ; colonnes : heure de Paris")
    print(g.round(2).to_string())
# meilleure combinaison choisie sur 2011-2018, jugée sur 2019-2026 (coût 1,5 pt)
t["net"] = t.gross_r - 1.5 / t.u
d_ = t[t.day < lib.SPLIT].groupby(["u", "mode", "heure"]).net.agg(["mean", "size"])
best = d_[d_["size"] > 2000]["mean"].idxmax()
v = t[(t.day >= lib.SPLIT) & (t.u == best[0]) & (t["mode"] == best[1]) & (t.heure == best[2])].net
print(f"\nMeilleure en 2011-2018 : stop {best[0]} pts, {best[1]}, {best[2]}h → {d_.loc[best, 'mean']:+.3f} R ; "
      f"en 2019-2026 : {v.mean():+.3f} R (t {v.mean()/v.std()*np.sqrt(len(v)):.2f}, {len(v)} trades)")
print("Part des 144 combinaisons positives en 2011-2018 :", f"{(d_['mean'] > 0).mean()*100:.0f} %")
