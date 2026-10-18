"""Socle commun de la campagne de recherche (oct. 2026). Chargement rapide, coûts, statistiques, critère.

Usage :
    import sys, os; sys.path.insert(0, "/home/claude/aca5983/backtests/campagne")
    from lib import load, sessions_ny, evaluate, COST, SWAP, MARKETS

load(inst, tz) -> DataFrame M1 (time UTC, open, high, low, close, local, day, hm) depuis 2010 (cache npz, rapide).
evaluate(trades, label) -> dict standardisé + verdict (voir PROTOCOLE.md).
`trades` = DataFrame avec au moins : day (Timestamp), gross_r, cost_r (coûts aller-retour + swap, en R).
"""
import glob
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data_cache")
# Marchés utilisables (DAX, WTI, CAC40 exclus : données corrompues ou incomplètes)
MARKETS = ["NASDAQ100", "SP500", "FTSE100", "NIKKEI225", "XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
# coût aller-retour (spread + slippage) en unités de prix — mêmes valeurs que les lots précédents
COST = {"NASDAQ100": 1.5, "SP500": 0.75, "FTSE100": 1.5, "NIKKEI225": 12.0, "XAUUSD": 0.47, "XAGUSD": 0.04,
        "EURUSD": 0.00015, "GBPUSD": 0.0002, "USDJPY": 0.02, "AUDUSD": 0.00015}
# swap par nuit calendaire (base 360), fraction du nominal par an : (achat, vente)
SWAP = {"NASDAQ100": (0.06, 0.01), "SP500": (0.06, 0.01), "FTSE100": (0.06, 0.01), "NIKKEI225": (0.06, 0.01),
        "XAUUSD": (0.06, 0.01), "XAGUSD": (0.06, 0.01),
        "EURUSD": (0.025, 0.025), "GBPUSD": (0.025, 0.025), "USDJPY": (0.025, 0.025), "AUDUSD": (0.025, 0.025)}
START = pd.Timestamp("2011-01-01")          # 2010 sert seulement de préchauffage des indicateurs
SPLIT = pd.Timestamp("2019-01-01")          # découverte 2011-2018 / validation 2019-2026


def _build(inst):
    files = sorted(glob.glob(os.path.join(ROOT, "data", inst, f"{inst}_M1_*.csv.gz")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    t = pd.to_datetime(df["time"], utc=True)
    df = df.assign(time=t).drop_duplicates("time").sort_values("time")
    os.makedirs(CACHE, exist_ok=True)
    np.savez(os.path.join(CACHE, f"{inst}.npz"), t=df["time"].values.astype("datetime64[m]").astype(np.int64),
             o=df["open"].values, h=df["high"].values, l=df["low"].values, c=df["close"].values)


def load(inst, tz="America/New_York"):
    p = os.path.join(CACHE, f"{inst}.npz")
    if not os.path.exists(p):
        _build(inst)
    z = np.load(p)
    time = pd.to_datetime(z["t"], unit="m", utc=True)
    df = pd.DataFrame({"time": time, "open": z["o"], "high": z["h"], "low": z["l"], "close": z["c"]})
    loc = df["time"].dt.tz_convert(tz)
    df["day"] = loc.dt.tz_localize(None).dt.normalize()
    df["hm"] = (loc.dt.hour * 60 + loc.dt.minute).astype(np.int16)
    return df


def sessions_ny(df, start_hm=570, end_hm=960, min_frac=0.9):
    """Dict jour -> (hm, O, H, L, C) pour la fenêtre [start_hm, end_hm) ; jours incomplets écartés."""
    s = df[(df["hm"] >= start_hm) & (df["hm"] < end_hm)]
    out = {}
    need = min_frac * (end_hm - start_hm)
    for d, g in s.groupby("day"):
        if d.dayofweek < 5 and len(g) >= need and g["hm"].iloc[0] == start_hm:
            out[d] = tuple(g[c].values for c in ("hm", "open", "high", "low", "close"))
    return out


def _st(r):
    r = np.asarray(r, float)
    if len(r) == 0:
        return {"trades": 0, "e_r": float("nan"), "pf": None, "win_rate": float("nan"), "resultat_eur": 0.0, "max_dd_eur": 0.0}
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    cum = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max())
    return {"trades": int(len(r)), "e_r": float(r.mean()), "pf": float(pos / neg) if neg else None,
            "win_rate": float((r > 0).mean() * 100), "resultat_eur": float(r.sum() * 100), "max_dd_eur": dd * 100}


def evaluate(t, label):
    """Critère de la campagne (fixé avant les tests, voir PROTOCOLE.md)."""
    t = t[t["day"] >= START].sort_values("day")
    x = (t["gross_r"] - t["cost_r"]).values
    x2 = (t["gross_r"] - 2 * t["cost_r"]).values
    d = t["day"]
    disc, val = x[(d < SPLIT).values], x[(d >= SPLIT).values]
    years = pd.Series(x, index=d.dt.year.values).groupby(level=0).sum()
    n = len(x)
    tstat = float(x.mean() / x.std(ddof=1) * np.sqrt(n)) if n > 2 and x.std() > 0 else 0.0
    top10 = float(np.sort(x)[:-10].mean()) if n > 30 else float("nan")
    r = {"label": label, "net": _st(x), "brut": _st(t["gross_r"].values), "decouverte_2011_2018": _st(disc),
         "validation_2019_2026": _st(val), "e_frais_x2": float(x2.mean()) if n else float("nan"), "t_stat": tstat,
         "sans_top10": top10, "annees_positives": f"{int((years > 0).sum())}/{len(years)}",
         "par_annee_eur": {str(k): round(float(v) * 100) for k, v in years.items()}}
    ok = (n >= 100 and _st(disc)["e_r"] > 0 and _st(val)["e_r"] > 0 and (r["net"]["pf"] or 0) >= 1.10
          and r["e_frais_x2"] > 0 and tstat >= 3.0 and top10 > 0 and (years > 0).mean() >= 0.6)
    r["valide"] = bool(ok)
    return r


def line(r):
    n = r["net"]
    return (f"{'✔' if r['valide'] else '✘'} {r['label']:45} n{n['trades']:>5} En{n['e_r']:+.3f} PF{(n['pf'] or 0):.2f} "
            f"D{r['decouverte_2011_2018']['e_r']:+.3f} V{r['validation_2019_2026']['e_r']:+.3f} x2{r['e_frais_x2']:+.3f} "
            f"t{r['t_stat']:+.2f} -top10{r['sans_top10']:+.3f} ans+{r['annees_positives']} {n['resultat_eur']:>8.0f}€ DD{n['max_dd_eur']:>6.0f}€")


# ---------------------------------------------------------------------------------------------------------------
# Campagne 2 « 1 trade par jour » (18/10/2026) — ajouts, n'altèrent rien de ce qui précède.
DATA_END = pd.Timestamp("2026-10-09")   # dernière séance des données

def regle_anto(t):
    """Règle d'Anto : chaque jour, 1er trade ; un 2e trade seulement si le 1er est perdant (net < 0) ; puis stop.
    `t` = TOUS les trades candidats, pris un à la fois (pas de chevauchement), colonnes : day, t_in, t_out, gross_r,
    cost_r (t_in/t_out triables : Timestamp ou minutes). Si la stratégie couvre plusieurs marchés, c'est le 1er signal
    de la journée, tous marchés confondus, puis le 1er signal entrant APRÈS la sortie du 1er trade.
    Retourne le sous-ensemble des trades réellement pris."""
    if not t.index.is_unique:                    # concat multi-marchés : index dupliqués → réindexation
        t = t.reset_index(drop=True)
    t = t.sort_values(["day", "t_in"])
    keep = []
    for _, g in t.groupby("day", sort=False):
        first = g.iloc[0]
        keep.append(first.name)
        if first["gross_r"] - first["cost_r"] < 0:
            nxt = g[g["t_in"] >= first["t_out"]]
            nxt = nxt[nxt.index != first.name]
            if len(nxt):
                keep.append(nxt.index[0])
    return t.loc[keep]


def stats_jour(t, end=None):
    """Statistiques journalières sur 2011 → fin des données (jours ouvrés sans trade = 0 €)."""
    t = t[t["day"] >= START]
    if len(t) == 0:
        return {}
    p = ((t["gross_r"] - t["cost_r"]) * 100).groupby(t["day"]).sum()
    days = pd.bdate_range(START, end or DATA_END)
    full = p.reindex(days, fill_value=0.0)
    neg = (p < 0).astype(int).values
    run = best = 0
    for v in neg:
        run = run + 1 if v else 0
        best = max(best, run)
    m = full.resample("ME").sum()
    yrs = len(days) / 261
    return {"jours_ouvres": int(len(days)), "jours_avec_trade_pct": round(len(p) / len(days) * 100, 1),
            "jours_positifs_pct_jours_trades": round(float((p > 0).mean() * 100), 1),
            "jours_50eur_ou_plus_pct": round(float((p >= 50).mean() * 100), 1),
            "eur_moyen_par_jour_ouvre": round(float(full.mean()), 2), "eur_par_an": round(float(p.sum() / yrs)),
            "pire_jour_eur": round(float(p.min())), "pire_serie_jours_perdants": int(best),
            "mois_positifs_pct": round(float((m > 0).mean() * 100), 1), "pire_mois_eur": round(float(m.min()))}


def line_jour(s):
    return (f"jours trade {s['jours_avec_trade_pct']:4.0f}% | positifs {s['jours_positifs_pct_jours_trades']:4.0f}% | ≥50€ "
            f"{s['jours_50eur_ou_plus_pct']:4.0f}% | {s['eur_moyen_par_jour_ouvre']:+6.2f} €/jour | {s['eur_par_an']:+6d} €/an | "
            f"pire série {s['pire_serie_jours_perdants']} j | mois+ {s['mois_positifs_pct']:.0f}% | pire mois {s['pire_mois_eur']} €")
