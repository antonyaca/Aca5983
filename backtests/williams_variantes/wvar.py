"""Campagne de variantes Williams. Sortie clôture 16:00 NY sauf mention. Coût fixe par marché (aller-retour), 100 €/R.
Chaque variante change UNE dimension par rapport à la référence (k=0,5, range veille, ancre ouverture, stop ouverture,
deux sens, entrée toute la séance)."""
import glob, sys, pickle, os
import numpy as np, pandas as pd

ROOT = sys.argv[1]; INST = sys.argv[2]; COST = {"NASDAQ100": 1.5, "SP500": 0.75, "XAUUSD": 0.47, "FTSE100": 1.5}[INST] * float(os.environ.get("CM", "1"))
cache = f"days_{INST}.pkl"
if os.path.exists(cache):
    days = pickle.load(open(cache, "rb"))
else:
    df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{ROOT}/data/{INST}/{INST}_M1_*.csv.gz"))])
    df["time"] = pd.to_datetime(df["time"], utc=True); df = df.drop_duplicates("time").sort_values("time")
    ny = df.time.dt.tz_convert("America/New_York"); df["m"] = ny.dt.hour * 60 + ny.dt.minute; df["d"] = ny.dt.date
    df = df[(df.m >= 570) & (df.m < 960)]
    days = []
    for d, g in df.groupby("d"):
        if len(g) >= 300 and g.m.iloc[0] <= 575 and pd.Timestamp(d).dayofweek < 5:
            days.append((pd.Timestamp(d), g.open.values, g.high.values, g.low.values, g.close.values, g.m.values))
    pickle.dump(days, open(cache, "wb"))

D = pd.DataFrame({"day": [x[0] for x in days], "O": [x[1][0] for x in days], "H": [x[2].max() for x in days],
                  "L": [x[3].min() for x in days], "C": [x[4][-1] for x in days]})
pc = D.C.shift()
D["rng"] = D.H - D.L
D["tr"] = pd.concat([D.rng, (D.H - pc).abs(), (D.L - pc).abs()], axis=1).max(axis=1)
D["prev_rng"] = D.rng.shift()
D["prev_tr"] = D.tr.shift()
for n in (3, 5, 10, 14): D[f"atr{n}"] = D.tr.rolling(n).mean().shift()
D["sma200"] = D.C.rolling(200).mean().shift(); D["sma50"] = D.C.rolling(50).mean().shift()
D["pc"] = pc
D["gap"] = (D.O - pc) / D.atr14
D["prev_dir"] = np.sign(pc - D.O.shift())          # sens de la séance de la veille
D["nr4"] = D.prev_rng <= D.rng.rolling(4).min().shift()  # veille = plus petit range des 4 dernières séances

REF = dict(k=0.5, vol="prev_rng", anchor="open", stop="anchor", side="both", tmax=960, tmin=570, texit=960,
           trend=None, dow=None, gapf=None, trail=None, filt=None)

def run(p):
    out = []
    for i in range(1, len(days)):
        row = D.iloc[i]; day, o, h, l, c, m = days[i]
        vol = row[p["vol"]]
        if not np.isfinite(vol) or vol <= 0: continue
        if p["dow"] is not None and day.dayofweek not in p["dow"]: continue
        if p["filt"] == "nr4" and not row.nr4: continue
        if p["filt"] == "not_nr4" and row.nr4: continue
        if p["gapf"] == "small" and abs(row.gap) > 0.3: continue
        if p["gapf"] == "big" and abs(row.gap) <= p.get("gapthr", 0.3): continue
        if p["gapf"] == "with" or p["gapf"] == "against":
            if abs(row.gap) <= p.get("gapthr", 0.3): continue
        anchor = o[0] if p["anchor"] == "open" else row.pc
        up, dn = anchor + p["k"] * vol, anchor - p["k"] * vol
        allow_long = allow_short = True
        if p["side"] == "long": allow_short = False
        if p["side"] == "short": allow_long = False
        if p["trend"]:
            if not np.isfinite(row[p["trend"]]): continue
            if o[0] > row[p["trend"]]: allow_short = False
            else: allow_long = False
        if p["side"] == "with_prev":
            allow_long, allow_short = row.prev_dir > 0, row.prev_dir < 0
        if p["side"] == "against_prev":
            allow_long, allow_short = row.prev_dir < 0, row.prev_dir > 0
        if p["gapf"] == "with":
            allow_long, allow_short = allow_long and row.gap > 0, allow_short and row.gap < 0
        if p["gapf"] == "against":
            allow_long, allow_short = allow_long and row.gap < 0, allow_short and row.gap > 0
        win = (m >= p["tmin"]) & (m < p["tmax"])
        hu = (h >= up) & win; hd = (l <= dn) & win
        iu = np.argmax(hu) if hu.any() else 10**9; idn = np.argmax(hd) if hd.any() else 10**9
        if iu == idn == 10**9 or iu == idn: continue
        if iu < idn:
            if not allow_long: continue
            s, j0 = 1, iu; e = max(up, o[j0])     # prix déjà au-delà du niveau : remplissage au marché
        else:
            if not allow_short: continue
            s, j0 = -1, idn; e = min(dn, o[j0])
        if p["stop"] == "anchor": st = anchor
        elif p["stop"] == "half": st = e - s * 0.5 * p["k"] * vol
        elif p["stop"] == "atr": st = e - s * row.atr14 * 0.5
        elif p["stop"] == "opposite": st = dn if s == 1 else up
        R = abs(e - st)
        if R <= 0 or (s == 1 and st >= e) or (s == -1 and st <= e): continue
        # sortie
        r = None; best = 0.0; stop = st
        for j in range(j0, len(m)):
            if m[j] >= p["texit"]: r = s * (o[j] - e) / R; break
            worst = (l[j] - e) / R if s == 1 else (e - h[j]) / R
            fav = (h[j] - e) / R if s == 1 else (e - l[j]) / R
            sr = s * (stop - e) / R
            if worst <= sr: r = sr; break
            if j > j0: best = max(best, fav)
            if p["trail"]:
                ns = e + s * (best - p["trail"]) * R
                stop = max(stop, ns) if s == 1 else min(stop, ns)
        if r is None: r = s * (c[-1] - e) / R
        out.append((day, r, COST / R, s))
    t = pd.DataFrame(out, columns=["day", "g", "c", "s"]); t["r"] = t.g - t.c
    return t[t.day >= "2011-01-01"]

def summ(t):
    def part(x):
        return x.r.mean() if len(x) else np.nan
    a, b = t[t.day < "2019-01-01"], t[t.day >= "2019-01-01"]
    eq = (t.r * 100).cumsum(); dd = (eq.cummax().clip(lower=0) - eq).max()
    yrs = 15.83; y = t.groupby(t.day.dt.year).r.sum()
    tstat = t.r.mean() / t.r.std() * np.sqrt(len(t))
    return dict(n=len(t), E=t.r.mean(), brut=t.g.mean(), t=tstat, an=t.r.sum() * 100 / yrs, an1926=b.r.sum() * 100 / 7.83,
                DD=dd, E1118=part(a), E1926=part(b), ans=f"{(y > 0).sum()}/{len(y)}")

V = {"Référence": {}}
for k in (0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 1.0): V[f"k = {k}"] = dict(k=k)
for v, lab in [("prev_tr", "TR veille (avec gap)"), ("atr3", "ATR3"), ("atr5", "ATR5"), ("atr10", "ATR10"), ("atr14", "ATR14")]:
    V[f"Volatilité : {lab}"] = dict(vol=v)
V["Ancre : clôture veille"] = dict(anchor="pclose")
V["Stop : mi-distance"] = dict(stop="half"); V["Stop : 0,5 ATR14"] = dict(stop="atr"); V["Stop : niveau opposé"] = dict(stop="opposite")
V["Achats seuls"] = dict(side="long"); V["Ventes seules"] = dict(side="short")
V["Sens de la SMA200"] = dict(trend="sma200"); V["Sens de la SMA50"] = dict(trend="sma50")
V["Sens de la veille"] = dict(side="with_prev"); V["Contre la veille"] = dict(side="against_prev")
for tm, lab in [(630, "16h30"), (690, "17h30"), (780, "19h30"), (870, "21h")]: V[f"Entrée avant {lab} Paris"] = dict(tmax=tm)
V["Entrée après 16h Paris"] = dict(tmin=600)
for dw, lab in [((0,), "lundi"), ((1,), "mardi"), ((2,), "mercredi"), ((3,), "jeudi"), ((4,), "vendredi")]: V[f"Seulement {lab}"] = dict(dow=dw)
V["Petit gap (< 0,3 ATR)"] = dict(gapf="small"); V["Gros gap (> 0,3 ATR)"] = dict(gapf="big")
V["Veille = NR4"] = dict(filt="nr4"); V["Veille ≠ NR4"] = dict(filt="not_nr4")
V["Trailing 1R"] = dict(trail=1.0)
if len(sys.argv) > 3:
    import json; V = json.loads(sys.argv[3])

rows = []
for name, ch in V.items():
    p = dict(REF); p.update(ch); s = summ(run(p)); s["variante"] = name; rows.append(s)
    print(f"{name:28} n={s['n']:5d} E={s['E']:+.3f} (brut {s['brut']:+.3f}) t={s['t']:+.2f} €/an={s['an']:+6.0f} "
          f"19-26 €/an={s['an1926']:+6.0f} DD={s['DD']:5.0f} | 11-18 {s['E1118']:+.3f} 19-26 {s['E1926']:+.3f} | ans+ {s['ans']}", flush=True)
pd.DataFrame(rows).to_csv(f"variantes_{INST}{'_combo' if len(sys.argv) > 3 else ''}.csv", index=False)
