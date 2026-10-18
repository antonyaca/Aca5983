"""Campagne 2 « 1 trade par jour » — agent « jours positifs » (règles fixées le 18/10/2026 AVANT tout calcul).

Question : existe-t-il une stratégie simple, 1 trade par jour (2e seulement si le 1er perd : lib.regle_anto), avec un
taux de jours positifs ÉLEVÉ **et** une espérance nette positive et robuste (lib.evaluate) ? Paramètres ronds, aucune
retouche après lecture des résultats. 16 variantes déclarées ci-dessous (+ V17-V20 réservées aux contrôles de
robustesse d'une éventuelle variante validée, définis ici). Budget : 20.

CADRE COMMUN
- Données M1 corrigées (lib.load, heure de New York). Résultats 2011-2026 ; 2010 sert au préchauffage des indicateurs.
- Séance 09:30-16:00 NY. Jour tradé en intraday = séance complète au sens de lib.sessions_ny (≥ 90 % des minutes,
  1re minute = 09:30) ; sinon pas de trade (fériés US où le CFD cote jusqu'à 13:00, demi-séances, trous de données).
- Barres journalières des indicateurs = séances « régulières » (≥ 300 minutes, 1re ≤ 09:35, dernière ≥ 15:50) ;
  clôture = dernière minute < 16:00. ATR14 = moyenne simple sur 14 séances du vrai range ; SMA200 des clôtures ;
  RSI2 de Wilder (même calcul que verification/verif_swing.py). Tendance haussière = clôture > SMA200, baissière <.
  Intraday : on utilise les valeurs de la DERNIÈRE séance régulière AVANT le jour J (connues à l'ouverture), écart
  ≤ 4 jours calendaires, sinon pas de trade.
- Nuit / swing (V12, V14, V16) : barres 09:30-15:55 (clôture = minute 15:55, convention de verif_swing.py) ; signal ET
  exécution au prix de clôture de la minute 15:55 du jour J ; sortie à l'ouverture 09:30 d'une séance complète
  ultérieure ; 1 R = ATR14 (séance du signal incluse) ; pas de stop ; swap lib.SWAP × nuits calendaires / 360.
- Exécution minute : stop prioritaire sur l'objectif dans une même minute ; stop franchi par un écart entre deux minutes
  → sortie à l'ouverture de la minute (pire prix) ; objectif franchi par un écart → sortie à l'ouverture (meilleur prix).
  Entrée par ordre stop/limite touché DANS une minute : stop testé dès cette minute, objectif à partir de la minute
  suivante (prudent). Entrée à l'ouverture d'une minute : stop et objectif testés dès cette minute.
  Sortie de fin de journée = clôture de la dernière minute < 16:00.
- 1 R = distance au stop = 100 €. Coût aller-retour lib.COST / R (+ swap si nuit). Pas de calendrier d'annonces
  avant 2020 → coûts ×2 des jours d'annonce non appliqués ; le test « frais ×2 » de lib.evaluate les couvre.
- Trades candidats générés un à la fois par marché (pas de chevauchement), puis lib.regle_anto tous marchés confondus
  (égalité de minute → Nasdaq d'abord), puis lib.evaluate + lib.stats_jour sur les trades pris.

VARIANTES
Famille A — Williams k = 0,5 Nasdaq (stratégie validée) avec des sorties « haute probabilité ».
  Niveaux = ouverture 09:30 ± 0,5 × amplitude H−L de la dernière séance complète ; 1er niveau touché (09:30-15:59) →
  entrée au niveau (ou à l'ouverture de la minute si écart) ; deux niveaux dans la même minute → plus de trade ce jour ;
  stop = ouverture du jour ; 1 R = |entrée − ouverture| (code d'origine : robustesse/three_strats.py). Après une sortie,
  un nouveau franchissement d'un niveau (à partir de la minute suivante) est un nouveau candidat.
  V01 référence : sortie 16:00.
  V02 objectif 0,5 R : sortie totale à entrée ± 0,5 R, sinon stop ou 16:00.
  V03 50 % de la position à 0,5 R, le reste jusqu'à 16:00 avec le stop d'origine.
  V04 50 % à 0,5 R, le reste jusqu'à 16:00 avec son stop ramené au prix d'entrée dès la minute suivante.
Famille B — achat d'un repli dans une tendance haussière (Nasdaq + S&P).
  Tendance haussière (J−1). Ordre limite d'achat à ouverture − X × ATR, actif de 09:31 à 14:59 ; objectif = ouverture
  du jour ; stop = entrée − 1 ATR (1 R = 1 ATR) ; sortie 16:00 ; un seul trade par jour et par marché.
  V05 X = 0,5.   V06 X = 0,25.
Famille C — RSI2 en H1 dans le sens de la tendance journalière (Nasdaq + S&P).
  Barres H1 de la séance : 09:30, 10:30, ..., 14:30 (60 min) puis 15:30-16:00 ; RSI2 de Wilder et SMA5 sur la série
  continue des clôtures H1 des séances complètes. Signal à la clôture des barres 09:30 à 14:30 : achat si tendance
  haussière (J−1) et RSI2 < 10 ; vente si tendance baissière et RSI2 > 90 ; entrée à l'ouverture de la minute suivante ;
  stop = 1 ATR journalier (1 R) ; un trade à la fois ; nouveaux signaux possibles après la sortie.
  V07 sortie à la 1re clôture H1 au-delà de la SMA5 H1 (achat : > SMA5 ; vente : < SMA5), à l'ouverture de la minute
      suivante (clôture 16:00 si c'est la dernière barre), sinon stop ou 16:00.
  V08 objectif court fixe : entrée ± 0,25 ATR, sinon stop ou 16:00.
Famille D — excès d'ouverture joué vers la clôture de la veille, stop large (Nasdaq + S&P).
  Gap = ouverture 09:30 − clôture de la veille (la veille doit être une séance régulière ET le jour ouvré précédent).
  Si 0,1 ATR ≤ |gap| ≤ 0,5 ATR : position contre le gap à l'ouverture de 09:31 (pas de trade si le gap est déjà comblé à
  ce prix) ; objectif = clôture de la veille ; stop = entrée ∓ 1 ATR (1 R) ; sortie 16:00.
  V09 les deux sens.
  V10 seulement dans le sens de la tendance (achat d'un gap baissier en tendance haussière, vente d'un gap haussier en
      tendance baissière).
Famille E — RSI2 journalier de Connors (RSI2 < 10 et clôture > SMA200) transformé en trade court (Nasdaq + S&P).
  V11 signal sur la séance J−1 → achat à l'ouverture 09:30 de J, stop = entrée − 1 ATR (1 R), sortie 16:00.
  V12 signal à 15:55 le jour J → achat à 15:55, vente à l'ouverture 09:30 de la séance suivante (une nuit, ≤ 4 jours).
  V16 signal à 15:55 → achat à 15:55, sortie « bail-out » de Larry Williams : 1re ouverture 09:30 supérieure au prix
      d'entrée parmi les 5 séances complètes suivantes, sinon à l'ouverture de la 5e (swing ; trade écarté s'il
      chevauche un trou de données > 7 jours).
Famille F — autres idées documentées.
  V13 contrôle sans signal (le piège) : Nasdaq, achat à l'ouverture 09:30 chaque jour, objectif +0,25 ATR, stop −1 ATR
      (1 R = 1 ATR), sortie 16:00.
  V14 nuit après une séance baissière en tendance haussière (« overnight drift », Cliff-Cooper-Gulen 2008) :
      clôture 15:55 < clôture 15:55 de la séance régulière précédente (≤ 7 jours avant, sinon trou de données → pas de
      signal) et > SMA200 → achat à 15:55, vente à l'ouverture 09:30 suivante (Nasdaq + S&P).
  V15 retour au TWAP (VWAP sans volume, absent des données) : de 10:00 à 14:59, si clôture de la minute − TWAP du jour
      (moyenne des clôtures depuis 09:30) ≥ 0,5 ATR → vente, ≤ −0,5 ATR → achat, à l'ouverture de la minute suivante
      (pas de trade si le prix a déjà rejoint le TWAP) ; objectif = TWAP courant (celui de la minute précédente) ;
      stop = 1 ATR (1 R) ; sortie 16:00 ; un trade à la fois (Nasdaq + S&P).
Contrôles réservés (V17-V20), uniquement pour une variante validée : même règle avec entrée et sortie décalées d'une
minute (intraday), ou exécution à l'ouverture 09:30 suivante au lieu de 15:55 (nuit / swing).

MESURES par variante : taux de réussite (trades nets > 0), jours positifs %, €/jour ouvré, pire jour, pire série de jours
perdants, espérance nette et t (lib.evaluate), €/an, drawdown.
VÉRIFICATIONS : `python run.py --lookahead` (Nasdaq, données tronquées au 01/01/2019 → candidats antérieurs au
01/12/2018 identiques) ; trades recalculés à la main dans verif.py.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa: E402

IDX = ("NASDAQ100", "SP500")
ORDER = {"NASDAQ100": 0, "SP500": 1}
REGLES = {
    "V01": "Williams k=0,5 Nasdaq, stop = ouverture, sortie 16:00 (référence)",
    "V02": "Williams k=0,5 Nasdaq, objectif 0,5 R (sortie totale), sinon stop ou 16:00",
    "V03": "Williams k=0,5 Nasdaq, 50 % à 0,5 R, reste à 16:00 (stop d'origine)",
    "V04": "Williams k=0,5 Nasdaq, 50 % à 0,5 R, reste à 16:00 avec stop au prix d'entrée",
    "V05": "Repli : achat limite ouverture − 0,5 ATR si C > SMA200, objectif ouverture, stop 1 ATR, 16:00 (NQ+SP)",
    "V06": "Repli : achat limite ouverture − 0,25 ATR si C > SMA200, objectif ouverture, stop 1 ATR, 16:00 (NQ+SP)",
    "V07": "RSI2 H1 < 10 / > 90 dans le sens de la tendance J−1, sortie clôture H1 au-delà de la SMA5 H1, stop 1 ATR (NQ+SP)",
    "V08": "RSI2 H1 < 10 / > 90 dans le sens de la tendance J−1, objectif 0,25 ATR, stop 1 ATR, 16:00 (NQ+SP)",
    "V09": "Gap 0,1-0,5 ATR joué vers la clôture de la veille (2 sens), entrée 09:31, stop 1 ATR, 16:00 (NQ+SP)",
    "V10": "Gap 0,1-0,5 ATR joué vers la clôture de la veille, seulement dans le sens de la tendance, stop 1 ATR (NQ+SP)",
    "V11": "RSI2 journalier < 10 & C > SMA200 → achat ouverture J+1, stop 1 ATR, sortie 16:00 (NQ+SP)",
    "V12": "RSI2 journalier < 10 & C > SMA200 → achat 15:55, vente ouverture suivante (nuit) (NQ+SP)",
    "V13": "Contrôle sans signal : achat ouverture chaque jour, objectif 0,25 ATR, stop 1 ATR, 16:00 (Nasdaq)",
    "V14": "Nuit après séance baissière en tendance haussière : achat 15:55, vente ouverture suivante (NQ+SP)",
    "V15": "Retour au TWAP : écart ≥ 0,5 ATR (10:00-14:59), objectif TWAP, stop 1 ATR, 16:00 (NQ+SP)",
    "V16": "RSI2 journalier < 10 & C > SMA200 → achat 15:55, sortie 1re ouverture profitable (≤ 5 séances) (NQ+SP, swing)",
}
MARCHES = {"V01": ("NASDAQ100",), "V02": ("NASDAQ100",), "V03": ("NASDAQ100",), "V04": ("NASDAQ100",),
           "V13": ("NASDAQ100",)}
M = pd.Timedelta(minutes=1)


# ------------------------------------------------------------------------------------------------ indicateurs
def rsi_wilder(c, n=2):
    c = np.asarray(c, float)
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    ch = np.diff(c)
    up, dn = np.maximum(ch, 0), np.maximum(-ch, 0)
    au, ad = up[:n].mean(), dn[:n].mean()
    out[n] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    for i in range(n + 1, len(c)):
        au, ad = (au * (n - 1) + up[i - 1]) / n, (ad * (n - 1) + dn[i - 1]) / n
        out[i] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    return out


def bars(df, end_hm):
    """Barres journalières 09:30 → end_hm (exclu) des séances régulières + ATR14, SMA200, RSI2."""
    rth = df[(df["hm"] >= 570) & (df["hm"] < 960)]
    full = rth.groupby("day").agg(n=("hm", "size"), first=("hm", "first"), last=("hm", "last"))
    ok = full[(full.n >= 300) & (full["first"] <= 575) & (full["last"] >= 950) & (full.index.dayofweek < 5)].index
    s = rth[rth["hm"] < end_hm]
    g = s.groupby("day")
    b = pd.DataFrame({"O": g.open.first(), "H": g.high.max(), "L": g.low.min(), "C": g.close.last(),
                      "last": g.hm.last()}).loc[lambda x: x.index.isin(ok)]
    b = b[b["last"] >= min(950, end_hm - 6)]
    pc = b.C.shift()
    tr = pd.concat([b.H - b.L, (b.H - pc).abs(), (b.L - pc).abs()], axis=1).max(axis=1)
    b["atr"] = tr.rolling(14).mean()
    b["sma200"] = b.C.rolling(200).mean()
    b["rsi2"] = rsi_wilder(b.C.values)
    return b


class Prev:
    """Valeurs de la dernière séance régulière avant le jour J (≤ 4 jours calendaires)."""

    def __init__(self, b):
        self.days = b.index.values
        self.b = {c: b[c].values for c in ("C", "atr", "sma200", "rsi2")}

    def __call__(self, D):
        d64 = pd.Timestamp(D).to_datetime64()
        p = int(np.searchsorted(self.days, d64, side="left")) - 1
        if p < 0 or (d64 - self.days[p]) > np.timedelta64(4, "D"):
            return None
        r = {c: v[p] for c, v in self.b.items()}
        if not np.isfinite(r["atr"]) or r["atr"] <= 0:
            return None
        r["day"] = pd.Timestamp(self.days[p])
        return r


# ------------------------------------------------------------------------------------------------ exécution
def simulate(hm, O, H, L, C, k, d, entry, stop, tp=None, tp_now=False, part=None, be=False):
    """Position 1 lot ouverte à l'indice k. Retourne (gain brut en prix, indice de sortie, motif)."""
    last = len(hm) - 1
    rem, acc, st, tp_on = 1.0, 0.0, stop, tp is not None
    for j in range(k, last + 1):
        hit = (L[j] <= st) if d == 1 else (H[j] >= st)
        if hit:
            if j == k:
                px = st
            else:
                px = (min(O[j], st)) if d == 1 else (max(O[j], st))
            acc += rem * (px - entry) * d
            return acc, j, ("stop" if rem == 1.0 else ("stop_entree" if be else "stop_reste"))
        if tp_on and (j > k or tp_now):
            if (H[j] >= tp) if d == 1 else (L[j] <= tp):
                px = tp if j == k else ((max(O[j], tp)) if d == 1 else (min(O[j], tp)))
                if part is None:
                    acc += rem * (px - entry) * d
                    return acc, j, "objectif"
                acc += part * (px - entry) * d
                rem -= part
                tp_on = False
                if be:
                    st = entry          # appliqué à partir de la minute suivante
    acc += rem * (C[last] - entry) * d
    return acc, last, ("cloture" if rem == 1.0 else "objectif+cloture")


def row(inst, D, hm, k, x, d, entry, risk, gross, cost, how, **kw):
    r = {"instrument": inst, "day": D, "t_in": D + int(hm[k]) * M, "t_out": D + int(hm[x]) * M, "d": d,
         "entry": entry, "risque": risk, "gross_r": gross / risk, "cost_r": cost / risk, "sortie": how}
    r.update(kw)
    return r


# ------------------------------------------------------------------------------------------------ familles
def fam_williams(inst, S):
    out = {v: [] for v in ("V01", "V02", "V03", "V04")}
    prev_range = None
    for D in sorted(S):
        hm, O, H, L, C = S[D]
        if prev_range is not None:
            o0 = O[0]
            up, dn = o0 + 0.5 * prev_range, o0 - 0.5 * prev_range
            for v in out:
                start = 0
                while start < len(hm):
                    hu, hd = H[start:] >= up, L[start:] <= dn
                    hit = hu | hd
                    if not hit.any():
                        break
                    j = int(hit.argmax())
                    if hu[j] and hd[j]:
                        break
                    k, d = start + j, (1 if hu[j] else -1)
                    entry = max(O[k], up) if d == 1 else min(O[k], dn)
                    risk = (entry - o0) * d
                    if risk <= 0:
                        break
                    tp = None if v == "V01" else entry + d * 0.5 * risk
                    g, x, how = simulate(hm, O, H, L, C, k, d, entry, o0, tp, False,
                                         0.5 if v in ("V03", "V04") else None, v == "V04")
                    out[v].append(row(inst, D, hm, k, x, d, entry, risk, g, lib.COST[inst], how))
                    start = x + 1
        prev_range = H.max() - L.min()
    return out


def fam_repli(inst, S, P):
    out = {"V05": [], "V06": []}
    for D in sorted(S):
        p = P(D)
        if p is None or not np.isfinite(p["sma200"]) or not p["C"] > p["sma200"]:
            continue
        hm, O, H, L, C = S[D]
        atr = p["atr"]
        for v, X in (("V05", 0.5), ("V06", 0.25)):
            lvl = O[0] - X * atr
            w = np.where((hm >= 571) & (hm < 900) & (L <= lvl))[0]
            if not len(w):
                continue
            k = int(w[0])
            entry = min(O[k], lvl)
            g, x, how = simulate(hm, O, H, L, C, k, 1, entry, entry - atr, O[0], False)
            out[v].append(row(inst, D, hm, k, x, 1, entry, atr, g, lib.COST[inst], how))
    return out


H1B = (570, 630, 690, 750, 810, 870, 930, 960)


def fam_rsi_h1(inst, S, P):
    days = sorted(S)
    rec = []                                   # (jour, barre, clôture, indice de la dernière minute ou -1)
    for D in days:
        hm, O, H, L, C = S[D]
        for b in range(7):
            idx = np.where((hm >= H1B[b]) & (hm < H1B[b + 1]))[0]
            if len(idx):
                rec.append((D, b, C[idx[-1]], int(idx[-1])))
            else:
                rec.append((D, b, rec[-1][2] if rec else np.nan, -1))
    closes = np.array([r[2] for r in rec])
    rsi = rsi_wilder(closes)
    sma5 = pd.Series(closes).rolling(5).mean().values
    out = {"V07": [], "V08": []}
    for i0 in range(0, len(rec), 7):
        D = rec[i0][0]
        p = P(D)
        if p is None or not np.isfinite(p["sma200"]):
            continue
        trend = 1 if p["C"] > p["sma200"] else (-1 if p["C"] < p["sma200"] else 0)
        if trend == 0:
            continue
        hm, O, H, L, C = S[D]
        last, atr = len(hm) - 1, p["atr"]
        ends = [rec[i0 + b][3] for b in range(7)]
        for v in out:
            free = 0
            for b in range(6):
                e = ends[b]
                if e < 0 or e < free or e + 1 > last:
                    continue
                r = rsi[i0 + b]
                if not ((trend == 1 and r < 10) or (trend == -1 and r > 90)):
                    continue
                d, k = trend, e + 1
                entry = O[k]
                stop = entry - d * atr
                if v == "V08":
                    g, x, how = simulate(hm, O, H, L, C, k, d, entry, stop, entry + d * 0.25 * atr, True)
                else:
                    g = x = None
                    for j in range(k, last + 1):
                        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                            px = stop if j == k else (min(O[j], stop) if d == 1 else max(O[j], stop))
                            g, x, how = (px - entry) * d, j, "stop"
                            break
                        bb = [bi for bi in range(b + 1, 7) if ends[bi] == j]
                        if bb and j < last:
                            s5 = sma5[i0 + bb[0]]
                            if (C[j] > s5) if d == 1 else (C[j] < s5):
                                g, x, how = (O[j + 1] - entry) * d, j + 1, "sma5"
                                break
                    if g is None:
                        g, x, how = (C[last] - entry) * d, last, "cloture"
                out[v].append(row(inst, D, hm, k, x, d, entry, atr, g, lib.COST[inst], how, rsi2=float(r)))
                free = x
    return out


def fam_gap(inst, S, P):
    out = {"V09": [], "V10": []}
    for D in sorted(S):
        p = P(D)
        if p is None or p["day"] != D - pd.offsets.BDay(1):
            continue
        hm, O, H, L, C = S[D]
        prev_c, atr = p["C"], p["atr"]
        gap = O[0] - prev_c
        if not (0.1 * atr <= abs(gap) <= 0.5 * atr):
            continue
        d = -1 if gap > 0 else 1
        kk = np.where(hm == 571)[0]
        if not len(kk):
            continue
        k = int(kk[0])
        entry = O[k]
        if (d == 1 and entry >= prev_c) or (d == -1 and entry <= prev_c):
            continue
        g, x, how = simulate(hm, O, H, L, C, k, d, entry, entry - d * atr, prev_c, True)
        r = row(inst, D, hm, k, x, d, entry, atr, g, lib.COST[inst], how, gap_atr=float(gap / atr))
        out["V09"].append(r)
        trend = 1 if (np.isfinite(p["sma200"]) and prev_c > p["sma200"]) else (
            -1 if (np.isfinite(p["sma200"]) and prev_c < p["sma200"]) else 0)
        if d == trend:
            out["V10"].append(dict(r))
    return out


def fam_jour(inst, S, P):
    """V11 (RSI2 J−1 → intraday J), V13 (contrôle), V15 (TWAP)."""
    out = {"V11": [], "V13": [], "V15": []}
    for D in sorted(S):
        p = P(D)
        if p is None:
            continue
        hm, O, H, L, C = S[D]
        last, atr = len(hm) - 1, p["atr"]
        if np.isfinite(p["sma200"]) and np.isfinite(p["rsi2"]) and p["rsi2"] < 10 and p["C"] > p["sma200"]:
            g, x, how = simulate(hm, O, H, L, C, 0, 1, O[0], O[0] - atr, None, True)
            out["V11"].append(row(inst, D, hm, 0, x, 1, O[0], atr, g, lib.COST[inst], how))
        if inst == "NASDAQ100":
            g, x, how = simulate(hm, O, H, L, C, 0, 1, O[0], O[0] - atr, O[0] + 0.25 * atr, True)
            out["V13"].append(row(inst, D, hm, 0, x, 1, O[0], atr, g, lib.COST[inst], how))
        tw = np.cumsum(C) / np.arange(1, len(C) + 1)
        dev = C - tw
        sig = np.where((hm >= 600) & (hm < 900) & (np.abs(dev) >= 0.5 * atr))[0]
        free = 0
        for k0 in sig:
            if k0 < free or k0 + 1 > last:
                continue
            d, k = (-1 if dev[k0] > 0 else 1), int(k0) + 1
            entry, stop = O[k], O[k] - (-1 if dev[k0] > 0 else 1) * atr
            if (d == 1 and entry >= tw[k - 1]) or (d == -1 and entry <= tw[k - 1]):
                continue
            g = x = None
            for j in range(k, last + 1):
                if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                    px = stop if j == k else (min(O[j], stop) if d == 1 else max(O[j], stop))
                    g, x, how = (px - entry) * d, j, "stop"
                    break
                tgt = tw[j - 1]
                if (H[j] >= tgt) if d == 1 else (L[j] <= tgt):
                    px = tgt if j == k else (max(O[j], tgt) if d == 1 else min(O[j], tgt))
                    g, x, how = (px - entry) * d, j, "objectif"
                    break
            if g is None:
                g, x, how = (C[last] - entry) * d, last, "cloture"
            out["V15"].append(row(inst, D, hm, k, x, d, entry, atr, g, lib.COST[inst], how))
            free = x
    return out


def fam_nuit(inst, S, b55):
    """V12, V14 (une nuit) et V16 (swing bail-out), signal et exécution à 15:55."""
    out = {"V12": [], "V14": [], "V16": []}
    sdays = np.array(sorted(S), dtype="datetime64[ns]")
    swap = lib.SWAP[inst][0]
    days = b55.index
    C, atr, sma, rsi = b55.C.values, b55.atr.values, b55.sma200.values, b55.rsi2.values

    def nxt(D, n):
        i = int(np.searchsorted(sdays, pd.Timestamp(D).to_datetime64(), side="right"))
        return [pd.Timestamp(x) for x in sdays[i:i + n]]

    def trade(D, i, exit_day, px):
        nights = (exit_day - D).days
        R = atr[i]
        return {"instrument": inst, "day": D, "t_in": D + 955 * M, "t_out": exit_day + 570 * M, "d": 1,
                "entry": C[i], "risque": R, "gross_r": (px - C[i]) / R,
                "cost_r": (lib.COST[inst] + C[i] * swap * nights / 360) / R, "nuits": nights, "sortie": "ouverture"}

    busy_until = None
    for i, D in enumerate(days):
        if not (np.isfinite(atr[i]) and np.isfinite(sma[i]) and atr[i] > 0) or i == 0:
            continue
        rsi_sig = np.isfinite(rsi[i]) and rsi[i] < 10 and C[i] > sma[i]
        down_sig = C[i] < C[i - 1] and C[i] > sma[i] and (D - days[i - 1]).days <= 7
        n1 = nxt(D, 1)
        if n1 and (n1[0] - D).days <= 4:
            o1 = S[n1[0]][1][0]
            if rsi_sig:
                out["V12"].append(trade(D, i, n1[0], o1))
            if down_sig:
                out["V14"].append(trade(D, i, n1[0], o1))
        if rsi_sig and (busy_until is None or D >= busy_until):
            n5 = nxt(D, 5)
            if len(n5) == 5 and all((b - a).days <= 7 for a, b in zip([D] + n5[:-1], n5)):
                ex = next((x for x in n5 if S[x][1][0] > C[i]), n5[-1])
                out["V16"].append(trade(D, i, ex, S[ex][1][0]))
                busy_until = ex
    return out


def candidates(inst, df):
    S = lib.sessions_ny(df)
    bf, b55 = bars(df, 960), bars(df, 956)
    P = Prev(bf)
    out = {}
    if inst == "NASDAQ100":
        out.update(fam_williams(inst, S))
    for f in (fam_repli, fam_rsi_h1, fam_gap, fam_jour):
        out.update(f(inst, S, P))
    out.update(fam_nuit(inst, S, b55))
    return {v: rows for v, rows in out.items() if inst in MARCHES.get(v, IDX)}


# ------------------------------------------------------------------------------------------------ évaluation
def taken(rows):
    t = pd.DataFrame(rows)
    t["ordre"] = t["instrument"].map(ORDER)
    t = t.sort_values(["day", "t_in", "ordre"], kind="mergesort").reset_index(drop=True)
    return t, lib.regle_anto(t)


def summary(v, t_all, k):
    k = k.sort_values(["day", "t_in"])
    r = lib.evaluate(k, f"{v} {REGLES[v][:38]}")
    k11 = k[k["day"] >= lib.START]
    net = k11["gross_r"] - k11["cost_r"]
    r["jour"] = lib.stats_jour(k)
    r["taux_reussite"] = round(float((net > 0).mean() * 100), 1)
    r["regles"] = REGLES[v]
    r["candidats"] = int((t_all["day"] >= lib.START).sum())
    r["jours_avec_2e_trade"] = int(k11.groupby("day").size().gt(1).sum())
    r["cout_median_r"] = round(float(k11["cost_r"].median()), 4)
    r["sorties_pct"] = {s: round(float(x) * 100, 1) for s, x in k11["sortie"].value_counts(normalize=True).items()}
    r["par_marche"] = {m: {"trades": int(len(g)), "e_r": round(float((g.gross_r - g.cost_r).mean()), 4),
                           "taux_reussite": round(float(((g.gross_r - g.cost_r) > 0).mean() * 100), 1)}
                       for m, g in k11.groupby("instrument")}
    return r


def main():
    t0 = time.time()
    allrows = {}
    for inst in IDX:                                           # un marché à la fois
        df = lib.load(inst)
        c = candidates(inst, df)
        del df
        for v, rows in c.items():
            allrows.setdefault(v, []).extend(rows)
        print(inst, {v: len(r) for v, r in c.items()}, f"{time.time() - t0:.0f}s", flush=True)
    res, keep = {}, []
    for v in sorted(allrows):
        t_all, k = taken(allrows[v])
        r = summary(v, t_all, k)
        res[v] = r
        k = k.assign(variante=v)
        keep.append(k)
        print(lib.line(r))
        print("    ", lib.line_jour(r["jour"]), f"| réussite {r['taux_reussite']}% | pire jour {r['jour']['pire_jour_eur']} €")
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)
    pd.concat(keep).drop(columns=["ordre"]).to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6f")
    print(f"terminé en {time.time() - t0:.0f}s")


def lookahead():
    """Contrôle : candidats calculés sur données tronquées au 01/01/2019 = candidats complets avant le 01/12/2018."""
    inst = "NASDAQ100"
    df = lib.load(inst)
    full = candidates(inst, df)
    trunc = candidates(inst, df[df["day"] < "2019-01-01"].reset_index(drop=True))
    del df
    cols = ["day", "t_in", "t_out", "gross_r", "cost_r"]
    for v in sorted(full):
        a = pd.DataFrame(full[v])
        b = pd.DataFrame(trunc[v])
        a = a[a["day"] < "2018-12-01"][cols].reset_index(drop=True)
        b = b[b["day"] < "2018-12-01"][cols].reset_index(drop=True)
        same = len(a) == len(b) and (a[["day", "t_in", "t_out"]] == b[["day", "t_in", "t_out"]]).all().all() and \
            np.allclose(a[["gross_r", "cost_r"]].values, b[["gross_r", "cost_r"]].values)
        print(v, "candidats", len(a), "look-ahead OK" if same else "DIFFÉRENCE")


if __name__ == "__main__":
    lookahead() if "--lookahead" in sys.argv else main()
