"""Campagne « 1 trade par jour » — FOREX ET MÉTAUX, sessions de Londres et de New York (agent forex_or, 18/10/2026).

Règles écrites AVANT tout calcul de résultat. Seuls des diagnostics de COÛT (sans résultat de stratégie) ont été calculés
avant : coût aller-retour rapporté à 0,5 ATR journalier (forex et or 0,02-0,08 R ; argent 0,10-0,33 R), à l'ATR14 H1
de 08:00 Londres (forex 0,10-0,25 R ; argent jusqu'à 1,15 R) et aux ranges d'ouverture (0,04-0,20 R).

MARCHÉS : EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, XAGUSD (M1 bid, lib.load en vrai UTC), 2011 → 09/10/2026.
Heures locales Europe/London et America/New_York converties en UTC jour par jour (heures d'été gérées).

CADRE COMMUN (toutes variantes)
- Journée J = journée de trading FX close à 17:00 New York (de 17:00 NY la veille à 17:00 NY) ; étiquette = date de J
  (la même à Londres et à New York pour toutes les heures utilisées) ; jours ouvrés seulement.
- Indicateurs connus avant J, sur les journées complètes (>= 600 minutes) précédentes : ATR = ATR14 journalier ;
  SMA20 = moyenne des 20 dernières clôtures 17:00 NY ; PDH/PDL/PDC = plus haut / plus bas / clôture de la dernière
  journée complète ; PWH/PWL = plus haut / plus bas de la semaine calendaire précédente.
  Tendance haussière si PDC > SMA20, baissière si PDC < SMA20.
- Pré-séance = de 17:00 NY la veille à 08:00 Londres (HS / LS = plus haut / plus bas). Niveau « vierge » = non touché
  en pré-séance (niveau au-dessus : HS < niveau ; au-dessous : LS > niveau). 1er contact du jour = 1re minute de la
  fenêtre d'entrée où le prix franchit le niveau (plus haut > niveau, ou plus bas < niveau).
- Fenêtre d'entrée : de l'heure de début de la variante jusqu'à 12:00 New York ; sortie forcée à 16:00 New York
  (clôture de la dernière minute < 16:00 NY) : jamais de position la nuit, donc pas de swap.
- Exécution M1 : ordre limite (rejet) rempli AU niveau ; ordre stop (cassure) rempli à max(ouverture, niveau) à l'achat,
  min(ouverture, niveau) à la vente ; entrée à heure fixe = ouverture de la 1re minute >= l'heure (<= 5 min de retard,
  sinon pas de trade). Stop prioritaire sur l'objectif dans la même minute ; dans la minute d'entrée seul le stop est
  testé (perte s'il est touché) ; gap au-delà du stop -> sortie à l'ouverture ; objectif = limite rempli au niveau.
- Un trade à la fois par marché ; le candidat suivant ne peut entrer qu'à partir de la minute qui suit la sortie.
  Niveaux : chaque niveau une fois par jour (son 1er contact ; s'il survient pendant un trade, il est perdu).
  Cassures de range : chaque côté une fois par jour, 1re cassure après la sortie précédente ; les deux côtés franchis
  dans la même minute -> plus de trade ce jour-là sur ce marché.
- Filtre de coût : signal ignoré si le risque < 10 x le coût aller-retour (coût > 0,10 R ; leçon des stops minuscules).
- Coûts lib.COST, x2 les jours d'annonce US (date NY de J) : NFP, CPI, FOMC officiels 2011-2026 (BLS, Réserve fédérale).
- 1 R = distance au stop = 100 EUR. Multi-marchés : TOUS les candidats des 6 marchés passent par lib.regle_anto
  (1er signal du jour tous marchés confondus ; 2e seulement si le 1er perd, entrant strictement après sa sortie).
  Égalité à la même minute : ordre EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, XAGUSD (V10 : tendance la plus forte,
  |PDC - SMA20| / ATR). Les résultats par marché sont des diagnostics, pas des variantes.

VARIANTES (V01-V17 : 17 sur les 20 autorisées, fixées avant tout calcul. L'engagement initial de ne pas utiliser les 3
restantes a été levé pour V18 SEULEMENT, à la demande du coordinateur, après lecture des résultats ; 2 restent inutilisées)
V01 Cassure de la 1re bougie H1 de Londres : range 08:00-09:00 Londres (>= 48 minutes) ; entrée 09:00 Londres ->
    12:00 NY ; stop = bord opposé du range ; objectif 1:1.
V02 Idem V01 avec objectif 1:2.
V03 PDH/PDL, rejet au 1er contact : niveaux vierges ; vente limite au PDH, achat limite au PDL ; entrée 08:00 Londres
    -> 12:00 NY ; stop 0,5 ATR au-delà du niveau ; objectif 0,5 ATR (1:1).
V04 PDH/PDL, cassure au 1er contact : achat stop au PDH, vente stop au PDL ; stop 0,5 ATR ; objectif 1 ATR (1:2).
V05 Points pivots classiques de la veille : P = (H + B + C) / 3, R1 = 2P - B, S1 = 2P - H ; niveaux vierges ; rebond
    au 1er contact (niveau au-dessus -> vente limite, au-dessous -> achat limite) ; entrée 08:00 Londres -> 12:00 NY ;
    stop et objectif 0,5 ATR.
V06 Nombres ronds « 00/50 » (EURUSD, GBPUSD, AUDUSD : multiples de 0,0050 ; USDJPY : 0,50 ; or : 50 $ ; argent :
    0,50 $) : niveaux vierges jusqu'à 4 ATR ; rejet au 1er contact ; entrée 08:00 Londres -> 12:00 NY ; stop et
    objectif 0,5 ATR.
V07 Nombres ronds, cassure au 1er contact (Osler 2003 : stops groupés juste au-delà des chiffres ronds) ; stop 0,5 ATR ;
    objectif 1 ATR (1:2).
V08 Ouverture de New York : range 08:00-09:30 NY (>= 72 minutes) ; entrée 09:30 -> 12:00 NY ; stop = bord opposé ;
    objectif 1:1 ; jours NFP / CPI / FOMC exclus.
V09 « Frankfurt open » : range 07:00-08:00 Londres (>= 48 minutes) ; entrée 08:00 Londres -> 12:00 NY ; stop = bord
    opposé ; objectif 1:1.
V10 Tendance + heure fixe : sens = tendance SMA20 ; achat/vente à 08:00 Londres ; si ce trade est clos, 2e candidat à
    08:00 NY dans le même sens ; stop 0,5 ATR (au lieu de « 1 ATR H1 », trop coûteux, voir plus haut) ; objectif 1:1.
V11 V04 dans le sens de la tendance seulement (cassure du PDH si haussière, du PDL si baissière).
V12 V01 dans le sens de la tendance seulement.
V13 V05 dans le sens de la tendance seulement (achats sur supports si haussière, ventes sur résistances si baissière).
V14 V06 dans le sens de la tendance seulement (idem).
V15 Plus haut / plus bas de la semaine précédente, rejet au 1er contact de la semaine (niveau vierge depuis le début de
    la semaine jusqu'à 08:00 Londres) ; entrée 08:00 Londres -> 12:00 NY ; stop et objectif 0,5 ATR.
V16 V03 dans le sens de la tendance seulement (achat au PDL si haussière, vente au PDH si baissière).
V17 V01 avec stop et objectif fixes de 0,5 ATR (entrée à la cassure du range 08:00-09:00 Londres ; risque indépendant
    de la taille du range).
V18 POST-HOC (ajoutée le 18/10/2026 APRÈS lecture des résultats V01-V17, inspirée du brut très négatif de V15, à la
    demande du coordinateur) : plus haut / plus bas de la semaine précédente, CASSURE au 1er contact de la semaine
    (niveau vierge depuis le début de la semaine jusqu'à 08:00 Londres, comme V15) ; achat stop au PWH, vente stop au
    PWL ; entrée 08:00 Londres -> 12:00 NY ; stop 0,5 ATR ; objectif 1 ATR (1:2) ; sortie 16:00 NY ; même filtre de
    coût ; même règle d'Anto sur les 6 marchés. Choisie après lecture : pas une validation propre, même si le critère passe.

SOURCES DES DATES D'ANNONCE : NFP 2011-2019 = liste BLS de campagne/nfp_2011/run.py ; CPI 2011-2019 (+ 14/01/2020) =
noms des communiqués archivés BLS (https://www.bls.gov/bls/news-release/cpi.htm, cpi_MMJJAAAA) ; FOMC 2011-2019 =
communiqués des réunions programmées (https://www.federalreserve.gov/monetarypolicy/fomchistoricalAAAA.htm) ;
2020-2026 = events/backtest.py et nfp/backtest.py (inchangés).
"""
import gc
import importlib.util
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CAMP = os.path.dirname(os.path.dirname(HERE))
BT = os.path.dirname(CAMP)
sys.path.insert(0, CAMP)
from lib import load, evaluate, line, COST, regle_anto, stats_jour, line_jour, START  # noqa: E402

INSTS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "XAGUSD"]   # ordre de priorité en cas d'égalité
ROUND = {"EURUSD": 0.005, "GBPUSD": 0.005, "AUDUSD": 0.005, "USDJPY": 0.5, "XAUUSD": 50.0, "XAGUSD": 0.5}
MAXLAG = 5
MINR_COST = 10.0          # risque >= 10 x coût
EPOCH = pd.Timestamp("1970-01-01")

# ---------------------------------------------------------------- calendrier des annonces (coûts x2, filtre V08)
_spec = importlib.util.spec_from_file_location("ev", os.path.join(BT, "events", "backtest.py"))
_ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ev)
NFP_2011_2019 = """2011-01-07 2011-02-04 2011-03-04 2011-04-01 2011-05-06 2011-06-03 2011-07-08 2011-08-05 2011-09-02 2011-10-07 2011-11-04 2011-12-02
2012-01-06 2012-02-03 2012-03-09 2012-04-06 2012-05-04 2012-06-01 2012-07-06 2012-08-03 2012-09-07 2012-10-05 2012-11-02 2012-12-07
2013-01-04 2013-02-01 2013-03-08 2013-04-05 2013-05-03 2013-06-07 2013-07-05 2013-08-02 2013-09-06 2013-10-22 2013-11-08 2013-12-06
2014-01-10 2014-02-07 2014-03-07 2014-04-04 2014-05-02 2014-06-06 2014-07-03 2014-08-01 2014-09-05 2014-10-03 2014-11-07 2014-12-05
2015-01-09 2015-02-06 2015-03-06 2015-04-03 2015-05-08 2015-06-05 2015-07-02 2015-08-07 2015-09-04 2015-10-02 2015-11-06 2015-12-04
2016-01-08 2016-02-05 2016-03-04 2016-04-01 2016-05-06 2016-06-03 2016-07-08 2016-08-05 2016-09-02 2016-10-07 2016-11-04 2016-12-02
2017-01-06 2017-02-03 2017-03-10 2017-04-07 2017-05-05 2017-06-02 2017-07-07 2017-08-04 2017-09-01 2017-10-06 2017-11-03 2017-12-08
2018-01-05 2018-02-02 2018-03-09 2018-04-06 2018-05-04 2018-06-01 2018-07-06 2018-08-03 2018-09-07 2018-10-05 2018-11-02 2018-12-07
2019-01-04 2019-02-01 2019-03-08 2019-04-05 2019-05-03 2019-06-07 2019-07-05 2019-08-02 2019-09-06 2019-10-04 2019-11-01 2019-12-06""".split()
# BLS, noms de fichiers cpi_MMJJAAAA de l'archive des communiqués CPI
CPI_BLS = """01142011 02172011 03172011 04152011 05132011 06152011 07152011 08182011 09152011 10192011 11162011 12162011
01192012 02172012 03162012 04132012 05152012 06142012 07172012 08152012 09142012 10162012 11152012 12142012
01162013 02212013 03152013 04162013 05162013 06182013 07162013 08152013 09172013 10302013 11202013 12172013
01162014 02202014 03182014 04152014 05152014 06172014 07222014 08192014 09172014 10222014 11202014 12172014
01162015 02262015 03242015 04172015 05222015 06182015 07172015 08192015 09162015 10152015 11172015 12152015
01202016 02192016 03162016 04142016 05172016 06162016 07152016 08162016 09162016 10182016 11172016 12152016
01182017 02152017 03152017 04142017 05122017 06142017 07142017 08112017 09142017 10132017 11152017 12132017
01122018 02142018 03132018 04112018 05102018 06122018 07122018 08102018 09132018 10112018 11142018 12122018
01112019 02132019 03122019 04102019 05102019 06122019 07112019 08132019 09122019 10102019 11132019 12112019
01142020""".split()
CPI_2011_2019 = [f"{s[4:]}-{s[:2]}-{s[2:4]}" for s in CPI_BLS]
# Réserve fédérale : communiqués des réunions programmées (monetaryAAAAMMJJa.htm)
FOMC_2011_2019 = """20110126 20110315 20110427 20110622 20110809 20110921 20111102 20111213
20120125 20120313 20120425 20120620 20120801 20120913 20121024 20121212
20130130 20130320 20130501 20130619 20130731 20130918 20131030 20131218
20140129 20140319 20140430 20140618 20140730 20140917 20141029 20141217
20150128 20150318 20150429 20150617 20150729 20150917 20151028 20151216
20160127 20160316 20160427 20160615 20160727 20160921 20161102 20161214
20170201 20170315 20170503 20170614 20170726 20170920 20171101 20171213
20180131 20180321 20180502 20180613 20180801 20180926 20181108 20181219
20190130 20190320 20190501 20190619 20190731 20190918 20191030 20191211""".split()
FOMC_2011_2019 = [f"{s[:4]}-{s[4:6]}-{s[6:]}" for s in FOMC_2011_2019]
assert len(NFP_2011_2019) == 108 and len(CPI_2011_2019) == 109 and len(FOMC_2011_2019) == 72
_all = pd.to_datetime(list(_ev.NFP) + list(_ev.CPI) + list(_ev.FOMC) + NFP_2011_2019 + CPI_2011_2019 + FOMC_2011_2019)
assert (_all.dayofweek < 5).all()
MACRO = set(int(x) for x in (_all - EPOCH).days)

VARS = [f"V{i:02d}" for i in range(1, 19)]
LABELS = {
    "V01": "Cassure 1re H1 Londres, TP 1:1", "V02": "Cassure 1re H1 Londres, TP 1:2",
    "V03": "PDH/PDL rejet 1er contact, 1:1", "V04": "PDH/PDL cassure 1er contact, 1:2",
    "V05": "Pivots P/R1/S1 rebond, 1:1", "V06": "Nombres ronds 00/50 rejet, 1:1",
    "V07": "Nombres ronds 00/50 cassure, 1:2", "V08": "Range NY 08:00-09:30 cassure, hors annonces, 1:1",
    "V09": "Frankfurt 07:00-08:00 cassure, 1:1", "V10": "Tendance SMA20 + 08:00 Londres (2e 08:00 NY), 1:1",
    "V11": "PDH/PDL cassure sens tendance, 1:2", "V12": "Cassure 1re H1 Londres sens tendance, 1:1",
    "V13": "Pivots rebond sens tendance, 1:1", "V14": "Nombres ronds rejet sens tendance, 1:1",
    "V15": "Plus haut/bas semaine préc. rejet, 1:1", "V16": "PDH/PDL rejet sens tendance, 1:1",
    "V17": "Cassure 1re H1 Londres, stop/TP 0,5 ATR",
    "V18": "POST-HOC Plus haut/bas semaine préc. cassure, 1:2",
}


def utcmin(days, tz, hm):
    """minutes UTC (depuis 1970) de l'heure locale hm (minutes) du jour `days` (jours depuis 1970)."""
    naive = pd.to_datetime(np.asarray(days), unit="D") + pd.to_timedelta(hm, unit="m")
    loc = pd.DatetimeIndex(naive).tz_localize(tz, ambiguous="raise", nonexistent="raise")
    return loc.tz_convert("UTC").tz_localize(None).values.astype("datetime64[m]").astype(np.int64)


class Mkt:
    def __init__(self, inst):
        df = load(inst, "UTC")
        self.inst = inst
        self.tm = df["time"].values.astype("datetime64[m]").astype(np.int64)
        self.O = df["open"].values.astype(float)
        self.H = df["high"].values.astype(float)
        self.L = df["low"].values.astype(float)
        self.C = df["close"].values.astype(float)
        ny = df["time"].dt.tz_convert("America/New_York").dt.tz_localize(None).values
        del df
        ny = ny.astype("datetime64[m]").astype(np.int64)
        self.td = (ny + 420) // 1440                     # journée de trading (close 17:00 NY)
        del ny
        assert np.all(np.diff(self.tm) > 0) and np.all(np.diff(self.td) >= 0)
        g = pd.DataFrame({"td": self.td, "h": self.H, "l": self.L, "c": self.C}).groupby("td")
        dd = pd.DataFrame({"h": g["h"].max(), "l": g["l"].min(), "c": g["c"].last(), "n": g.size()})
        comp = dd[dd["n"] >= 600].copy()
        pc = comp["c"].shift(1)
        tr = np.maximum(comp["h"] - comp["l"], np.maximum((comp["h"] - pc).abs(), (comp["l"] - pc).abs()))
        comp["atr"] = tr.rolling(14).mean()              # inclut la journée elle-même -> utilisé pour le lendemain
        comp["sma20"] = comp["c"].rolling(20).mean()
        dd["wk"] = (dd.index.values + 3) // 7            # semaine calendaire (lundi = début)
        wk = dd.groupby("wk").agg(h=("h", "max"), l=("l", "min"))
        dd["wtd_h"] = dd.groupby("wk")["h"].transform(lambda s: s.cummax().shift(1))   # jours précédents de la semaine
        dd["wtd_l"] = dd.groupby("wk")["l"].transform(lambda s: s.cummin().shift(1))
        dd["pwh"] = wk["h"].reindex(dd["wk"].values - 1).values
        dd["pwl"] = wk["l"].reindex(dd["wk"].values - 1).values
        self.dd, self.comp = dd, comp


def simulate(m, k, d, E, R, TPd, iend):
    """Entrée minute k, sens d, prix E, stop à R, objectif à TPd ; sortie au plus tard à la clôture de iend-1.
    Retourne (prix de sortie, indice de sortie, type)."""
    S, T = E - d * R, E + d * TPd
    if (m.L[k] <= S) if d == 1 else (m.H[k] >= S):
        return S, k, "SL"
    if iend <= k + 1:
        return m.C[k], k, "T"
    seg = slice(k + 1, iend)
    hs = (m.L[seg] <= S) if d == 1 else (m.H[seg] >= S)
    ht = (m.H[seg] >= T) if d == 1 else (m.L[seg] <= T)
    big = iend + 1
    js = int(hs.argmax()) if hs.any() else big
    jt = int(ht.argmax()) if ht.any() else big
    if js == big and jt == big:
        return m.C[iend - 1], iend - 1, "T"
    if js <= jt:
        j = k + 1 + js
        o = m.O[j]
        return (o if ((o < S) if d == 1 else (o > S)) else S), j, "SL"
    return T, k + 1 + jt, "TP"


def level_trades(m, levels, mode, R, TPd, ia, iz, iend, minR, tag):
    """levels : [(niveau, pos)] pos = +1 au-dessus (résistance), -1 au-dessous (support). mode 'fade' ou 'break'."""
    if R < minR or iz <= ia:
        return []
    cont = []
    for X, pos in levels:
        hit = (m.H[ia:iz] > X) if pos == 1 else (m.L[ia:iz] < X)
        if hit.any():
            cont.append((ia + int(hit.argmax()), X, pos))
    cont.sort()
    rows, free = [], ia
    for j, X, pos in cont:
        if j < free:
            continue                                      # 1er contact pendant un trade : perdu
        if mode == "fade":
            d, E = -pos, X
        else:
            d = pos
            E = max(m.O[j], X) if d == 1 else min(m.O[j], X)
        px, jx, how = simulate(m, j, d, E, R, TPd, iend)
        rows.append(dict(kind=f"{tag}{'+' if pos == 1 else '-'}", d=d, entry=E, exit=px, R=R, i_in=j, i_out=jx, sortie=how))
        free = jx + 1
    return rows


def orb_trades(m, up, dn, ia, iz, iend, stop_mode, tp_mult, sides, minR, R_atr=None, tag="ORB"):
    rows, free, done = [], ia, set()
    while free < iz:
        todo = [s for s in sides if s not in done]
        if not todo:
            break
        n = iz - free
        hu = (m.H[free:iz] > up) if 1 in todo else np.zeros(n, bool)
        hd = (m.L[free:iz] < dn) if -1 in todo else np.zeros(n, bool)
        hit = hu | hd
        if not hit.any():
            break
        jj = int(hit.argmax())
        if hu[jj] and hd[jj]:
            break                                         # deux côtés dans la même minute
        j, d = free + jj, (1 if hu[jj] else -1)
        done.add(d)
        E = max(m.O[j], up) if d == 1 else min(m.O[j], dn)
        if stop_mode == "range":
            R = (E - dn) if d == 1 else (up - E)
            TPd = tp_mult * R
        else:
            R = TPd = R_atr
        if R <= 0 or R < minR:
            free = j + 1                                  # signal ignoré (coût), côté consommé
            continue
        px, jx, how = simulate(m, j, d, E, R, TPd, iend)
        rows.append(dict(kind=f"{tag}{'+' if d == 1 else '-'}", d=d, entry=E, exit=px, R=R, i_in=j, i_out=jx, sortie=how))
        free = jx + 1
    return rows


def round_levels(HS, LS, step, atr):
    eps = step * 1e-6
    k0 = int(np.floor(HS / step)) + 1
    above = []
    while True:
        X = round(k0 * step, 8)
        if X > HS + 4 * atr:
            break
        if X > HS + eps:
            above.append((X, 1))
        k0 += 1
    k1 = int(np.ceil(LS / step)) - 1
    below = []
    while True:
        X = round(k1 * step, 8)
        if X < LS - 4 * atr or X <= 0:
            break
        if X < LS - eps:
            below.append((X, -1))
        k1 -= 1
    return above + below


def gen(inst, keys=None):
    m = Mkt(inst)
    minR = MINR_COST * COST[inst]
    dd, comp = m.dd, m.comp
    cidx = comp.index.values
    days = dd.index.values
    days = days[(((days + 3) % 7) < 5) & (days >= (pd.Timestamp("2010-02-01") - EPOCH).days)]
    pos = np.searchsorted(cidx, days, "left") - 1          # dernière journée complète AVANT J
    ok = pos >= 0
    days, pos = days[ok], pos[ok]
    c_atr, c_sma = comp["atr"].values[pos], comp["sma20"].values[pos]
    c_h, c_l, c_c = comp["h"].values[pos], comp["l"].values[pos], comp["c"].values[pos]
    assert np.all(cidx[pos] < days)
    wtd_h, wtd_l = dd["wtd_h"].reindex(days).values, dd["wtd_l"].reindex(days).values
    pwh, pwl = dd["pwh"].reindex(days).values, dd["pwl"].reindex(days).values
    tm, td = m.tm, m.td
    i_td0 = np.searchsorted(td, days, "left")
    uL7, uL8, uL9 = (utcmin(days, "Europe/London", h) for h in (420, 480, 540))
    uN8, uN930, uN12, uN16 = (utcmin(days, "America/New_York", h) for h in (480, 570, 720, 960))
    iL7, iL8, iL9 = (np.searchsorted(tm, u, "left") for u in (uL7, uL8, uL9))
    iN8, iN930, iN12, iN16 = (np.searchsorted(tm, u, "left") for u in (uN8, uN930, uN12, uN16))
    # 07:00 Londres de J est après le début de J (17:00 NY la veille) et 16:00 NY avant sa fin (17:00 NY)
    assert np.all(uL7 > utcmin(days - 1, "America/New_York", 1020)) and np.all(uN16 < utcmin(days, "America/New_York", 1020))
    out = {k: [] for k in VARS}
    N = len(tm)

    def add(key, rows, D, extra=None):
        if keys is not None and key not in keys:
            return
        for r in rows:
            r["day_n"] = D
            if extra:
                r.update(extra)
            out[key].append(r)

    for k in range(len(days)):
        D = int(days[k])
        atr = c_atr[k]
        if not np.isfinite(atr) or atr <= 0:
            continue
        sma, pdh, pdl, pdc = c_sma[k], c_h[k], c_l[k], c_c[k]
        trend = 0 if not np.isfinite(sma) else (1 if pdc > sma else (-1 if pdc < sma else 0))
        i0, a7, a8, a9 = i_td0[k], iL7[k], iL8[k], iL9[k]
        n8, n930, n12, n16 = iN8[k], iN930[k], iN12[k], iN16[k]
        if a8 >= N or n16 <= a8 or a8 <= i0 or td[a8] != D or td[n16 - 1] != D:
            continue                                      # pas de données de séance appartenant à J
        HS, LS = m.H[i0:a8].max(), m.L[i0:a8].min()
        R05 = 0.5 * atr
        # ---------------- ranges d'ouverture
        if a9 - a8 >= 48 and a9 < n12:
            up, dn = m.H[a8:a9].max(), m.L[a8:a9].min()
            add("V01", orb_trades(m, up, dn, a9, n12, n16, "range", 1.0, (1, -1), minR), D)
            add("V02", orb_trades(m, up, dn, a9, n12, n16, "range", 2.0, (1, -1), minR), D)
            if trend:
                add("V12", orb_trades(m, up, dn, a9, n12, n16, "range", 1.0, (trend,), minR), D)
            add("V17", orb_trades(m, up, dn, a9, n12, n16, "atr", None, (1, -1), minR, R_atr=R05), D)
        if a8 - a7 >= 48 and a7 >= i0:
            up, dn = m.H[a7:a8].max(), m.L[a7:a8].min()
            add("V09", orb_trades(m, up, dn, a8, n12, n16, "range", 1.0, (1, -1), minR), D)
        if D not in MACRO and n930 - n8 >= 72 and n930 < n12:
            up, dn = m.H[n8:n930].max(), m.L[n8:n930].min()
            add("V08", orb_trades(m, up, dn, n930, n12, n16, "range", 1.0, (1, -1), minR), D)
        # ---------------- niveaux de la veille
        lv = []
        if HS < pdh:
            lv.append((pdh, 1))
        if LS > pdl:
            lv.append((pdl, -1))
        add("V03", level_trades(m, lv, "fade", R05, R05, a8, n12, n16, minR, "PD"), D)
        add("V04", level_trades(m, lv, "break", R05, 2 * R05, a8, n12, n16, minR, "PD"), D)
        if trend:
            add("V11", level_trades(m, [x for x in lv if x[1] == trend], "break", R05, 2 * R05, a8, n12, n16, minR, "PD"), D)
            add("V16", level_trades(m, [x for x in lv if x[1] == -trend], "fade", R05, R05, a8, n12, n16, minR, "PD"), D)
        # ---------------- pivots
        P = (pdh + pdl + pdc) / 3.0
        piv = []
        for X, nm in ((P, "P"), (2 * P - pdl, "R1"), (2 * P - pdh, "S1")):
            if HS < X:
                piv.append((X, 1))
            elif LS > X:
                piv.append((X, -1))
        add("V05", level_trades(m, piv, "fade", R05, R05, a8, n12, n16, minR, "PIV"), D)
        if trend:
            add("V13", level_trades(m, [x for x in piv if x[1] == -trend], "fade", R05, R05, a8, n12, n16, minR, "PIV"), D)
        # ---------------- nombres ronds
        rl = round_levels(HS, LS, ROUND[inst], atr)
        add("V06", level_trades(m, rl, "fade", R05, R05, a8, n12, n16, minR, "RN"), D)
        add("V07", level_trades(m, rl, "break", R05, 2 * R05, a8, n12, n16, minR, "RN"), D)
        if trend:
            add("V14", level_trades(m, [x for x in rl if x[1] == -trend], "fade", R05, R05, a8, n12, n16, minR, "RN"), D)
        # ---------------- semaine précédente
        if np.isfinite(pwh[k]) and np.isfinite(pwl[k]):
            wh = HS if not np.isfinite(wtd_h[k]) else max(HS, wtd_h[k])
            wl = LS if not np.isfinite(wtd_l[k]) else min(LS, wtd_l[k])
            wlv = []
            if wh < pwh[k]:
                wlv.append((pwh[k], 1))
            if wl > pwl[k]:
                wlv.append((pwl[k], -1))
            add("V15", level_trades(m, wlv, "fade", R05, R05, a8, n12, n16, minR, "PW"), D)
            add("V18", level_trades(m, wlv, "break", R05, 2 * R05, a8, n12, n16, minR, "PW"), D)   # POST-HOC
        # ---------------- tendance + heure fixe
        if trend and R05 >= minR:
            strength = abs(pdc - sma) / atr
            j1 = a8 if (a8 < n12 and tm[a8] - uL8[k] <= MAXLAG) else -1
            last = -1
            if j1 >= 0:
                px, jx, how = simulate(m, j1, trend, m.O[j1], R05, R05, n16)
                add("V10", [dict(kind="H08L", d=trend, entry=m.O[j1], exit=px, R=R05, i_in=j1, i_out=jx, sortie=how)],
                    D, {"force": strength})
                last = jx
            j2 = n8 if (n8 < n12 and tm[n8] - uN8[k] <= MAXLAG) else -1
            if j2 >= 0 and j2 > last:
                px, jx, how = simulate(m, j2, trend, m.O[j2], R05, R05, n16)
                add("V10", [dict(kind="H08NY", d=trend, entry=m.O[j2], exit=px, R=R05, i_in=j2, i_out=jx, sortie=how)],
                    D, {"force": strength})

    res = {}
    for key, rows in out.items():
        t = pd.DataFrame(rows)
        if not len(t):
            res[key] = t
            continue
        t["instrument"] = inst
        t["t_in_min"] = tm[t["i_in"].values]
        t["t_out_min"] = tm[t["i_out"].values]
        # contrôles anti look-ahead / cohérence
        dn_ = t["day_n"].values
        kk = np.searchsorted(days, dn_)
        assert np.all(days[kk] == dn_)
        assert np.all(t["i_out"].values >= t["i_in"].values)
        assert np.all(t["t_in_min"].values >= uL7[kk]) and np.all(t["t_in_min"].values < uN12[kk])
        assert np.all(t["t_out_min"].values < uN16[kk])
        assert np.all(t["R"].values >= minR - 1e-12)
        mult = np.where(pd.Index(dn_).isin(list(MACRO)), 2.0, 1.0)
        t["annonce"] = mult > 1
        t["gross_r"] = (t["exit"] - t["entry"]) * t["d"] / t["R"]
        t["cost_r"] = COST[inst] * mult / t["R"]
        t["day"] = pd.to_datetime(dn_, unit="D")
        res[key] = t.drop(columns=["i_in", "i_out"])
    del m
    gc.collect()
    return res


def add_tin(t, key):
    """t_in / t_out triables : minute UTC + priorité (égalité à la même minute) ; t_out = minute de sortie + 0,5
    -> un 2e trade doit entrer à une minute strictement postérieure à la sortie du 1er."""
    t = t.copy()
    if key == "V10":
        rank = t.groupby(["day", "t_in_min"])["force"].rank(ascending=False, method="first") - 1
    else:
        rank = t["instrument"].map({s: i for i, s in enumerate(INSTS)}).astype(float)
    t["t_in"] = t["t_in_min"] + rank.values / 100.0
    t["t_out"] = t["t_out_min"] + 0.5
    return t.sort_values(["day", "t_in"]).reset_index(drop=True)


def regles(key):
    doc = __doc__.split("VARIANTES")[1].split("SOURCES DES DATES")[0]
    blk = doc.split("\n" + key + " ")[1]
    nxt = f"\nV{int(key[1:]) + 1:02d} "
    return (key + " " + blk.split(nxt)[0]).replace("\n    ", " ").strip()


CADRE = __doc__.split("CADRE COMMUN (toutes variantes)")[1].split("VARIANTES")[0].replace("\n  ", " ").strip()


def echecs(r):
    f = []
    if r["net"]["trades"] < 100:
        f.append("< 100 trades")
    if not r["decouverte_2011_2018"]["e_r"] > 0:
        f.append("découverte <= 0")
    if not r["validation_2019_2026"]["e_r"] > 0:
        f.append("validation <= 0")
    if (r["net"]["pf"] or 0) < 1.10:
        f.append("PF < 1,10")
    if not r["e_frais_x2"] > 0:
        f.append("frais x2 <= 0")
    if not r["t_stat"] >= 3:
        f.append("t < 3")
    if not r["sans_top10"] > 0:
        f.append("sans top 10 <= 0")
    a, b = (int(x) for x in r["annees_positives"].split("/"))
    if a / b < 0.6:
        f.append("années positives < 60 %")
    return f


def extras(cand, taken):
    c = cand[cand["day"] >= START]
    tk = taken[taken["day"] >= START]
    yrs = (pd.Timestamp("2026-10-09") - START).days / 365.25
    netc, nett = c["gross_r"] - c["cost_r"], tk["gross_r"] - tk["cost_r"]
    first = tk.groupby("day").cumcount() == 0
    out = {"candidats": int(len(c)), "trades_par_an": round(len(tk) / yrs, 1),
           "cout_median_r": round(float(tk["cost_r"].median()), 4), "e_brute_r": round(float(tk["gross_r"].mean()), 4),
           "e_nette_1er_trade": round(float(nett[first.values].mean()), 4),
           "e_nette_2e_trade": round(float(nett[~first.values].mean()), 4) if (~first).any() else None,
           "part_2e_trades_pct": round(float((~first).mean() * 100), 1),
           "sorties_pct": {k: round(float(v) * 100, 1) for k, v in tk["sortie"].value_counts(normalize=True).items()},
           "candidats_e_nette": round(float(netc.mean()), 4),
           "candidats_t": round(float(netc.mean() / netc.std() * np.sqrt(len(netc))), 2) if len(netc) > 2 else None,
           "par_instrument_pris": {}, "par_instrument_candidats": {}}
    for s, g in tk.groupby("instrument"):
        x = g["gross_r"] - g["cost_r"]
        out["par_instrument_pris"][s] = {"n": int(len(g)), "e_nette": round(float(x.mean()), 4),
                                         "cout_median_r": round(float(g["cost_r"].median()), 4)}
    for s, g in c.groupby("instrument"):
        x = g["gross_r"] - g["cost_r"]
        out["par_instrument_candidats"][s] = {"n": int(len(g)), "e_brute": round(float(g["gross_r"].mean()), 4),
                                              "e_nette": round(float(x.mean()), 4),
                                              "t": round(float(x.mean() / x.std() * np.sqrt(len(x))), 2) if len(x) > 2 else None}
    return out


def main(only=None):
    """only : liste de variantes à (re)calculer seules ; les autres entrées de results.json restent inchangées."""
    store = {k: [] for k in VARS}
    for inst in INSTS:
        t0 = time.time()
        r = gen(inst, only)
        for k, t in r.items():
            if len(t):
                store[k].append(t)
        print(f"{inst} : candidats générés en {time.time() - t0:.0f} s", flush=True)
        del r
        gc.collect()
    results = []
    for k in (only or VARS):
        cand = add_tin(pd.concat(store[k], ignore_index=True), k)
        taken = regle_anto(cand)
        cand["pris"] = cand.index.isin(taken.index)
        r = evaluate(taken, f"{k} {LABELS[k]}")
        r["jour"] = stats_jour(taken)
        r["regles"] = regles(k)
        r["cadre_commun"] = CADRE
        r["echecs"] = echecs(r)
        r.update(extras(cand, taken))
        results.append(r)
        cols = ["day", "instrument", "kind", "d", "entry", "exit", "R", "gross_r", "cost_r", "sortie", "annonce",
                "t_in", "t_out", "t_in_min", "t_out_min", "pris"] + (["force"] if k == "V10" else [])
        cand[cols].to_csv(os.path.join(HERE, "trades", f"{k}.csv.gz"), index=False, float_format="%.6f")
        print(line(r), f"| {r['trades_par_an']}/an coût~{r['cout_median_r']:.3f}R brut{r['e_brute_r']:+.3f}", flush=True)
        print("    ", line_jour(r["jour"]), flush=True)
    if only:
        with open(os.path.join(HERE, "results.json")) as f:
            old = [r for r in json.load(f) if r["label"][:3] not in only]
        results = sorted(old + results, key=lambda r: r["label"][:3])
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
