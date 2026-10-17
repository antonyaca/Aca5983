"""Campagne métaux + forex (XAUUSD, XAGUSD, EURUSD, GBPUSD, USDJPY, AUDUSD) — règles fixées AVANT tout calcul.

Données : lib.load(inst, "UTC") (cache corrigé en vrai UTC, fichier data_cache/FIXED), puis conversion vers le fuseau utile
(Asia/Tokyo, Europe/London, America/New_York, heures d'été comprises). Prix bid, coût aller-retour lib.COST (spread inclus).
« Prix à HH:MM » = ouverture de la 1re minute >= HH:MM (au plus 5 min de retard, sinon pas de trade).
Journée de trading = rollover 17:00 New York (date de NY+7 h). 1 R (sans stop) = ATR14 journalier des journées précédentes
(journées >= 600 minutes). Swap = nuits calendaires entre journées de trading d'entrée et de sortie × taux/360 × prix / R
(forex 2,5 %/an ; métaux 6 %/an achat, 1 %/an vente). Coûts ×2 les jours d'annonce US (date NY de l'entrée) :
NFP/CPI/FOMC officiels 2020+ ; avant 2020 seul le NFP est approximé par le 1er vendredi du mois (calendrier CPI/FOMC absent).
Stop prioritaire ; gap au-delà du stop -> sortie à l'ouverture ; deux niveaux franchis dans la même minute -> pas de trade.

VARIANTES (19 sur 25 autorisées) :
V01 Gotobi USDJPY achat : jours Gotobi (5, 10, 15, 20, 25 et dernier jour du mois ; si week-end -> jour ouvré précédent ;
    fériés japonais ignorés), achat à 08:00 Tokyo, sortie 09:55 Tokyo (fix de Tokyo).
V02 Gotobi USDJPY vente après le fix : jours Gotobi, vente 09:56 Tokyo, sortie 12:00 Tokyo.
V03 Témoin Tokyo : achat USDJPY 08:00 -> 09:55 Tokyo les jours ouvrés NON Gotobi.
V04 Fix WM fin de mois, retournement (4 paires poolées) : dernier jour ouvré du mois (Londres). m = prix 16:00 - prix 15:00
    Londres ; position opposée au signe de m, entrée 16:05, sortie 19:00 Londres.
V05 Même règle tous les autres jours ouvrés (fix quotidien), 4 paires poolées.
V06 Cassure du range asiatique, 4 paires poolées : range 00:00-07:00 Londres (>= 300 minutes) ; 1er franchissement du haut
    (achat) ou du bas (vente) entre 07:00 et 12:00 Londres ; entrée au niveau (ou ouverture si gap) ; stop = bord opposé ;
    sortie 16:00 Londres. R = distance au stop.
V07 Même règle sur XAUUSD.
V08 Or, retournement autour du fix PM (15:00 Londres) : m = prix 15:00 - prix 14:00 ; position opposée, 15:05 -> 17:00 Londres.
V09 Or, retournement autour du fix AM (10:30 Londres) : m = prix 10:30 - prix 09:30 ; position opposée, 10:35 -> 12:30.
V10 Or, achat de la séance asiatique : achat 19:00 New York (dim.-jeu.), sortie 03:00 New York le lendemain (pas de rollover).
V11 Même règle sur XAGUSD.
V12 Or, vente de la séance COMEX : vente 08:20 New York, sortie 13:30 New York, tous les jours ouvrés.
V13 Or, momentum d'ouverture COMEX : sens = signe(prix 08:50 - prix 08:20) ; entrée 08:51, sortie 13:30 New York.
V14 Ratio or/argent, retour à la moyenne : photo quotidienne à 16:00 NY ; s = ln(XAG) - ln(XAU) ; z = (s - moyenne 20 j) /
    écart-type 20 j (photos <= jour t). z < -2 : achat argent / vente or (nominaux égaux) ; z > +2 : l'inverse. Entrée au
    prix de 16:01 NY du jour t ; sortie au prix 16:01 du 1er jour où z repasse 0, ou après 20 jours de bourse. Une position
    à la fois. 1 R = moyenne des ATR14 en % des deux jambes ; coûts = coûts des deux jambes ; swap 6 % (jambe achetée)
    + 1 % (jambe vendue) par nuit calendaire.
V15 Grosse bougie H1, momentum (6 instruments poolés) : H1 en heures UTC (>= 30 minutes). Signal si amplitude >= 2 ×
    moyenne des amplitudes des 24 H1 précédentes ET corps >= 50 % de l'amplitude ; entrée à l'ouverture de la H1 suivante
    dans le sens du corps, sortie à la clôture de la 4e H1 (4 H1 consécutives exigées) ; pas de chevauchement.
V16 Même signal, retournement (sens opposé).
V17 Inside day XAUUSD sur 16 ans (règle du lot 3 inchangée) : journée 00:00-17:00 NY (>= 600 minutes) ; si J strictement
    contenu dans J-1, en J+1 1er franchissement du haut/bas de J, stop bord opposé, sortie dernière minute avant 17:00 NY.
V18 Même règle, 4 paires forex poolées.
V19 Même règle, XAGUSD.
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib import load, evaluate, line, COST, SWAP  # noqa: E402

FX = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
INSTS = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD", "XAUUSD", "XAGUSD"]
MAXLAG = 5

# ---------- calendrier macro
_spec = importlib.util.spec_from_file_location(
    "ev", os.path.join(os.path.dirname(os.path.dirname(HERE)), "events", "backtest.py"))
_ev = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_ev)
MACRO = set(pd.to_datetime(list(_ev.NFP) + list(_ev.CPI) + list(_ev.FOMC)))
for y in range(2010, 2020):
    for m in range(1, 13):
        d = pd.Timestamp(y, m, 1)
        MACRO.add(d + pd.Timedelta(days=(4 - d.dayofweek) % 7))


def gotobi_days(y0=2010, y1=2026):
    out = set()
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            last = (pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)).day
            for n in (5, 10, 15, 20, 25, last):
                d = pd.Timestamp(y, m, n)
                while d.dayofweek >= 5:
                    d -= pd.Timedelta(days=1)
                out.add(d)
    return out


class Mkt:
    """Tableaux M1 d'un instrument + clés de minutes locales par fuseau + ATR par journée de trading."""

    def __init__(self, inst):
        df = load(inst, "UTC")
        self.inst = inst
        self.t = df["time"]
        self.O, self.H, self.L, self.C = (df[c].values for c in ("open", "high", "low", "close"))
        self.utcmin = (df["time"].values.astype("datetime64[m]").astype(np.int64))
        self.keys = {}
        ny = self.key("America/New_York")
        td = ((ny + 7 * 60) // 1440)                      # journée de trading (jours depuis epoch, date NY+7h)
        self.td = td
        g = pd.DataFrame({"td": td, "h": self.H, "l": self.L, "c": self.C}).groupby("td")
        d = pd.DataFrame({"h": g["h"].max(), "l": g["l"].min(), "c": g["c"].last(), "n": g.size()})
        d = d[d["n"] >= 600]
        pc = d["c"].shift(1)
        tr = np.maximum(d["h"] - d["l"], np.maximum((d["h"] - pc).abs(), (d["l"] - pc).abs()))
        atr = tr.rolling(14).mean().shift(1)            # connu avant la journée
        self.atr = atr.reindex(range(int(td.min()), int(td.max()) + 2)).ffill()  # journées courtes : dernier ATR connu
        self.daily = d
        del df

    def key(self, tz):
        if tz not in self.keys:
            loc = self.t.dt.tz_convert(tz).dt.tz_localize(None)
            self.keys[tz] = loc.values.astype("datetime64[m]").astype(np.int64)
        return self.keys[tz]

    def at(self, tz, targets):
        """indices de la 1re minute >= cible (minutes locales) ; -1 si absente ou > MAXLAG min de retard."""
        k = self.key(tz)
        targets = np.asarray(targets, np.int64)
        i = np.searchsorted(k, targets, "left")
        ok = i < len(k)
        i2 = np.where(ok, i, 0)
        ok &= (k[i2] - targets) <= MAXLAG
        return np.where(ok, i2, -1)

    def local_days(self, tz):
        k = self.key(tz)
        days = np.unique(k // 1440)
        wd = (days + 3) % 7                               # 1970-01-01 = jeudi -> lundi = 0
        return days[wd < 5]


def daynum(ts):
    return int((pd.Timestamp(ts) - pd.Timestamp("1970-01-01")).days)


def finish(m, rows, side_swap=True):
    """rows : liste de dict(day_td, d, ie, ix, entry, exit, risk|None). Retourne DataFrame avec gross_r/cost_r."""
    if not rows:
        return pd.DataFrame(columns=["instrument", "day", "d", "entry", "exit", "gross_r", "cost_r"])
    t = pd.DataFrame(rows)
    ny = m.key("America/New_York")
    td_e, td_x = m.td[t["ie"].values], m.td[t["ix"].values]
    atr = m.atr.reindex(td_e).values
    risk = np.where(t["risk"].isna(), atr, t["risk"].astype(float))
    t["R"] = risk
    t = t[np.isfinite(t["R"]) & (t["R"] > 0)].copy()
    td_e, td_x = m.td[t["ie"].values], m.td[t["ix"].values]
    nights = (td_x - td_e).astype(float)
    lo, sh = SWAP[m.inst]
    rate = np.where(t["d"].values == 1, lo, sh)
    ny_date = pd.to_datetime(ny[t["ie"].values] // 1440, unit="D")
    mult = np.where(pd.Index(ny_date).isin(list(MACRO)), 2.0, 1.0)
    t["gross_r"] = (t["exit"] - t["entry"]) * t["d"] / t["R"]
    t["cost_r"] = (COST[m.inst] * mult + nights * rate / 360 * t["entry"]) / t["R"]
    t["day"] = pd.to_datetime(td_e, unit="D")
    t["instrument"] = m.inst
    return t[["instrument", "day", "d", "entry", "exit", "R", "gross_r", "cost_r"]]


# ---------- briques
def timed(m, tz, days, t_sig0, t_sig1, t_in, t_out, mode, day_offset_out=0):
    """Trade à heures fixes. mode : +1/-1 (sens fixe), 'fade' / 'mom' (selon signe prix(t_sig1)-prix(t_sig0))."""
    base = np.asarray(days, np.int64) * 1440
    ie, ix = m.at(tz, base + t_in), m.at(tz, base + day_offset_out * 1440 + t_out)
    ok = (ie >= 0) & (ix >= 0)
    if mode in ("fade", "mom"):
        i0, i1 = m.at(tz, base + t_sig0), m.at(tz, base + t_sig1)
        ok &= (i0 >= 0) & (i1 >= 0)
        mv = np.sign(m.O[np.maximum(i1, 0)] - m.O[np.maximum(i0, 0)])
        dirs = (-mv if mode == "fade" else mv)
        ok &= dirs != 0
    else:
        dirs = np.full(len(base), mode)
    ok &= ix > ie
    rows = [dict(ie=int(a), ix=int(b), d=int(c), entry=m.O[a], exit=m.O[b], risk=np.nan)
            for a, b, c in zip(ie[ok], ix[ok], dirs[ok])]
    return finish(m, rows)


def walk_exit(m, k, d, stop, iend):
    """sortie : stop (prioritaire, gap -> ouverture) sinon clôture de la barre iend-1."""
    if (m.L[k] <= stop) if d == 1 else (m.H[k] >= stop):
        return stop, k
    seg = slice(k + 1, iend)
    hit = (m.L[seg] <= stop) if d == 1 else (m.H[seg] >= stop)
    if hit.any():
        j = k + 1 + int(hit.argmax())
        o = m.O[j]
        return (o if ((o < stop) if d == 1 else (o > stop)) else stop), j
    return m.C[iend - 1], iend - 1


def breakout(m, a, b, up, dn, iend):
    """1er franchissement de up/dn sur les barres [a, b) ; stop bord opposé ; sortie barre iend-1."""
    if b <= a:
        return None
    hu, hd = m.H[a:b] > up, m.L[a:b] < dn
    hit = hu | hd
    if not hit.any():
        return None
    j = int(hit.argmax())
    if hu[j] and hd[j]:
        return None
    k, d = a + j, (1 if hu[j] else -1)
    entry = max(m.O[k], up) if d == 1 else min(m.O[k], dn)
    stop = dn if d == 1 else up
    risk = (entry - stop) * d
    if risk <= 0:
        return None
    px, ix = walk_exit(m, k, d, stop, iend)
    return dict(ie=k, ix=ix, d=d, entry=entry, exit=px, risk=risk)


def asian_breakout(m):
    tz = "Europe/London"
    k = m.key(tz)
    rows = []
    for day in m.local_days(tz):
        b = day * 1440
        i0, i7, i12, i16 = np.searchsorted(k, [b, b + 420, b + 720, b + 960])
        if i7 - i0 < 300 or i16 <= i12:
            continue
        up, dn = m.H[i0:i7].max(), m.L[i0:i7].min()
        if up <= dn:
            continue
        r = breakout(m, i7, i12, up, dn, i16)
        if r:
            rows.append(r)
    return finish(m, rows)


def inside_day(m):
    tz = "America/New_York"
    k = m.key(tz)
    days = m.local_days(tz)
    info = []
    for day in days:
        i0, i1 = np.searchsorted(k, [day * 1440, day * 1440 + 1020])
        if i1 - i0 >= 600:
            info.append((day, i0, i1, m.H[i0:i1].max(), m.L[i0:i1].min()))
    rows = []
    for (_, _, _, ha, la), (_, _, _, hb, lb), (_, c0, c1, _, _) in zip(info[:-2], info[1:-1], info[2:]):
        if hb < ha and lb > la:
            r = breakout(m, c0, c1, hb, lb, c1)
            if r:
                rows.append(r)
    return finish(m, rows)


def h1_bigbar(m):
    hk = m.utcmin // 60
    starts = np.r_[0, np.flatnonzero(np.diff(hk)) + 1]
    n = np.diff(np.r_[starts, len(hk)])
    hour = hk[starts]
    O = m.O[starts]
    H = np.maximum.reduceat(m.H, starts)
    L = np.minimum.reduceat(m.L, starts)
    C = m.C[np.r_[starts[1:], len(hk)] - 1]
    keep = n >= 30
    hour, O, H, L, C = hour[keep], O[keep], H[keep], L[keep], C[keep]
    st_k = starts[keep]
    rng = H - L
    avg = pd.Series(rng).rolling(24).mean().shift(1).values
    body = C - O
    sig = (rng >= 2 * avg) & (np.abs(body) >= 0.5 * rng) & np.isfinite(avg)
    rows, nxt = [], 0
    N = len(hour)
    for i in np.flatnonzero(sig):
        if i < nxt or i + 4 >= N:
            continue
        if hour[i + 4] != hour[i] + 4:
            continue
        d = 1 if body[i] > 0 else -1
        ie = int(st_k[i + 1])
        # sortie = clôture de la 4e H1 : dernière minute de l'heure hour[i]+4
        ix = int(np.searchsorted(hk, hour[i] + 5) - 1)
        rows.append(dict(ie=ie, ix=ix, d=d, entry=m.O[ie], exit=m.C[ix], risk=np.nan))
        nxt = i + 5
    rev = [dict(r, d=-r["d"]) for r in rows]
    return finish(m, rows), finish(m, rev)


def main():
    res, store = [], {}
    gotobi = {daynum(d) for d in gotobi_days()}

    def add(key, t):
        store.setdefault(key, []).append(t)

    snaps = {}
    for inst in INSTS:
        print("chargement", inst, flush=True)
        m = Mkt(inst)
        if inst == "USDJPY":
            tdays = m.local_days("Asia/Tokyo")
            g = np.array([d for d in tdays if d in gotobi]); ng = np.array([d for d in tdays if d not in gotobi])
            add("V01", timed(m, "Asia/Tokyo", g, 0, 0, 480, 595, 1))
            add("V02", timed(m, "Asia/Tokyo", g, 0, 0, 596, 720, -1))
            add("V03", timed(m, "Asia/Tokyo", ng, 0, 0, 480, 595, 1))
        if inst in FX:
            ld = m.local_days("Europe/London")
            ser = pd.Series(ld, index=pd.to_datetime(ld, unit="D"))
            me = set(ser.groupby(ser.index.to_period("M")).max().values)
            add("V04", timed(m, "Europe/London", np.array([d for d in ld if d in me]), 900, 960, 965, 1140, "fade"))
            add("V05", timed(m, "Europe/London", np.array([d for d in ld if d not in me]), 900, 960, 965, 1140, "fade"))
            add("V06", asian_breakout(m))
            add("V18", inside_day(m))
        if inst == "XAUUSD":
            ld = m.local_days("Europe/London")
            nd = m.local_days("America/New_York")
            add("V07", asian_breakout(m))
            add("V08", timed(m, "Europe/London", ld, 840, 900, 905, 1020, "fade"))
            add("V09", timed(m, "Europe/London", ld, 570, 630, 635, 750, "fade"))
            ev = nd[((nd + 3) % 7) <= 3]                      # lundi-jeudi -> veille = dim.-mer.
            sun = nd[((nd + 3) % 7) == 0] - 1                 # dimanches (veille des lundis)
            ev_days = np.unique(np.r_[ev, sun])               # soirées dim.-jeu.
            ev_days = ev_days[((ev_days + 3) % 7) != 4]       # pas le vendredi soir
            add("V10", timed(m, "America/New_York", ev_days, 0, 0, 1140, 180, 1, day_offset_out=1))
            add("V12", timed(m, "America/New_York", nd, 0, 0, 500, 810, -1))
            add("V13", timed(m, "America/New_York", nd, 500, 530, 531, 810, "mom"))
            add("V17", inside_day(m))
        if inst == "XAGUSD":
            nd = m.local_days("America/New_York")
            ev = nd[((nd + 3) % 7) <= 3]
            sun = nd[((nd + 3) % 7) == 0] - 1
            ev_days = np.unique(np.r_[ev, sun]); ev_days = ev_days[((ev_days + 3) % 7) != 4]
            add("V11", timed(m, "America/New_York", ev_days, 0, 0, 1140, 180, 1, day_offset_out=1))
            add("V19", inside_day(m))
        # H1 grosse bougie (momentum + retournement)
        mo, rv = h1_bigbar(m)
        add("V15", mo)
        add("V16", rv)
        # photos 16:00 / 16:01 NY pour le ratio
        if inst in ("XAUUSD", "XAGUSD"):
            nd = m.local_days("America/New_York")
            i16, i161 = m.at("America/New_York", nd * 1440 + 960), m.at("America/New_York", nd * 1440 + 961)
            ok = (i16 >= 0) & (i161 >= 0)
            atrp = m.atr.reindex(m.td[i16[ok]]).values / m.O[i16[ok]]
            snaps[inst] = pd.DataFrame({"p16": m.O[i16[ok]], "pin": m.O[i161[ok]], "atrp": atrp,
                                        "td": m.td[i16[ok]]}, index=pd.to_datetime(nd[ok], unit="D"))
        del m
    add("V14", ratio_mr(snaps))
    return store


def ratio_mr(snaps):
    g, s = snaps["XAUUSD"], snaps["XAGUSD"]
    j = g.join(s, lsuffix="_g", rsuffix="_s", how="inner").dropna()
    sp = np.log(j["p16_s"]) - np.log(j["p16_g"])
    z = ((sp - sp.rolling(20).mean()) / sp.rolling(20).std()).values
    R = ((j["atrp_g"] + j["atrp_s"]) / 2).values
    rows, pos = [], None
    dates = j.index
    for i in range(len(j)):
        if pos is not None:
            e = pos
            held = i - e["i"]
            if (e["d"] == 1 and z[i] >= 0) or (e["d"] == -1 and z[i] <= 0) or held >= 20:
                rs = j["pin_s"].iloc[i] / e["ps"] - 1
                rg = j["pin_g"].iloc[i] / e["pg"] - 1
                pnl = e["d"] * (rs - rg)
                nights = (dates[i] - dates[e["i"]]).days
                cost = (COST["XAUUSD"] / e["pg"] + COST["XAGUSD"] / e["ps"]) * e["mult"] \
                    + nights * (0.06 + 0.01) / 360
                rows.append(dict(instrument="XAU/XAG", day=dates[e["i"]], d=e["d"], entry=e["ratio"],
                                 exit=j["pin_g"].iloc[i] / j["pin_s"].iloc[i], R=e["R"],
                                 gross_r=pnl / e["R"], cost_r=cost / e["R"]))
                pos = None
        if pos is None and np.isfinite(z[i]) and np.isfinite(R[i]) and abs(z[i]) > 2:
            mult = 2.0 if dates[i] in MACRO else 1.0
            pos = dict(i=i, d=1 if z[i] < -2 else -1, ps=j["pin_s"].iloc[i], pg=j["pin_g"].iloc[i], R=R[i],
                       ratio=j["pin_g"].iloc[i] / j["pin_s"].iloc[i], mult=mult)
    return pd.DataFrame(rows)


LABELS = {
    "V01": "Gotobi USDJPY achat 08:00-09:55 JST", "V02": "Gotobi USDJPY vente 09:56-12:00 JST",
    "V03": "Témoin USDJPY achat 08:00-09:55 non-Gotobi", "V04": "Fix WM fin de mois retournement 4 FX",
    "V05": "Fix WM 16h quotidien retournement 4 FX", "V06": "Cassure range asiatique 4 FX",
    "V07": "Cassure range asiatique XAU", "V08": "Or retournement fix PM 15:00",
    "V09": "Or retournement fix AM 10:30", "V10": "Or achat séance Asie 19h-03h NY",
    "V11": "Argent achat séance Asie 19h-03h NY", "V12": "Or vente séance COMEX 08:20-13:30",
    "V13": "Or momentum ouverture COMEX", "V14": "Ratio or/argent z20 ±2",
    "V15": "Grosse bougie H1 momentum 6 instr.", "V16": "Grosse bougie H1 retournement 6 instr.",
    "V17": "Inside day XAU 16 ans", "V18": "Inside day 4 FX", "V19": "Inside day XAG",
}


def regles(key):
    doc = __doc__.split("VARIANTES")[1]
    blk = doc.split(key + " ")[1]
    nxt = f"V{int(key[1:]) + 1:02d} "
    return (key + " " + blk.split(nxt)[0]).replace("\n    ", " ").strip()


if __name__ == "__main__":
    store = main()
    res = []
    os.makedirs(os.path.join(HERE, "trades"), exist_ok=True)
    for key in sorted(store):
        t = pd.concat([x for x in store[key] if len(x)], ignore_index=True)
        t.to_csv(os.path.join(HERE, "trades", f"{key}.csv.gz"), index=False, float_format="%.6f")
        r = evaluate(t, f"{key} {LABELS[key]}")
        r["regles"] = regles(key)
        tt = t[t["day"] >= "2011-01-01"]
        r["trades_par_an"] = round(len(tt) / (tt["day"].max() - tt["day"].min()).days * 365.25, 1)
        r["cout_median_r"] = float(tt["cost_r"].median())
        if "instrument" in tt:
            r["par_instrument_e_net"] = {k: round(float((g["gross_r"] - g["cost_r"]).mean()), 4)
                                         for k, g in tt.groupby("instrument")}
        res.append(r)
        print(line(r), f"| {r['trades_par_an']}/an coût~{r['cout_median_r']:.3f}R", flush=True)
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1, ensure_ascii=False)
