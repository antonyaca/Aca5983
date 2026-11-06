"""Backtest ORB 30 min (achats seuls) + Williams k=0.5, Nasdaq 100 CFD, règles du script Pine orb_williams_nasdaq.pine.
Données HistData M1 (bid, UTC corrigé). Séance 09:30-16:00 New York. Coût 1,5 pt aller-retour. 100 EUR par R.
Ambiguïtés intrabar résolues contre nous (bougie d'entrée qui touche aussi le stop = perte)."""
import glob, sys
import numpy as np, pandas as pd

ROOT = sys.argv[1]
COST = 1.5
files = sorted(glob.glob(f"{ROOT}/data/NASDAQ100/NASDAQ100_M1_*.csv.gz"))
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
df["time"] = pd.to_datetime(df["time"], utc=True)
df = df.drop_duplicates("time").sort_values("time")
ny = df["time"].dt.tz_convert("America/New_York")
df["m"] = ny.dt.hour * 60 + ny.dt.minute
df["d"] = ny.dt.date
df = df[(df.m >= 570) & (df.m < 960)]

trades = []
prev_range = None
for d, g in df.groupby("d", sort=True):
    if len(g) < 300:          # séance incomplète (trou de données / demi-journée) : on saute, range non mis à jour
        prev_range = None
        continue
    o, h, l, c, m = g.open.values, g.high.values, g.low.values, g.close.values, g.m.values
    exit_px = c[-1]
    # ---------- Williams
    if prev_range:
        op = o[0]; up = op + 0.5 * prev_range; dn = op - 0.5 * prev_range
        for i in range(len(g)):
            hu, hd = h[i] >= up, l[i] <= dn
            if hu and hd: break
            if hu or hd:
                side = 1 if hu else -1
                entry = up if hu else dn
                risk = abs(entry - op)
                stopped = False
                for j in range(i, len(g)):
                    if (side == 1 and l[j] <= op) or (side == -1 and h[j] >= op):
                        stopped = True; break
                r = -1.0 if stopped else side * (exit_px - entry) / risk
                trades.append((d, "Williams", "achat" if side == 1 else "vente", r, COST / risk))
                break
    # ---------- ORB 30 min, achats seuls
    rng = m < 600
    if rng.sum() >= 25:
        oh, ol = h[rng].max(), l[rng].min()
        risk = oh - ol
        for i in np.where(~rng)[0]:
            if m[i] >= 900: break
            hu, hd = h[i] > oh, l[i] < ol
            if hu and hd: break
            if hd: break
            if hu:
                stopped = any(l[j] <= ol for j in range(i, len(g)))
                r = -1.0 if stopped else (exit_px - oh) / risk
                trades.append((d, "ORB", "achat", r, COST / risk))
                break
    prev_range = h.max() - l.min()

t = pd.DataFrame(trades, columns=["day", "strat", "side", "gross_r", "cost_r"])
t["day"] = pd.to_datetime(t["day"])
t["net_r"] = t.gross_r - t.cost_r
t["eur"] = t.net_r * 100
t = t[t.day >= "2011-01-01"]
t.to_csv(sys.argv[2], index=False)

def stats(x, label):
    n = len(x)
    if n == 0: return
    e = x.net_r.mean(); tstat = e / x.net_r.std() * np.sqrt(n)
    eq = x.sort_values("day").eur.cumsum(); dd = (eq.cummax() - eq).max()
    yrs = (x.day.max() - x.day.min()).days / 365.25
    yearly = x.groupby(x.day.dt.year).eur.sum()
    print(f"{label:34s} n={n:5d} win={100*(x.net_r>0).mean():4.1f}% E={e:+.3f}R t={tstat:+.2f} "
          f"total={x.eur.sum():+9.0f}€ /an={x.eur.sum()/yrs:+7.0f}€ DD={dd:6.0f}€ ans+={(yearly>0).sum()}/{len(yearly)}")

for name, sub in [("Combiné", t), ("Williams", t[t.strat == "Williams"]), ("ORB", t[t.strat == "ORB"]),
                  ("Williams achats", t[(t.strat == "Williams") & (t.side == "achat")]),
                  ("Williams ventes", t[(t.strat == "Williams") & (t.side == "vente")])]:
    stats(sub, name + " 2011-2026")
    stats(sub[sub.day < "2019-01-01"], name + " 2011-2018")
    stats(sub[sub.day >= "2019-01-01"], name + " 2019-2026")
    stats(sub[sub.day >= "2025-11-01"], name + " 12 derniers mois")
print()
print(t.groupby([t.day.dt.year, "strat"]).eur.sum().unstack().round(0).to_string())
# objectif perso : semaines positives
w = t.groupby(t.day.dt.to_period("W")).eur.sum()
print(f"\nSemaines positives : {100*(w>0).mean():.0f}%  | semaines >= +500 € : {100*(w>=500).mean():.0f}%  | pire semaine {w.min():.0f} €")
print("Gross E (avant frais) combiné :", round(t.gross_r.mean(), 3), "| coût moyen :", round(t.cost_r.mean(), 3), "R")
