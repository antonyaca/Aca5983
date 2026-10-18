"""Campagne 2 « 1 trade par jour » — INDICES (NASDAQ100, SP500, FTSE100, NIKKEI225), autour de l'ouverture.

Règles fixées le 18/10/2026 AVANT tout calcul de résultat. Seuls des contrôles de DONNÉES ont précédé l'écriture :
densité des minutes par séance, taille médiane des ranges d'ouverture en points (pour estimer le coût en R) et horaire
du pic de volatilité d'ouverture (09:30 NY, 08:00 Londres, 09:00 Tokyo, y compris pendant les semaines de décalage
d'heure d'été). Aucun paramètre ne sera modifié après lecture des résultats.

CADRE (jour/PROTOCOLE.md) : 100 € par R, coûts lib.COST aller-retour (spread + glissement), pas de swap (tout est
clôturé le jour même), coûts ×2 pour Nasdaq et S&P les jours de décision FOMC programmés (liste reprise de
calendrier/run.py). Découverte 2011-2018 / validation 2019-2026. Critère lib.evaluate ; règle du jour lib.regle_anto ;
statistiques journalières lib.stats_jour. Budget : 20 variantes, toutes déclarées ici et enregistrées dans results.json.

SÉANCES (heure locale) : Nasdaq / S&P 09:30-16:00 New York (calendrier XNYS) ; FTSE 08:00-16:30 Londres (XLON) ;
Nikkei 09:00-15:00 Tokyo (XTKS ; fin à 15:00 conservée après le passage de la Bourse de Tokyo à 15:30 le 05/11/2024).
- Seuls les jours de séance officielle sont tradés (exchange_calendars, figé dans calendriers.csv.gz) : les jours fériés
  où le CFD cote quand même sont exclus. Clôture anticipée (veille de Noël, etc.) : la séance finit à l'heure officielle.
- Séance valable : 1re minute à l'heure exacte d'ouverture, ≥ 50 % des minutes présentes, aucun trou > 30 minutes.
- Barre journalière = séance valable (O = ouverture de la 1re minute, H, L, C = clôture de la dernière minute).
  Séance précédente = séance officielle précédente au calendrier ; si elle n'est pas valable, pas de trade pour les
  règles qui en ont besoin (Williams, gap). ATR14 = moyenne des 14 vrais ranges des séances valables PRÉCÉDENTES.
  SMA200 = moyenne des 200 dernières clôtures valables jusqu'à la veille incluse. Filtre de tendance : achats seulement
  si la clôture de la veille > SMA200, ventes seulement si elle est < SMA200.

EXÉCUTION (minutes M1, prix bid HistData)
- « Entrée à la clôture d'une bougie » = ouverture de la 1re minute ≥ fin de la bougie (5 min de retard au plus, sinon
  pas de trade).
- Ordre stop d'entrée sur un niveau : rempli au niveau, ou à l'ouverture de la minute si elle s'ouvre au-delà ; deux
  niveaux franchis dans la même minute → plus aucun trade de cette règle ce jour-là.
- Stop prioritaire sur l'objectif dans une même minute ; dans la minute d'entrée d'un ordre stop, stop touché → perte
  (prudent) ; minute qui s'ouvre au-delà du stop → sortie à son ouverture ; objectif rempli à son niveau (jamais mieux).
- Sinon sortie à la clôture de la dernière minute de la séance.
- 1 R = |entrée − stop| ; gross_r = (sortie − entrée) × sens / R ; cost_r = COST / R (×2 FOMC, US seulement).
- Candidats « un trade à la fois » : après une sortie, le signal suivant est cherché à partir de la minute qui suit la
  sortie, dans la même fenêtre d'entrée (au plus 10 candidats par jour). lib.regle_anto garde le 1er trade du jour, puis
  le 1er candidat entrant après sa sortie seulement s'il est perdant (net < 0).
- Version « 4 indices » : union des candidats des 4 marchés (t_in en UTC, jour = date locale de la séance) → 1er signal
  du jour tous indices confondus (Nikkei, puis FTSE, puis US), 2e seulement si le 1er perd.

RÈGLES
A. Bougie M15 d'ouverture — idée d'Anto (son EA sur l'or) ; version M5 avec objectif 10 R : Zarattini & Aziz 2023
   (SSRN 4416622), « brut reproduit, net nul » sur CFD (réplication MQL5 2026). Bougie = minutes [ouverture, +15)
   (≥ 10 minutes présentes). Sens = signe(clôture − ouverture de la bougie) ; égalité → pas de trade. Entrée à la clôture
   de la bougie ; stop = autre extrémité (bas pour un achat) ; objectif k × R. Un seul candidat par jour.
   M15 plutôt que M5 : en 2011-2017 la 1re bougie M5 du Nasdaq mesure 6-9 pts → frais 0,2-0,35 R (leçon clé).
B. ORB 15 min (Crabel 1990 ; Holmberg, Lönnbark & Lundström 2013) : range [ouverture, +15) (≥ 10 min) ; ordres stop au
   plus haut (achat) et au plus bas (vente) de ouverture+15 à ouverture+180 ; stop = bord opposé ; objectif 2 R.
C. ORB 60 min : range [ouverture, +60) (≥ 40 min) ; entrées de ouverture+60 à ouverture+180 ; stop = bord opposé ;
   objectif k × R. (B à 2 R et C à 1 R visent à peu près la même distance au-delà du niveau : 2 ranges de 15 min
   ≈ 1 range de 60 min.)
D. Williams k = 0,5 avec objectif — VARIANTE D'UNE STRATÉGIE VALIDÉE (Williams k = 0,5 Nasdaq, sortie en clôture) :
   niveaux = ouverture ± 0,5 × amplitude de la séance précédente ; ordres stop sur toute la séance (comme l'original) ;
   stop = ouverture ; objectif 1 R (= ouverture ± 1 × amplitude de la veille) au lieu de la clôture.
E. 1er repli sur l'EMA20 M5 dans le sens des 30 premières minutes (Raschke & Connors 1995, « Holy Grail » ; Al Brooks) :
   sens = signe(clôture de la minute ouverture+29 − ouverture). EMA20 des clôtures M5 (bougies M5 calées sur l'horloge,
   construites sur toutes les minutes du CFD, calcul continu depuis 2010). Signal = 1re bougie M5 commençant entre
   ouverture+30 et ouverture+175 dont le bas ≤ EMA20 et la clôture > EMA20 (achat ; miroir pour la vente), EMA20 de la
   bougie elle-même (connue à sa clôture). Entrée à sa clôture ; stop = 0,5 × ATR14 ; objectif 1:1 (0,5 × ATR14).
   Signal suivant : bougie commençant après la minute de sortie.
F. Gap & go confirmé : gap = ouverture − clôture de la séance précédente ; si |gap| ≥ 0,25 × ATR14 et si la 1re bougie
   M15 clôture dans le sens du gap → entrée à sa clôture dans le sens du gap ; stop = clôture de la veille (gap comblé
   = idée invalidée) ; objectif 1:1 ; un candidat par jour. (Le comblement de gap avec TP/SL fixes 1:1 a déjà été testé
   sur les 4 indices : retour_moyenne V13/V14, non refait.)

VARIANTES (20)
 V01 A, objectif 1 R — NASDAQ100            V11 C, objectif 2 R — NASDAQ100
 V02 A, objectif 1 R — FTSE100              V12 C, objectif 1 R + filtre SMA200 — NASDAQ100
 V03 A, objectif 1 R — 4 indices (1er signal) V13 D (Williams, objectif 1 R) — NASDAQ100  [variante d'un validé]
 V04 A, objectif 2 R — NASDAQ100            V14 D — SP500
 V05 B (ORB 15, objectif 2 R) — NASDAQ100   V15 D — NIKKEI225
 V06 C (ORB 60, objectif 1 R) — NASDAQ100   V16 D — 4 indices (1er signal)
 V07 C, objectif 1 R — SP500                V17 D + filtre SMA200 — NASDAQ100  [variante d'un validé]
 V08 C, objectif 1 R — FTSE100              V18 E (repli EMA20 M5) — NASDAQ100
 V09 C, objectif 1 R — NIKKEI225            V19 E — SP500
 V10 C, objectif 1 R — 4 indices (1er signal) V20 F (gap & go confirmé) — NASDAQ100
Les résultats par marché des règles A, C et D calculés pour les versions « 4 indices » (A sur S&P et Nikkei, D sur FTSE)
sont des diagnostics, pas des variantes : ils ne peuvent pas être déclarés validés.

CONTRÔLE (hors budget, pas une variante) : Williams k = 0,5 Nasdaq sortie en clôture, 1er niveau seulement (règle
validée) → doit retrouver les trades de robustesse/three_strats.py (hors_echantillon/trades_NASDAQ100.csv.gz) aux
mêmes dates.

AJOUT APRÈS LECTURE DES RÉSULTATS (18/10/2026, information seulement, ne change aucune règle ni aucun verdict) :
clé « sensibilite_cout_proportionnel » de results.json = lib.evaluate des mêmes trades avec un coût proportionnel au
prix (1,25 pb du prix d'entrée, ×2 FOMC), convention de hors_echantillon/README.md qui avait servi à valider le Williams
Nasdaq. Calculée pour TOUTES les variantes Nasdaq et pour le contrôle (pas de convention établie pour les autres marchés).

Usage : python3 run.py  (un marché à la fois, ≈ 1 Go de mémoire au plus ; écrit results.json, candidats.csv.gz,
trades.csv.gz et calendriers.csv.gz dans ce dossier).
"""
import gc
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa: E402

PYLIB = "/tmp/claude-0/-home-claude/1a5d9817-381e-5156-b888-c64c4882cf71/scratchpad/pylib"  # exchange_calendars
CAL_CSV = os.path.join(HERE, "calendriers.csv.gz")

# marché : (fuseau, ouverture, fin de séance standard en minutes locales, calendrier)
MK = {"NASDAQ100": ("America/New_York", 570, 960, "XNYS"),
      "SP500": ("America/New_York", 570, 960, "XNYS"),
      "FTSE100": ("Europe/London", 480, 990, "XLON"),
      "NIKKEI225": ("Asia/Tokyo", 540, 900, "XTKS")}
US = {"NASDAQ100", "SP500"}
INDICES = list(MK)
WIN_END = 180            # fin des entrées (ORB, EMA) : ouverture + 180 min
KMAX = 10                # candidats max par jour et par règle
# Décisions FOMC programmées 2011-2026 (reprises de calendrier/run.py, sources federalreserve.gov)
FOMC = set(pd.to_datetime("""
2011-01-26 2011-03-15 2011-04-27 2011-06-22 2011-08-09 2011-09-21 2011-11-02 2011-12-13
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
2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29 2026-09-16""".split()))

R_A = ("Bougie M15 d'ouverture : sens de la bougie [ouverture, +15 min), entrée à sa clôture, stop à l'autre extrémité, "
       "objectif {k} R, sinon sortie en clôture de séance ; 1 trade max par jour.")
R_B = ("ORB 15 min : ordres stop au plus haut / plus bas des 15 premières minutes, entrées jusqu'à ouverture + 3 h, "
       "stop au bord opposé, objectif 2 R, sinon clôture ; après une perte, 2e cassure possible.")
R_C = ("ORB 60 min : ordres stop au plus haut / plus bas de la 1re heure, entrées jusqu'à ouverture + 3 h, stop au "
       "bord opposé, objectif {k} R, sinon clôture ; après une perte, 2e cassure possible.{f}")
R_D = ("Williams k = 0,5 avec objectif (variante d'une stratégie validée) : ordres stop à ouverture ± 0,5 × amplitude "
       "de la veille, toute la séance, stop = ouverture, objectif 1 R au lieu de la clôture ; après une perte, l'autre "
       "niveau peut déclencher un 2e trade.{f}")
R_E = ("1er repli sur l'EMA20 M5 dans le sens des 30 premières minutes : bougie M5 (début entre ouverture + 30 et + 175 "
       "min) dont le bas touche l'EMA20 et qui clôture au-dessus (miroir en vente) ; entrée à sa clôture ; stop et "
       "objectif à 0,5 × ATR14 (1:1) ; repli suivant possible après une perte.")
R_F = ("Gap & go confirmé : |gap| ≥ 0,25 × ATR14 et 1re bougie M15 dans le sens du gap ; entrée à sa clôture dans le "
       "sens du gap ; stop = clôture de la veille ; objectif 1:1 ; 1 trade max par jour.")
SMA_TXT = " Filtre : achats seulement si clôture de la veille > SMA200 journalière, ventes seulement si < SMA200."
MULTI = " 4 indices : 1er signal du jour tous indices confondus (Nikkei, FTSE, puis US)."

# code : (règle calculée, marchés, libellé, texte des règles)
VARIANTS = {
    "V01": ("A1", ["NASDAQ100"], "Bougie M15 d'ouverture 1:1 Nasdaq", R_A.format(k=1)),
    "V02": ("A1", ["FTSE100"], "Bougie M15 d'ouverture 1:1 FTSE", R_A.format(k=1)),
    "V03": ("A1", INDICES, "Bougie M15 d'ouverture 1:1, 4 indices", R_A.format(k=1) + MULTI),
    "V04": ("A2", ["NASDAQ100"], "Bougie M15 d'ouverture 1:2 Nasdaq", R_A.format(k=2)),
    "V05": ("B", ["NASDAQ100"], "ORB 15 min 1:2 Nasdaq", R_B),
    "V06": ("C1", ["NASDAQ100"], "ORB 60 min 1:1 Nasdaq", R_C.format(k=1, f="")),
    "V07": ("C1", ["SP500"], "ORB 60 min 1:1 S&P 500", R_C.format(k=1, f="")),
    "V08": ("C1", ["FTSE100"], "ORB 60 min 1:1 FTSE", R_C.format(k=1, f="")),
    "V09": ("C1", ["NIKKEI225"], "ORB 60 min 1:1 Nikkei", R_C.format(k=1, f="")),
    "V10": ("C1", INDICES, "ORB 60 min 1:1, 4 indices", R_C.format(k=1, f="") + MULTI),
    "V11": ("C2", ["NASDAQ100"], "ORB 60 min 1:2 Nasdaq", R_C.format(k=2, f="")),
    "V12": ("C1F", ["NASDAQ100"], "ORB 60 min 1:1 + SMA200 Nasdaq", R_C.format(k=1, f=SMA_TXT)),
    "V13": ("D1", ["NASDAQ100"], "Williams 0,5 objectif 1:1 Nasdaq", R_D.format(f="")),
    "V14": ("D1", ["SP500"], "Williams 0,5 objectif 1:1 S&P 500", R_D.format(f="")),
    "V15": ("D1", ["NIKKEI225"], "Williams 0,5 objectif 1:1 Nikkei", R_D.format(f="")),
    "V16": ("D1", INDICES, "Williams 0,5 objectif 1:1, 4 indices", R_D.format(f="") + MULTI),
    "V17": ("D1F", ["NASDAQ100"], "Williams 0,5 1:1 + SMA200 Nasdaq", R_D.format(f=SMA_TXT)),
    "V18": ("E", ["NASDAQ100"], "1er repli EMA20 M5 Nasdaq", R_E),
    "V19": ("E", ["SP500"], "1er repli EMA20 M5 S&P 500", R_E),
    "V20": ("F", ["NASDAQ100"], "Gap & go confirmé Nasdaq", R_F),
}
# règles à calculer par marché (diagnostics compris)
RULES = {"NASDAQ100": ["A1", "A2", "B", "C1", "C2", "C1F", "D1", "D1F", "E", "F", "CTRL"],
         "SP500": ["A1", "C1", "D1", "E"],
         "FTSE100": ["A1", "C1", "D1"],
         "NIKKEI225": ["A1", "C1", "D1"]}
COLS = ["rule", "instrument", "day", "t_in", "t_out", "hm_in", "hm_out", "d", "entry", "stop", "tp", "exit", "risk",
        "gross_r", "cost_r", "why"]


# ------------------------------------------------------------------------------------------------ données
def calendars():
    """Séances officielles et heure de clôture locale (minutes) ; figées dans calendriers.csv.gz au 1er passage."""
    if not os.path.exists(CAL_CSV):
        sys.path.append(PYLIB)
        import exchange_calendars as xc
        rows = []
        for code, tz in (("XNYS", "America/New_York"), ("XLON", "Europe/London"), ("XTKS", "Asia/Tokyo")):
            s = xc.get_calendar(code, start="2010-06-01", end="2026-12-31").schedule
            idx = s.index.tz_localize(None) if s.index.tz is not None else s.index
            cl = s["close"].dt.tz_convert(tz)
            rows.append(pd.DataFrame({"code": code, "day": idx, "close_hm": (cl.dt.hour * 60 + cl.dt.minute).values}))
        pd.concat(rows, ignore_index=True).to_csv(CAL_CSV, index=False)
    c = pd.read_csv(CAL_CSV, parse_dates=["day"])
    return {code: dict(zip(g["day"], g["close_hm"].astype(int))) for code, g in c.groupby("code")}


def build(inst, cal):
    """Séances valables (tableaux M1), barres journalières et, pour Nasdaq / S&P, la table M5 24 h avec EMA20."""
    tz, op, cl, code = MK[inst]
    df = lib.load(inst, tz)
    tm = df["time"].values.astype("datetime64[m]").astype(np.int64)     # minutes UTC depuis 1970
    hm_all = df["hm"].values.astype(np.int32)
    O_, H_, L_, C_ = (df[c].values for c in ("open", "high", "low", "close"))
    day_all = df["day"].values
    m5 = None
    if "E" in RULES[inst]:
        g = pd.DataFrame({"k": tm // 5, "h": H_, "l": L_, "c": C_}).groupby("k", sort=True)
        t5 = g.agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
        ema = t5["c"].ewm(span=20, adjust=False).mean()
        m5 = (t5.index.values.astype(np.int64), t5["h"].values, t5["l"].values, t5["c"].values, ema.values)
        del g, t5, ema
    closes = cal[code]
    sel = np.where((hm_all >= op) & (hm_all < cl))[0]
    ds = day_all[sel]
    cut = np.r_[0, np.where(ds[1:] != ds[:-1])[0] + 1, len(sel)]
    days, reject = {}, {"hors_calendrier": 0, "1re_minute": 0, "minutes<50%": 0, "trou>30min": 0}
    for a, b in zip(cut[:-1], cut[1:]):
        d = pd.Timestamp(ds[a])
        if d.dayofweek >= 5 or d not in closes:
            reject["hors_calendrier"] += 1
            continue
        cl_d = min(cl, closes[d])
        idx = sel[a:b]
        idx = idx[hm_all[idx] < cl_d]
        hm = hm_all[idx]
        if len(hm) == 0 or hm[0] != op:
            reject["1re_minute"] += 1
            continue
        if len(hm) < 0.5 * (cl_d - op):
            reject["minutes<50%"] += 1
            continue
        if len(hm) > 1 and np.diff(hm).max() - 1 > 30:
            reject["trou>30min"] += 1
            continue
        days[d] = (hm, O_[idx], H_[idx], L_[idx], C_[idx], tm[idx])
    del df, tm, hm_all, O_, H_, L_, C_, day_all
    gc.collect()
    D = sorted(days)
    daily = pd.DataFrame({"O": [days[d][1][0] for d in D], "H": [days[d][2].max() for d in D],
                          "L": [days[d][3].min() for d in D], "C": [days[d][4][-1] for d in D]}, index=pd.DatetimeIndex(D))
    cal_days = sorted(closes)
    prev_cal = dict(zip(cal_days[1:], cal_days[:-1]))
    prev_ok = np.array([prev_cal.get(d) in days for d in D])
    pc = daily["C"].shift(1)
    tr = np.where(prev_ok, np.maximum(daily["H"], pc) - np.minimum(daily["L"], pc), daily["H"] - daily["L"])
    daily["ATR"] = pd.Series(tr, index=daily.index).rolling(14).mean().shift(1)
    daily["PR"] = np.where(prev_ok, (daily["H"] - daily["L"]).shift(1), np.nan)
    daily["PC"] = np.where(prev_ok, pc, np.nan)
    daily["CPREV"] = pc
    daily["SMA200"] = daily["C"].rolling(200).mean().shift(1)
    info = {"seances_valables_par_an": {str(k): int(v) for k, v in daily.groupby(daily.index.year).size().items()},
            "rejets": reject}
    return days, daily, m5, info


# ------------------------------------------------------------------------------------------------ exécution
def sim(O, H, L, C, j, entry, d, stop, tp):
    """Sortie d'une position entrée dans la minute j. Retourne (indice de sortie, prix, motif)."""
    last = len(C) - 1
    if d == 1:
        if L[j] <= stop:
            return j, stop, "SL"
        if H[j] >= tp:
            return j, tp, "TP"
        sl, tg = L[j + 1:] <= stop, H[j + 1:] >= tp
    else:
        if H[j] >= stop:
            return j, stop, "SL"
        if L[j] <= tp:
            return j, tp, "TP"
        sl, tg = H[j + 1:] >= stop, L[j + 1:] <= tp
    a = int(sl.argmax()) if sl.any() else None
    b = int(tg.argmax()) if tg.any() else None
    if a is None and b is None:
        return last, C[last], "EOD"
    if b is None or (a is not None and a <= b):
        k = j + 1 + a
        return k, (min(O[k], stop) if d == 1 else max(O[k], stop)), "SL"
    return j + 1 + b, tp, "TP"


def breakout(S, up, dn, w0, w1, lstop, sstop, tpm, allow_l=True, allow_s=True, kmax=KMAX):
    """Ordres stop d'entrée sur deux niveaux, un trade à la fois ; fenêtre d'entrée hm ∈ [w0, w1)."""
    hm, O, H, L, C, tm = S
    out, i, iend = [], int(np.searchsorted(hm, w0)), int(np.searchsorted(hm, w1))
    while i < iend and len(out) < kmax:
        hu = H[i:iend] >= up if allow_l else np.zeros(iend - i, bool)
        hd = L[i:iend] <= dn if allow_s else np.zeros(iend - i, bool)
        hit = hu | hd
        if not hit.any():
            break
        m = int(hit.argmax())
        j = i + m
        if hu[m] and hd[m]:
            break
        d = 1 if hu[m] else -1
        entry = max(O[j], up) if d == 1 else min(O[j], dn)
        stop = lstop if d == 1 else sstop
        risk = (entry - stop) * d
        if not risk > 0:
            i = j + 1
            continue
        tp = entry + d * tpm * risk
        k, px, why = sim(O, H, L, C, j, entry, d, stop, tp)
        out.append((j, k, d, entry, stop, tp, px, risk, why))
        i = k + 1
    return out


def first_candle(S, op, tpm, gap_dir=0, pc=np.nan):
    """Règle A (gap_dir = 0) ou F (gap_dir = ±1, stop = clôture de la veille pc)."""
    hm, O, H, L, C, tm = S
    e = int(np.searchsorted(hm, op + 15))
    if e < 10 or e >= len(hm) or hm[e] >= op + 20:
        return []
    d = int(np.sign(C[e - 1] - O[0]))
    if d == 0 or (gap_dir and d != gap_dir):
        return []
    entry = O[e]
    stop = pc if gap_dir else (L[:e].min() if d == 1 else H[:e].max())
    risk = (entry - stop) * d
    if not risk > 0:
        return []
    tp = entry + d * tpm * risk
    k, px, why = sim(O, H, L, C, e, entry, d, stop, tp)
    return [(e, k, d, entry, stop, tp, px, risk, why)]


def orb(S, op, n, tpm, allow_l=True, allow_s=True):
    hm, O, H, L, C, tm = S
    e = int(np.searchsorted(hm, op + n))
    if e < (2 * n) // 3:
        return []
    up, dn = H[:e].max(), L[:e].min()
    return breakout(S, up, dn, op + n, op + WIN_END, dn, up, tpm, allow_l, allow_s)


def williams(S, op, pr, tpm, allow_l=True, allow_s=True, kmax=KMAX):
    if not pr > 0:
        return []
    o = S[1][0]
    return breakout(S, o + 0.5 * pr, o - 0.5 * pr, op, 10 ** 5, o, o, tpm, allow_l, allow_s, kmax)


def ema_pullback(S, op, atr, m5):
    hm, O, H, L, C, tm = S
    e30 = int(np.searchsorted(hm, op + 30))
    i1 = int(np.searchsorted(hm, op + WIN_END))
    if e30 == 0 or e30 >= i1 or not atr > 0:
        return []
    di = int(np.sign(C[e30 - 1] - O[0]))
    if di == 0:
        return []
    keys, h5, l5, c5, e5 = m5
    ks = np.unique(tm[e30:i1] // 5)
    p = np.searchsorted(keys, ks)
    if di == 1:
        sig = (l5[p] <= e5[p]) & (c5[p] > e5[p])
    else:
        sig = (h5[p] >= e5[p]) & (c5[p] < e5[p])
    out, after = [], -1
    for q in np.where(sig)[0]:
        start = int(ks[q]) * 5
        if start <= after:
            continue
        j = int(np.searchsorted(tm, start + 5))
        if j >= len(tm) or tm[j] >= start + 10:
            continue
        entry = O[j]
        stop, tp = entry - di * 0.5 * atr, entry + di * 0.5 * atr
        k, px, why = sim(O, H, L, C, j, entry, di, stop, tp)
        out.append((j, k, di, entry, stop, tp, px, 0.5 * atr, why))
        after = int(tm[k])
        if len(out) >= KMAX:
            break
    return out


def candidates(inst, days, daily, m5):
    tz, op, cl, code = MK[inst]
    rows = []
    for d, S in days.items():
        x = daily.loc[d]
        trend = 0
        if x["SMA200"] > 0:
            trend = 1 if x["CPREV"] > x["SMA200"] else (-1 if x["CPREV"] < x["SMA200"] else 0)
        res = {}
        for rule in RULES[inst]:
            if rule == "A1":
                res[rule] = first_candle(S, op, 1.0)
            elif rule == "A2":
                res[rule] = first_candle(S, op, 2.0)
            elif rule == "B":
                res[rule] = orb(S, op, 15, 2.0)
            elif rule == "C1":
                res[rule] = orb(S, op, 60, 1.0)
            elif rule == "C2":
                res[rule] = orb(S, op, 60, 2.0)
            elif rule == "C1F":
                res[rule] = orb(S, op, 60, 1.0, trend == 1, trend == -1) if trend else []
            elif rule == "D1":
                res[rule] = williams(S, op, x["PR"], 1.0)
            elif rule == "D1F":
                res[rule] = williams(S, op, x["PR"], 1.0, trend == 1, trend == -1) if trend else []
            elif rule == "CTRL":
                res[rule] = williams(S, op, x["PR"], np.inf, kmax=1)
            elif rule == "E":
                res[rule] = ema_pullback(S, op, x["ATR"], m5)
            elif rule == "F":
                gap = x["O"] - x["PC"]
                ok = x["ATR"] > 0 and abs(gap) >= 0.25 * x["ATR"]
                res[rule] = first_candle(S, op, 1.0, int(np.sign(gap)), x["PC"]) if ok else []
        hm, tmin = S[0], S[5]
        cm = 2.0 if (inst in US and d in FOMC) else 1.0
        for rule, lst in res.items():
            for (j, k, dd, entry, stop, tp, px, risk, why) in lst:
                rows.append((rule, inst, d, int(tmin[j]), int(tmin[k]), int(hm[j]), int(hm[k]), dd, entry, stop, tp, px,
                             risk, (px - entry) * dd / risk, cm * lib.COST[inst] / risk, why))
    return pd.DataFrame(rows, columns=COLS)


# ------------------------------------------------------------------------------------------------ évaluation
def diag(c, taken):
    t = taken[taken["day"] >= lib.START]
    net = t["gross_r"] - t["cost_r"]
    first = ~t.duplicated("day")
    out = {"candidats": int((c["day"] >= lib.START).sum()), "trades_pris": int(len(t)),
           "part_2e_trade_pct": round(float((~first).mean() * 100), 1) if len(t) else None,
           "trades_par_an_median": float(t.groupby(t["day"].dt.year).size().median()) if len(t) else None,
           "e_brute": round(float(t["gross_r"].mean()), 4) if len(t) else None,
           "cout_median_r": {"2011-2018": round(float(t.loc[t["day"] < lib.SPLIT, "cost_r"].median()), 3) if (t["day"] < lib.SPLIT).any() else None,
                             "2019-2026": round(float(t.loc[t["day"] >= lib.SPLIT, "cost_r"].median()), 3) if (t["day"] >= lib.SPLIT).any() else None},
           "sorties_pct": {k: round(float(v) * 100, 1) for k, v in t["why"].value_counts(normalize=True).items()},
           "achats_pct": round(float((t["d"] == 1).mean() * 100), 1) if len(t) else None}
    if t["instrument"].nunique() > 1:
        out["par_marche"] = {m: {"trades": int(len(g)), "e_nette": round(float((g["gross_r"] - g["cost_r"]).mean()), 4),
                                 "resultat_eur": round(float((g["gross_r"] - g["cost_r"]).sum() * 100))}
                             for m, g in t.groupby("instrument")}
    out["net_1er_trade"] = round(float(net[first.values].mean()), 4) if len(t) else None
    out["net_2e_trade"] = round(float(net[~first.values].mean()), 4) if (~first).any() else None
    return out


def evaluate_variant(code, c, label, regles):
    c = c.reset_index(drop=True).copy()
    c["t_in"] = pd.to_datetime(c["t_in"], unit="m", utc=True)
    c["t_out"] = pd.to_datetime(c["t_out"], unit="m", utc=True)
    taken = lib.regle_anto(c)
    r = lib.evaluate(taken, f"{code} {label}")
    r["jour"] = lib.stats_jour(taken)
    r["regles"] = regles
    r["diagnostic"] = diag(c, taken)
    return r, taken


def main():
    cal = calendars()
    allc, info = [], {}
    for inst in INDICES:                        # un marché à la fois
        days, daily, m5, inf = build(inst, cal)
        c = candidates(inst, days, daily, m5)
        info[inst] = inf
        print(f"{inst}: {len(days)} séances valables, {len(c)} candidats", flush=True)
        allc.append(c)
        del days, daily, m5
        gc.collect()
    cand = pd.concat(allc, ignore_index=True)
    cand.to_csv(os.path.join(HERE, "candidats.csv.gz"), index=False, float_format="%.6f")
    results, taken_all = {}, []
    for code, (rule, insts, label, regles) in VARIANTS.items():
        c = cand[(cand["rule"] == rule) & cand["instrument"].isin(insts)]
        r, taken = evaluate_variant(code, c, label, regles)
        results[code] = r
        taken_all.append(taken.assign(variante=code))
        print(lib.line(r), "|", lib.line_jour(r["jour"]), flush=True)
    diags = {}
    for (rule, inst), c in cand.groupby(["rule", "instrument"]):
        if rule == "CTRL" or any(v[0] == rule and v[1] == [inst] for v in VARIANTS.values()):
            continue
        r, _ = evaluate_variant(f"diag {rule}", c, f"{inst} (diagnostic, non compté)", "voir règle " + rule)
        diags[f"{rule} {inst}"] = r
        print("  [diag]", lib.line(r), flush=True)
    ctrl = cand[cand["rule"] == "CTRL"]
    rc, ctrl_taken = evaluate_variant("CTRL", ctrl, "Williams 0,5 Nasdaq sortie clôture (contrôle)", "contrôle")
    print("  [contrôle]", lib.line(rc), flush=True)
    taken_df = pd.concat(taken_all, ignore_index=True)
    taken_df.to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6f")
    # ajout après résultats (information) : coût proportionnel au prix, variantes Nasdaq + contrôle
    sens = {}
    for code, x in [(k, taken_df[taken_df["variante"] == k]) for k, v in VARIANTS.items() if v[1] == ["NASDAQ100"]] + \
            [("CTRL", ctrl_taken)]:
        x = x.copy()
        mult = np.where(x["day"].isin(FOMC), 2.0, 1.0)
        x["cost_r"] = mult * 1.25e-4 * x["entry"] / x["risk"]
        s = lib.evaluate(x, f"{code} coût ∝ prix (information)")
        sens[code] = s
        print("  [coût ∝ prix]", lib.line(s), flush=True)
    out = {"variantes": results, "diagnostics_par_marche": diags, "controle_williams_cloture": rc,
           "sensibilite_cout_proportionnel": sens, "donnees": info}
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
