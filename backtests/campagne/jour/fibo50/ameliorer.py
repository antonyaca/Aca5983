"""Amélioration du setup Fibo M15 (demande d'Anto 22/10/2026 : « trouve des solutions »). Protocole fixé AVANT calcul.

Base = variante A de run.py (référence M15 09:00 Paris / 09:30 NY, cassure en clôture M15, Fibonacci 1 = extrémité opposée
de la référence (stop), 0 = extrême de la bougie de cassure).
Grille de gestion : entrée ∈ {0,5 ; 0,618 ; 0,705 ; 0,786} × objectif ∈ {0 ; −0,272 ; −0,618} (extensions).
Ordre annulé si l'objectif est touché avant le remplissage, ou à l'échéance (14:00 / 21:00 Paris). Sortie forcée 22:00.
Filtres (calculés AVANT l'entrée, aucune info future) :
  tendJ   : cassure dans le sens de la tendance journalière (clôture de la veille vs SMA 20 jours)
  mom24   : cassure dans le sens du mouvement des 24 h précédentes
  pre     : cassure dans le sens du mouvement avant la session (00:00→09:00 Paris pour Londres, 09:00 Paris→09:30 NY pour NY)
  immed   : la cassure est la 1re bougie après la référence
  corps   : corps de la bougie de cassure ≥ 60 % de son range
  compr   : range de référence < médiane (ATR 14 j normalisé, médiane calculée sur 2011-2018)
  large   : range de référence ≥ cette médiane
  + paires (tendJ|mom24|pre) × (immed|corps|compr|large).
Sessions : Londres, New York, les deux. Marchés : XAUUSD, NASDAQ100, SP500, EURUSD.
SÉLECTION sur 2011-2018 uniquement (n ≥ 80, classement par t net), VALIDATION sur 2019-2026 jamais regardé avant.
Un résultat n'est retenu que s'il passe lib.evaluate sur toute la période ET reste positif en validation.
"""
import itertools, os, sys
import numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import lib  # noqa
MARKETS = ["XAUUSD", "NASDAQ100", "SP500", "EURUSD"]
ENTRIES, TPS = (0.5, 0.618, 0.705, 0.786), (0.0, -0.272, -0.618)
SPLIT = np.datetime64("2019-01-01")


def utc_min(d, tz, h, m):
    return int((pd.Timestamp(d.date()).tz_localize(tz) + pd.Timedelta(hours=h, minutes=m)).tz_convert("UTC").value // 60_000_000_000)


@njit(cache=True)
def sim(O, H, L, C, ke, idl, iend, dd, sl, x0, f, t):
    n = len(ke); fill = np.zeros(n, np.bool_); gross = np.zeros(n); risk = np.zeros(n)
    for s in range(n):
        d = dd[s]; F = x0[s] - sl[s]
        en = x0[s] - f * F; tp = x0[s] - t * F
        j = -1
        for k in range(ke[s], idl[s]):
            if (d == 1 and L[k] <= en) or (d == -1 and H[k] >= en):
                j = k; break
            if (d == 1 and H[k] >= tp) or (d == -1 and L[k] <= tp):
                break
        if j < 0:
            continue
        e = min(O[j], en) if d == 1 else max(O[j], en)
        r = (e - sl[s]) * d
        if r <= 0:
            continue
        px = C[iend[s] - 1]
        for i in range(j, iend[s]):
            if (d == 1 and L[i] <= sl[s]) or (d == -1 and H[i] >= sl[s]):
                px = sl[s]
                if i > j and ((d == 1 and O[i] < sl[s]) or (d == -1 and O[i] > sl[s])):
                    px = O[i]
                break
            if i > j and ((d == 1 and H[i] >= tp) or (d == -1 and L[i] <= tp)):
                px = tp
                if (d == 1 and O[i] > tp) or (d == -1 and O[i] < tp):
                    px = O[i]
                break
        fill[s] = True; gross[s] = (px - e) * d / r; risk[s] = r
    return fill, gross, risk


def setups(inst):
    df = lib.load(inst)
    T = df["time"].values.astype("datetime64[m]").astype(np.int64)
    O, H, L, C = (df[c].values for c in ("open", "high", "low", "close"))
    # journalier (jour de Paris) pour SMA20 / ATR14, décalés d'un jour
    dp = df.assign(dp=df.time.dt.tz_convert("Europe/Paris").dt.tz_localize(None).dt.normalize()).groupby("dp").agg(
        h=("high", "max"), l=("low", "min"), c=("close", "last"))
    pc = dp.c.shift()
    atr = pd.concat([dp.h - dp.l, (dp.h - pc).abs(), (dp.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift()
    trend = np.sign(dp.c - dp.c.rolling(20).mean()).shift()
    rows = []
    for d in pd.bdate_range("2011-01-01", lib.DATA_END):
        if d not in atr.index or np.isnan(atr[d]) or np.isnan(trend[d]):
            continue
        end = utc_min(d, "Europe/Paris", 22, 0)
        for sname, t0, dl, pre0 in (("Londres", utc_min(d, "Europe/Paris", 9, 0), utc_min(d, "Europe/Paris", 14, 0), utc_min(d, "Europe/Paris", 0, 0)),
                                    ("New York", utc_min(d, "America/New_York", 9, 30), utc_min(d, "Europe/Paris", 21, 0), utc_min(d, "Europe/Paris", 9, 0))):
            a, z = np.searchsorted(T, t0), np.searchsorted(T, t0 + 15)
            if z - a < 12:
                continue
            rh, rl = H[a:z].max(), L[a:z].min()
            if rh <= rl:
                continue
            brk, k, nb = None, z, 0
            while k < len(T) and T[k] < dl:
                bstart = t0 + ((T[k] - t0) // 15) * 15
                kz = np.searchsorted(T, bstart + 15)
                if kz - k < 5:
                    k = max(kz, k + 1); nb += 1; continue
                if C[kz - 1] > rh: brk = (1, k, kz); break
                if C[kz - 1] < rl: brk = (-1, k, kz); break
                k = kz; nb += 1
            if brk is None:
                continue
            dd, kb, kz = brk
            bh, bl, bo, bc = H[kb:kz].max(), L[kb:kz].min(), O[kb], C[kz - 1]
            i24, ip = np.searchsorted(T, t0 - 1440) - 1, np.searchsorted(T, pre0)
            if i24 < 0:
                continue
            rows.append(dict(instrument=inst, session=sname, day=d, d=dd, ke=kz, idl=np.searchsorted(T, dl), iend=np.searchsorted(T, end),
                             sl=rl if dd == 1 else rh, x0=bh if dd == 1 else bl,
                             tendJ=trend[d] == dd, mom24=np.sign(C[a - 1] - C[i24]) == dd, pre=np.sign(C[a - 1] - O[ip]) == dd,
                             immed=nb == 0, corps=abs(bc - bo) >= 0.6 * (bh - bl), refn=(rh - rl) / atr[d]))
    s = pd.DataFrame(rows)
    med = s[s.day < SPLIT].refn.median()
    s["compr"], s["large"] = s.refn < med, s.refn >= med
    return s, (O, H, L, C)


def tstat(x):
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


FILTERS = ["tout", "tendJ", "mom24", "pre", "immed", "corps", "compr", "large"] + \
          [f"{a}+{b}" for a, b in itertools.product(["tendJ", "mom24", "pre"], ["immed", "corps", "compr", "large"])]
res, keep = [], {}
for inst in MARKETS:
    s, (O, H, L, C) = setups(inst)
    arr = {c: s[c].values for c in ("ke", "idl", "iend", "d", "sl", "x0")}
    for f, tp in itertools.product(ENTRIES, TPS):
        fill, g, r = sim(O, H, L, C, arr["ke"].astype(np.int64), arr["idl"].astype(np.int64), arr["iend"].astype(np.int64),
                         arr["d"].astype(np.int64), arr["sl"].astype(float), arr["x0"].astype(float), f, tp)
        t = s[fill].copy(); t["gross_r"] = g[fill]; t["cost_r"] = lib.COST[inst] / r[fill]; t["net"] = t.gross_r - t.cost_r
        for sess in ("Londres", "New York", "les deux"):
            ts = t if sess == "les deux" else t[t.session == sess]
            for flt in FILTERS:
                m = np.ones(len(ts), bool)
                for p in flt.split("+"):
                    if p != "tout":
                        m &= ts[p].values
                k = ts[m]; dsc, val = k[k.day < SPLIT], k[k.day >= SPLIT]
                key = (inst, f, tp, sess, flt)
                res.append(dict(marché=inst, entrée=f, objectif=tp, session=sess, filtre=flt, n=len(k), n_dsc=len(dsc),
                                brut=k.gross_r.mean(), net_dsc=dsc.net.mean(), t_dsc=tstat(dsc.net), net_val=val.net.mean(), t_val=tstat(val.net)))
                keep[key] = k
    print(inst, len(s), "setups", flush=True)

R = pd.DataFrame(res)
R.to_csv(os.path.join(HERE, "ameliorer_grille.csv.gz"), index=False, float_format="%.4f")
print(f"\n{len(R)} variantes testées. Positives en découverte : {(R.net_dsc > 0).sum()} ; positives en découverte ET validation : {((R.net_dsc > 0) & (R.net_val > 0)).sum()}")
top = R[R.n_dsc >= 80].sort_values("t_dsc", ascending=False).head(15)
print("\nTop 15 choisis sur 2011-2018, puis jugés sur 2019-2026 :")
print(top.round(3).to_string(index=False))
print("\nCritère complet (lib.evaluate) sur le top 15 :")
for r in top.itertuples():
    k = keep[(r.marché, r.entrée, r.objectif, r.session, r.filtre)]
    print(lib.line(lib.evaluate(k, f"{r.marché} {r.session} e{r.entrée} tp{r.objectif} {r.filtre}")))
