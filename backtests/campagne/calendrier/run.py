"""Famille EFFETS DE CALENDRIER / SAISONNALITÉ / HORAIRES DE SÉANCE — règles fixées le 17/10/2026 AVANT tout calcul.

Cadre : PROTOCOLE.md (1 R = 100 €, coûts lib.COST, swap lib.SWAP par nuit calendaire, base 360, découverte 2011-2018 /
validation 2019-2026, critère lib.evaluate). Budget : 21 variantes (sur 25 autorisées), toutes enregistrées.

Séances : SP500/NASDAQ100 09:30-16:00 New York ; FTSE100 08:00-16:30 Londres ; NIKKEI225 09:00-15:00 Tokyo.
Ouverture = open de la 1re minute de séance (obligatoire) ; clôture = close de la dernière minute avant la fin de séance
(jours de séance réduite conservés, la clôture est alors le dernier prix CFD avant l'heure de fin).
Calendriers de bourse PRÉVISIBLES (exchange_calendars : XNYS, XLON, XTKS) : « dernière séance du mois », « veille de
férié », « 3e vendredi » sont déterminés par le calendrier officiel, jamais par les données futures. Fermetures non
prévisibles exclues des signaux : XNYS 2012-10-29/30 (ouragan Sandy), XTKS 2020-10-01 (panne). Un trade dont une barre
d'entrée ou de sortie manque dans les données est ignoré (compté dans les anomalies).
Sans stop : 1 R = ATR14 des séances (indices) ou des journées 17:00-17:00 NY (or) TERMINÉES AVANT le jour d'entrée.
cost_r = COST/R + swap (prix d'entrée × taux × nuits calendaires / 360 / R) ; FOMC : COST ×2 (jour d'annonce).

Variantes (toutes à l'achat sauf mention) :
 V1-V4  Turn of the month (Lakonishok-Smidt 1988, Ariel 1987, McConnell-Xu 2008) — SP500, NASDAQ100, FTSE100, NIKKEI225 :
        achat clôture de l'avant-dernière séance du mois, vente clôture de la 3e séance du mois suivant.
 V5     TOM portefeuille : chaque mois, moyenne des gross_r / cost_r des 4 indices de V1-V4 (0,25 R chacun ; ≥ 3 indices).
 V6-V9  Veille de jour férié (Ariel 1990, Kim-Park 1994) — SP500, NASDAQ100 (XNYS), FTSE100 (XLON), NIKKEI225 (XTKS) :
        P = dernière séance avant un jour de semaine férié ; achat clôture de la séance précédant P, vente clôture de P.
 V10-V11 Pre-FOMC drift (Lucca-Moench 2015) — SP500, NASDAQ100 : réunions PROGRAMMÉES (federalreserve.gov,
        pages fomchistorical 2011-2019 ; 2020-2026 reprises de events/backtest.py), jour = dernier jour de réunion ;
        achat clôture 16:00 de la séance précédente, vente à l'open de la barre de 12:00 NY le jour J (avant toute
        annonce : 12:30/14:15 en 2011-2012, 14:00 ensuite).
 V12-V13 Semaine d'expiration des options mensuelles — SP500, NASDAQ100 : X = dernière séance ≤ 3e vendredi ;
        achat clôture de la dernière séance ≤ (3e vendredi − 7 jours), vente clôture de X.
 V14    Halloween / Sell in May (Bouman-Jacobsen 2002) — portefeuille 4 indices, mois de novembre à avril : achat
        clôture dernière séance du mois précédent, vente clôture dernière séance du mois ; moyenne des 4 indices.
 V15    Nuit FTSE100 : achat clôture 16:30 → vente ouverture 08:00 de la séance suivante (séances consécutives au calendrier).
 V16    Nuit NIKKEI225 : achat clôture 15:00 → vente ouverture 09:00 suivante (idem).
 V17    Or, session Asie : achat XAUUSD open 18:00 NY (dim-jeu) → vente open 03:00 NY le lendemain (pas de rollover 17:00).
 V18    Or, séance COMEX : VENTE XAUUSD open 08:20 NY → rachat open 13:30 NY (lun-ven).
 V19    Or, fix PM de Londres (Caminschi-Heaney 2014) : VENTE XAUUSD open 14:30 Londres → rachat open 15:30 Londres (lun-ven).
 V20    Dernière heure du vendredi SP500 : achat open 15:00 NY → vente clôture séance (dernière minute < 16:00),
        vendredis sans clôture anticipée au calendrier.
 V21    Effet week-end / lundi (French 1980) SP500 : VENTE clôture du vendredi → rachat clôture du lundi suivant
        (vendredi et lundi séances consécutives au calendrier), 3 nuits de swap vendeur.
Barres « open HH:MM » : open de la première minute dans [HH:MM, HH:MM + 5 min[ ; sinon trade ignoré.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.append("/tmp/claude-0/-home-claude/1a5d9817-381e-5156-b888-c64c4882cf71/scratchpad/pylib")
from lib import load, evaluate, line, COST, SWAP, START  # noqa: E402
import exchange_calendars as xc  # noqa: E402

IDX = {"SP500": ("America/New_York", 570, 960, "XNYS"), "NASDAQ100": ("America/New_York", 570, 960, "XNYS"),
       "FTSE100": ("Europe/London", 480, 990, "XLON"), "NIKKEI225": ("Asia/Tokyo", 540, 900, "XTKS")}
UNFORESEEN = {"XNYS": ["2012-10-29", "2012-10-30"], "XLON": [], "XTKS": ["2020-10-01"]}
FOMC = """2011-01-26 2011-03-15 2011-04-27 2011-06-22 2011-08-09 2011-09-21 2011-11-02 2011-12-13
2012-01-25 2012-03-13 2012-04-25 2012-06-20 2012-08-01 2012-09-13 2012-10-24 2012-12-12
2013-01-30 2013-03-20 2013-05-01 2013-06-19 2013-07-31 2013-09-18 2013-10-30 2013-12-18
2014-01-29 2014-03-19 2014-04-30 2014-06-18 2014-07-30 2014-09-17 2014-10-29 2014-12-17
2015-01-28 2015-03-18 2015-04-29 2015-06-17 2015-07-29 2015-09-17 2015-10-28 2015-12-16
2016-01-27 2016-03-16 2016-04-27 2016-06-15 2016-07-27 2016-09-21 2016-11-02 2016-12-14
2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10
2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29 2026-09-16""".split()
ANOM = []


def calendar(code):
    cal = xc.get_calendar(code, start="2010-06-01", end="2026-12-31")
    sess = pd.DatetimeIndex(cal.sessions).tz_localize(None) if cal.sessions.tz else pd.DatetimeIndex(cal.sessions)
    unf = pd.DatetimeIndex(UNFORESEEN[code])
    wd = pd.bdate_range("2010-06-01", "2026-12-31")
    hol = wd.difference(sess).difference(unf)
    early = pd.DatetimeIndex(cal.early_closes).tz_localize(None) if getattr(cal.early_closes, "tz", None) else pd.DatetimeIndex(cal.early_closes)
    return sess, hol, early


def at(g_hm, g_open, hm):
    """open de la première minute dans [hm, hm+5[ ; NaN sinon."""
    k = np.searchsorted(g_hm, hm)
    return g_open[k] if k < len(g_hm) and g_hm[k] < hm + 5 else np.nan


def index_bars(inst):
    tz, s0, s1, _ = IDX[inst]
    df = load(inst, tz)
    s = df[(df["hm"] >= s0) & (df["hm"] < s1)]
    rows = {}
    for d, g in s.groupby("day"):
        hm, o, h, l, c = (g[k].values for k in ("hm", "open", "high", "low", "close"))
        if d.dayofweek >= 5 or hm[0] != s0 or len(hm) < 0.4 * (s1 - s0):
            continue
        rows[d] = {"open": o[0], "high": h.max(), "low": l.min(), "close": c[-1], "n": len(hm),
                   "p1200": at(hm, o, 720), "p1500": at(hm, o, 900), "last_hm": hm[-1]}
    del df, s
    b = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    pc = b["close"].shift(1)
    tr = pd.concat([b["high"] - b["low"], (b["high"] - pc).abs(), (b["low"] - pc).abs()], axis=1).max(axis=1)
    b["atr_prev"] = tr.rolling(14).mean().shift(1)    # ATR des 14 séances terminées AVANT ce jour
    return b


def mk(inst, d, t_in, t_out, p_in, p_out, risk, nights, cmult=1.0):
    if not (risk > 0) or np.isnan(p_in) or np.isnan(p_out):
        return None
    lo, sh = SWAP[inst]
    swap = p_in * (lo if d == 1 else sh) * nights / 360 / risk
    return {"instrument": inst, "d": d, "day": t_in, "exit_day": t_out, "entry": p_in, "exit": p_out, "risque": risk,
            "nuits": nights, "gross_r": (p_out - p_in) * d / risk, "cost_r": cmult * COST[inst] / risk + swap}


def close_to_close(inst, b, pairs, d=1, cmult=1.0, label=""):
    out, miss = [], 0
    for a, z in pairs:
        if a not in b.index or z not in b.index:
            miss += 1
            continue
        t = mk(inst, d, a, z, b.at[a, "close"], b.at[z, "close"], b.at[a, "atr_prev"], (z - a).days, cmult)
        if t:
            out.append(t)
    if miss:
        ANOM.append(f"{label} {inst}: {miss} trades ignorés (séance absente des données)")
    return out


def months(sess):
    s = pd.Series(sess, index=sess)
    return [list(v) for _, v in s.groupby([sess.year, sess.month])]


def index_variants(inst):
    tz, s0, s1, code = IDX[inst]
    b = index_bars(inst)
    sess, hol, early = calendar(code)
    sess = sess[(sess >= b.index[0]) & (sess <= b.index[-1])]
    missing = sess.difference(b.index)
    ANOM.append(f"{inst}: {len(missing)} séances du calendrier {code} absentes/incomplètes dans les données "
                f"(par an : {dict(pd.Series(missing.year).value_counts().sort_index())})")
    extra = b.index.difference(sess)
    if len(extra):
        ANOM.append(f"{inst}: {len(extra)} jours de données hors calendrier {code} (ignorés) ex. {[str(x.date()) for x in extra[:5]]}")
    b = b[b.index.isin(sess)]
    res = {}
    ml = months(sess)
    res["TOM"] = close_to_close(inst, b, [(a[-2], z[2]) for a, z in zip(ml[:-1], ml[1:]) if len(a) >= 2 and len(z) >= 3], label="TOM")
    res["HALLO"] = close_to_close(inst, b, [(a[-1], z[-1]) for a, z in zip(ml[:-1], ml[1:]) if z[0].month in (11, 12, 1, 2, 3, 4)], label="Halloween")
    sl = list(sess)
    pre = sorted({sess[sess < h][-1] for h in hol if (sess < h).any() and h <= sess[-1]})
    pos = {d: i for i, d in enumerate(sl)}
    res["PREHOL"] = close_to_close(inst, b, [(sl[pos[p] - 1], p) for p in pre if pos[p] > 0], label="Pré-férié")
    if code == "XNYS":
        f = pd.DatetimeIndex(FOMC)
        tr, miss = [], 0
        for x in f:
            if x not in pos:
                ANOM.append(f"FOMC {x.date()} n'est pas une séance XNYS"); continue
            a = sl[pos[x] - 1]
            if a not in b.index or x not in b.index:
                miss += 1; continue
            t = mk(inst, 1, a, x, b.at[a, "close"], b.at[x, "p1200"], b.at[a, "atr_prev"], (x - a).days, 2.0)
            if t: tr.append(t)
            else: miss += 1
        if miss: ANOM.append(f"Pré-FOMC {inst}: {miss} trades ignorés")
        res["FOMC"] = tr
        pairs = []
        for y in range(2010, 2027):
            for m in range(1, 13):
                fr = pd.date_range(f"{y}-{m:02d}-01", periods=21, freq="D")
                f3 = fr[fr.dayofweek == 4][2]
                xs, es = sess[sess <= f3], sess[sess <= f3 - pd.Timedelta(days=7)]
                if len(es) and len(xs) and xs[-1].month == m and f3 <= sess[-1] and es[-1] >= sess[0]:
                    pairs.append((es[-1], xs[-1]))
        res["OPEX"] = close_to_close(inst, b, pairs, label="Expiration")
        if inst == "SP500":
            fr_ = [d for d in sess if d.dayofweek == 4 and d not in early]
            tr = []
            for d in fr_:
                if d in b.index and b.at[d, "last_hm"] == 959:
                    t = mk(inst, 1, d, d, b.at[d, "p1500"], b.at[d, "close"], b.at[d, "atr_prev"], 0)
                    if t: tr.append(t)
            res["FRI"] = tr
            res["MON"] = close_to_close(inst, b, [(a, z) for a, z in zip(sl[:-1], sl[1:]) if a.dayofweek == 4 and z.dayofweek == 0
                                                  and (z - a).days == 3], d=-1, label="Week-end")
    if code in ("XLON", "XTKS"):
        tr, miss = [], 0
        for a, z in zip(sl[:-1], sl[1:]):
            if a in b.index and z in b.index:
                t = mk(inst, 1, a, z, b.at[a, "close"], b.at[z, "open"], b.at[a, "atr_prev"], (z - a).days)
                if t: tr.append(t)
            else:
                miss += 1
        res["NIGHT"] = tr
    return res


def gold_variants():
    inst = "XAUUSD"
    df = load(inst, "America/New_York")
    loc = df["time"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    df["gday"] = (loc + pd.Timedelta(hours=7)).dt.normalize()     # journée or 17:00 → 17:00 NY
    g = df.groupby("gday")
    dbar = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(), "n": g["open"].count()})
    dbar = dbar[(dbar.index.dayofweek < 5) & (dbar["n"] >= 600)]
    pc = dbar["close"].shift(1)
    trr = pd.concat([dbar["high"] - dbar["low"], (dbar["high"] - pc).abs(), (dbar["low"] - pc).abs()], axis=1).max(axis=1)
    atr = trr.rolling(14).mean()          # ATR incluant la journée-or indexée ; on lira la journée précédente

    def atr_before(t):                   # ATR des journées-or terminées avant l'instant t (heure NY naïve)
        k = atr.index.searchsorted((t + pd.Timedelta(hours=7)).normalize()) - 1
        return atr.iloc[k] if k >= 0 else np.nan

    lon = df["time"].dt.tz_convert("Europe/London")
    df["lday"] = lon.dt.tz_localize(None).dt.normalize()
    df["lhm"] = (lon.dt.hour * 60 + lon.dt.minute).astype(np.int16)
    out = {"ASIA": [], "COMEX": [], "FIX": []}
    byday = {d: (x["hm"].values, x["open"].values) for d, x in df.groupby("day")}
    days = sorted(byday)
    for d in days:
        hm, o = byday[d]
        if d.dayofweek in (6, 0, 1, 2, 3):
            nx = d + pd.Timedelta(days=1)
            if nx in byday:
                p0, p1 = at(hm, o, 1080), at(*byday[nx], 180)
                t = mk(inst, 1, d, nx, p0, p1, atr_before(d + pd.Timedelta(hours=18)), 0)
                if t: out["ASIA"].append(t)
        if d.dayofweek < 5:
            t = mk(inst, -1, d, d, at(hm, o, 500), at(hm, o, 810), atr_before(d + pd.Timedelta(hours=8, minutes=20)), 0)
            if t: out["COMEX"].append(t)
    for d, x in df.groupby("lday"):
        if d.dayofweek < 5:
            hm, o, tt = x["lhm"].values, x["open"].values, x["time"].values
            k = np.searchsorted(hm, 870)
            if k < len(hm) and hm[k] < 875:
                tny = pd.Timestamp(tt[k]).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
                t = mk(inst, -1, d, d, o[k], at(hm, o, 930), atr_before(tny), 0)
                if t: out["FIX"].append(t)
    del df
    return out


RULES = {
    "TOM": "Achat clôture avant-dernière séance du mois → vente clôture 3e séance du mois suivant (calendrier {cal}).",
    "PREHOL": "Achat clôture de la séance précédant la veille de férié → vente clôture de la veille de férié (calendrier {cal}).",
    "FOMC": "Achat clôture 16:00 veille de la décision FOMC programmée → vente open 12:00 NY le jour J (coûts ×2).",
    "OPEX": "Achat clôture dernière séance ≤ 3e vendredi − 7 j → vente clôture dernière séance ≤ 3e vendredi.",
    "NIGHT": "Achat clôture de séance → vente ouverture séance suivante (séances consécutives au calendrier {cal}).",
    "FRI": "Achat open 15:00 NY le vendredi → vente clôture séance (vendredis sans clôture anticipée).",
    "MON": "Vente clôture vendredi → rachat clôture lundi suivant.",
}


def main():
    res, alltr = [], []
    per = {}
    for inst in IDX:
        print("…", inst, flush=True)
        per[inst] = index_variants(inst)
    calname = {k: v[3] for k, v in IDX.items()}
    plan = [("V1", "SP500", "TOM"), ("V2", "NASDAQ100", "TOM"), ("V3", "FTSE100", "TOM"), ("V4", "NIKKEI225", "TOM")]
    plan += [("V6", "SP500", "PREHOL"), ("V7", "NASDAQ100", "PREHOL"), ("V8", "FTSE100", "PREHOL"), ("V9", "NIKKEI225", "PREHOL")]
    plan += [("V10", "SP500", "FOMC"), ("V11", "NASDAQ100", "FOMC"), ("V12", "SP500", "OPEX"), ("V13", "NASDAQ100", "OPEX")]
    plan += [("V15", "FTSE100", "NIGHT"), ("V16", "NIKKEI225", "NIGHT"), ("V20", "SP500", "FRI"), ("V21", "SP500", "MON")]
    variants = []
    for v, inst, k in plan:
        variants.append((v, f"{v} {k} {inst}", RULES[k].format(cal=calname[inst]), pd.DataFrame(per[inst][k])))
    for v, k, txt in (("V5", "TOM", "TOM portefeuille 4 indices : moyenne mensuelle des trades V1-V4 (≥ 3 indices)."),
                      ("V14", "HALLO", "Halloween : mois nov.-avril, achat clôture dernière séance du mois précédent → "
                                       "clôture dernière séance du mois, moyenne des 4 indices (≥ 3).")):
        t = pd.concat([pd.DataFrame(per[i][k]) for i in IDX])
        t["ym"] = t["exit_day"].dt.to_period("M")
        a = t.groupby("ym").agg(day=("day", "min"), exit_day=("exit_day", "max"), gross_r=("gross_r", "mean"),
                                cost_r=("cost_r", "mean"), n=("gross_r", "size")).reset_index(drop=True)
        a = a[a["n"] >= 3].assign(instrument="PORTEFEUILLE4", d=1, entry=np.nan, exit=np.nan)
        variants.append((v, f"{v} {k} portefeuille 4 indices", txt, a))
    print("… XAUUSD", flush=True)
    gv = gold_variants()
    variants += [("V17", "V17 Or Asie 18:00→03:00 NY", "Achat XAUUSD open 18:00 NY (dim-jeu) → vente open 03:00 NY.", pd.DataFrame(gv["ASIA"])),
                 ("V18", "V18 Or COMEX vente 08:20→13:30", "Vente XAUUSD open 08:20 NY → rachat open 13:30 NY.", pd.DataFrame(gv["COMEX"])),
                 ("V19", "V19 Or fix PM vente 14:30→15:30 Ldn", "Vente XAUUSD open 14:30 Londres → rachat open 15:30 Londres.", pd.DataFrame(gv["FIX"]))]
    variants.sort(key=lambda x: int(x[0][1:]))
    for v, lab, txt, t in variants:
        t = t.copy(); t["day"] = pd.to_datetime(t["day"])
        r = evaluate(t, lab)
        tt = t[t["day"] >= START]
        r["regles"] = txt
        r["trades_par_an"] = round(len(tt) / tt["day"].dt.year.nunique(), 1)
        res.append(r)
        print(line(r), f"| {r['trades_par_an']}/an")
        alltr.append(tt.assign(variante=v))
    print("\nANOMALIES :"); [print(" -", a) for a in ANOM]
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    pd.concat(alltr).to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6f")
    with open(os.path.join(HERE, "anomalies.txt"), "w") as f:
        f.write("\n".join(ANOM))


if __name__ == "__main__":
    main()
