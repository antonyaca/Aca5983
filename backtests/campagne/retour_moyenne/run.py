"""Campagne — famille RETOUR À LA MOYENNE (intraday et swing 1-5 jours). Règles fixées AVANT tout calcul (17/10/2026).

Budget : 17 variantes déclarées ci-dessous (≤ 25). Aucune ne sera ajoutée ni modifiée après lecture des résultats.
Critère : lib.evaluate (PROTOCOLE.md). 1 R = 100 €. Période 2011-2026 (2010 = préchauffage des indicateurs).

Littérature : IBS (Pagonidis 2014, « The IBS effect » ; Lento & Gradojevic 2023, arXiv 2306.12434), RSI 2 et
« double seven » (Connors & Alvarez, « Short Term Trading Strategies That Work », 2008), séries de baisses
consécutives et bandes de Bollinger (mêmes sources, retour à la moyenne court terme sur indices actions),
comblement de gap et sur-réaction d'ouverture (littérature mitigée ; Gao-Han-Li-Zhou 2018 montrent plutôt un
MOMENTUM intraday, donc la variante « fade de la 1re heure » est un test contradictoire assumé).

DONNÉES ET BARRES JOURNALIÈRES
- Indices (séance principale, heure locale) : NASDAQ100 et SP500 09:30-16:00 New York ; FTSE100 08:00-16:30 Londres ;
  NIKKEI225 09:00-15:00 Tokyo. Forex et métaux : journée 17:00 → 17:00 New York (clôture forex standard).
- Barre de signal du jour t = minutes de [ouverture, clôture − 5 min) : O, H, L, C (C = clôture de la dernière minute
  avant « clôture − 5 min »). Jour valable si ≥ 80 % des minutes présentes, 1re minute ≤ ouverture + 5 min, lun.-ven.
- Exécution swing : signal calculé sur C_t ; entrée/sortie au prix suivant = ouverture de la minute « clôture − 5 min »
  (si absente : C_t, compté et signalé). Métaux : réouverture 18:00 NY → 1re minute tolérée jusqu'à 18:05. Pas de look-ahead : tout est connu à l'instant de l'ordre.
- ATR14 = moyenne simple des 14 derniers True Range journaliers (barre t incluse pour le swing, car complète à
  l'entrée ; barre t−1 pour l'intraday).
- Swing sans stop : 1 R = ATR14. Coûts = lib.COST / R + swap (lib.SWAP, nuits calendaires, base 360, nominal = prix
  d'entrée). Une seule position par marché et par variante ; pas de ré-entrée le jour de la sortie.
- Coûts ×2 des jours d'annonce : non appliqués (pas de calendrier macro fiable avant 2020 ; les exécutions se font à
  l'ouverture/clôture, pas à l'heure des annonces). Le critère « frais ×2 » couvre ce point de façon conservatrice.

INDICES = NASDAQ100, SP500, FTSE100, NIKKEI225 ; FXM = XAUUSD, XAGUSD, EURUSD, GBPUSD, USDJPY, AUDUSD ; FX4 = 4 paires.
IBS = (C − L) / (H − L). RSI2 = RSI de Wilder 2 périodes. SMA = moyenne simple des clôtures C.

VARIANTES SWING (barres journalières)
 V01 IBS bas, 4 indices : achat si IBS < 0,2 ; sortie à la clôture suivante.
 V02 IBS bas sortie swing, 4 indices : achat si IBS < 0,2 ; sortie au 1er C_j > H_{j−1}, ou après 5 séances.
 V03 IBS symétrique, FXM : achat si IBS < 0,2, vente si IBS > 0,8 ; sortie à la clôture suivante.
 V04 RSI2 Connors 16 ans, NASDAQ100 + SP500 : achat si RSI2 < 10 et C > SMA200 ; sortie dès C > SMA5 (pas de limite).
 V05 RSI2 Connors, 4 indices : mêmes règles que V04.
 V06 RSI2 symétrique, 10 marchés : achat RSI2 < 10 et C > SMA200, sortie C > SMA5 ; vente RSI2 > 90 et C < SMA200,
     sortie C < SMA5.
 V07 Double seven (Connors), 4 indices : achat si C > SMA200 et C = plus bas des 7 dernières clôtures (t incluse) ;
     sortie quand C = plus haut des 7 dernières clôtures.
 V08 3 baisses consécutives, 4 indices : achat si C_t < C_{t−1} < C_{t−2} < C_{t−3} ; sortie 1re clôture en hausse
     (C_j > C_{j−1}) ou après 5 séances.
 V09 = V08 avec filtre C > SMA200.
 V10 Bollinger bas, 4 indices : achat si C < SMA20 − 2 σ20 ; sortie dès C > SMA20 ou après 5 séances.
 V11 Bollinger symétrique, FXM : achat sous SMA20 − 2 σ20 (sortie C > SMA20), vente au-dessus de SMA20 + 2 σ20
     (sortie C < SMA20) ; 5 séances maximum.
 V12 Panier indices déclaré à l'avance : union des trades V02 + V05 + V07 (chacun 1 R).

VARIANTES INTRADAY (minutes, séance locale, sortie au plus tard à la dernière minute de la séance)
 V13 Comblement de gap, 4 indices, deux sens : gap = ouverture − clôture de la séance précédente ;
     si 0,1 ATR ≤ |gap| ≤ 1 ATR (ATR veille) : position contraire au gap à la clôture de la 1re minute ;
     objectif = clôture de la veille ; stop = entrée ∓ |gap| (1 R = |gap|) ; stop prioritaire ; sinon sortie en clôture.
 V14 = V13 gaps baissiers seulement (achats).
 V15 Fade de la 1re heure, 4 indices : m = clôture de la 60e minute − ouverture ; si |m| ≥ 0,5 ATR (veille) :
     position contraire à l'ouverture de la 61e minute, sortie en clôture de séance, sans stop, 1 R = ATR.
 V16 Écart à la moyenne intraday, NASDAQ100 + SP500 : pas de volume dans les données → TWAP (moyenne cumulée des
     clôtures M1 depuis l'ouverture) en lieu de VWAP. Entre ouverture + 60 min et clôture − 60 min, 1re minute où
     |C − TWAP| ≥ 0,5 ATR : position contraire à l'ouverture de la minute suivante ; objectif = TWAP au signal ;
     stop = 0,5 ATR (1 R) ; un trade par jour ; sortie en clôture.
 V17 Fade du range asiatique, FX4 (heure de Londres) : range 00:00-07:00 (≥ 380 minutes), W = largeur ;
     de 07:00 à 12:00, vente limite à H + 0,25 W ou achat limite à L − 0,25 W (1er niveau touché ; deux dans la même
     minute → pas de trade) ; stop 0,5 W au-delà (1 R) ; objectif = milieu du range ; sortie 16:00.
     Remplissage au niveau ; si le stop est touché dans la minute d'entrée → perte (conservateur).

TROUS DE DONNÉES (règle de traitement ajoutée après constat des trous, avant lecture de résultats corrigés ; uniforme,
non liée à une variante) : un trade swing dont la détention chevauche un intervalle > 7 jours calendaires entre deux
séances valables est écarté (non valorisable) ; pas de trade de gap si la séance précédente date de > 7 jours.

CONTRÔLES : look-ahead (indicateurs recalculés sur données tronquées identiques), trades/an, distribution de R,
exemples de trades imprimés pour vérification manuelle.
"""
import gc
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib import load, evaluate, line, COST, SWAP, MARKETS  # noqa: E402

INDICES = {"NASDAQ100": ("America/New_York", 570, 960), "SP500": ("America/New_York", 570, 960),
           "FTSE100": ("Europe/London", 480, 990), "NIKKEI225": ("Asia/Tokyo", 540, 900)}
FXM = ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
FX4 = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
NOTES = []
MAXGAP = 7          # jours calendaires max entre deux séances valables pendant un trade (trous de données)
SKIPPED = {}


# ---------------------------------------------------------------- barres journalières
def daily_bars(df, start, end, open_tol=5):
    cut = end - 5
    s = df[(df["hm"] >= start) & (df["hm"] < cut)]
    g = s.groupby("day")
    b = pd.DataFrame({"O": g["open"].first(), "H": g["high"].max(), "L": g["low"].min(), "C": g["close"].last(),
                      "n": g["open"].size(), "h0": g["hm"].first()})
    px = df[(df["hm"] >= cut) & (df["hm"] < cut + 5)].groupby("day")["open"].first()
    b["px"] = px.reindex(b.index)
    b = b[(b["n"] >= 0.8 * (cut - start)) & (b["h0"] <= start + open_tol) & (b.index.dayofweek < 5)].copy()
    miss = int(b["px"].isna().sum())
    b["px"] = b["px"].fillna(b["C"])
    pc = b["C"].shift(1)
    tr = pd.concat([b["H"] - b["L"], (b["H"] - pc).abs(), (b["L"] - pc).abs()], axis=1).max(axis=1)
    b["atr"] = tr.rolling(14).mean()
    return b, miss


def indicators(b):
    c = b["C"]
    x = pd.DataFrame(index=b.index)
    rng = (b["H"] - b["L"]).replace(0, np.nan)
    x["ibs"] = (c - b["L"]) / rng
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=0.5, adjust=False).mean()
    x["rsi2"] = 100 - 100 / (1 + up / dn)
    x["sma200"], x["sma5"], x["sma20"] = c.rolling(200).mean(), c.rolling(5).mean(), c.rolling(20).mean()
    x["sd20"] = c.rolling(20).std(ddof=0)
    x["min7"], x["max7"] = c.rolling(7).min(), c.rolling(7).max()
    x["down3"] = (c < c.shift(1)) & (c.shift(1) < c.shift(2)) & (c.shift(2) < c.shift(3))
    x["up1"] = c > c.shift(1)
    x["gt_prevH"] = c > b["H"].shift(1)
    return x


def swing(inst, b, longs, shorts, exl, exs, maxd, var):
    """longs/shorts/exl/exs : tableaux booléens alignés sur b. maxd = nb max de séances (None = illimité)."""
    px, atr, days = b["px"].values, b["atr"].values, b.index
    n, rows, i = len(b), [], 0
    sl, ss = SWAP[inst]
    while i < n:
        d = 1 if longs[i] else (-1 if shorts[i] else 0)
        if d == 0 or not np.isfinite(atr[i]) or atr[i] <= 0:
            i += 1
            continue
        j, ex = i + 1, None
        while j < n:
            if (exl[j] if d == 1 else exs[j]) or (maxd is not None and j - i >= maxd):
                ex = j
                break
            j += 1
        if ex is None:
            break
        if (np.diff(days[i:ex + 1].values).astype("timedelta64[D]").astype(int) > MAXGAP).any():
            SKIPPED[var] = SKIPPED.get(var, 0) + 1      # trou de données pendant la détention → trade non valorisable
            i = ex + 1
            continue
        R = atr[i]
        nights = (days[ex] - days[i]).days
        swap = px[i] * (sl if d == 1 else ss) * nights / 360 / R
        rows.append({"variante": var, "instrument": inst, "day": days[i], "exit_day": days[ex], "d": d,
                     "entry": px[i], "exit": px[ex], "R": R, "nuits": nights,
                     "gross_r": (px[ex] - px[i]) * d / R, "cost_r": COST[inst] / R + swap})
        i = ex + 1
    return rows


def swing_variants(inst, b, is_index):
    x = indicators(b)
    F = np.zeros(len(b), bool)
    c = b["C"]
    rows = []
    ibs_lo, ibs_hi = (x["ibs"] < 0.2).values, (x["ibs"] > 0.8).values
    rsi_l = ((x["rsi2"] < 10) & (c > x["sma200"])).values
    rsi_s = ((x["rsi2"] > 90) & (c < x["sma200"])).values
    ex_l5, ex_s5 = (c > x["sma5"]).values, (c < x["sma5"]).values
    bb_l, bb_s = (c < x["sma20"] - 2 * x["sd20"]).values, (c > x["sma20"] + 2 * x["sd20"]).values
    ex_l20, ex_s20 = (c > x["sma20"]).values, (c < x["sma20"]).values
    if is_index:
        rows += swing(inst, b, ibs_lo, F, F, F, 1, "V01")
        rows += swing(inst, b, ibs_lo, F, x["gt_prevH"].values, F, 5, "V02")
        if inst in ("NASDAQ100", "SP500"):
            rows += swing(inst, b, rsi_l, F, ex_l5, F, None, "V04")
        rows += swing(inst, b, rsi_l, F, ex_l5, F, None, "V05")
        ds_l = ((c > x["sma200"]) & (c <= x["min7"])).values
        rows += swing(inst, b, ds_l, F, (c >= x["max7"]).values, F, None, "V07")
        rows += swing(inst, b, x["down3"].values, F, x["up1"].values, F, 5, "V08")
        rows += swing(inst, b, (x["down3"] & (c > x["sma200"])).values, F, x["up1"].values, F, 5, "V09")
        rows += swing(inst, b, bb_l, F, ex_l20, F, 5, "V10")
    else:
        rows += swing(inst, b, ibs_lo, ibs_hi, F, F, 1, "V03")
        rows += swing(inst, b, bb_l, bb_s, ex_l20, ex_s20, 5, "V11")
    rows += swing(inst, b, rsi_l, rsi_s, ex_l5, ex_s5, None, "V06")
    return rows


# ---------------------------------------------------------------- intraday
def day_slices(df, start, end):
    s = df[(df["hm"] >= start) & (df["hm"] < end)]
    days = s["day"].values
    cuts = np.flatnonzero(days[1:] != days[:-1]) + 1
    bounds = np.r_[0, cuts, len(s)]
    arr = {k: s[k].values for k in ("hm", "open", "high", "low", "close")}
    out = {}
    for a, z in zip(bounds[:-1], bounds[1:]):
        out[pd.Timestamp(days[a])] = tuple(arr[k][a:z] for k in ("hm", "open", "high", "low", "close"))
    return out


def walk(O, H, L, C, k0, d, stop, target):
    """Parcourt les minutes k0.. ; stop prioritaire ; gap au-delà du stop → ouverture. Retourne (prix, motif)."""
    if k0 >= len(O):
        return None, None
    o, h, l = O[k0:], H[k0:], L[k0:]
    hs = (l <= stop) if d == 1 else (h >= stop)
    ht = np.zeros(len(o), bool) if target is None else ((h >= target) if d == 1 else (l <= target))
    js = int(hs.argmax()) if hs.any() else len(o)
    jt = int(ht.argmax()) if ht.any() else len(o)
    if js <= jt and js < len(o):
        oo = o[js]
        gapped = (oo < stop) if d == 1 else (oo > stop)
        return (oo if gapped else stop), "SL"
    if jt < len(o):
        oo = o[jt]
        gapped = (oo > target) if d == 1 else (oo < target)
        return (oo if gapped else target), "TP"
    return C[-1], "Cloture"


def intraday_index(inst, df, b, start, end):
    S = day_slices(df, start, end)
    atr_prev = b["atr"].shift(1)
    vdays = list(b.index)
    rows = []
    cost = COST[inst]
    for t in range(1, len(vdays)):
        day, pday = vdays[t], vdays[t - 1]
        if day not in S or pday not in S or (day - pday).days > MAXGAP:
            continue
        A = atr_prev.iloc[t]
        if not np.isfinite(A) or A <= 0:
            continue
        hm, O, H, L, C = S[day]
        if hm[0] != start or len(hm) < 0.8 * (end - start):
            continue
        prevC = S[pday][4][-1]
        # V13 / V14 gap
        g = O[0] - prevC
        if 0.1 * A <= abs(g) <= A:
            d = -1 if g > 0 else 1
            entry = C[0]
            stop = entry - d * abs(g)
            if (prevC - entry) * d > 0:
                ex, why = walk(O, H, L, C, 1, d, stop, prevC)
                if ex is not None:
                    r = {"instrument": inst, "day": day, "d": d, "entry": entry, "exit": ex, "R": abs(g), "motif": why,
                         "gross_r": (ex - entry) * d / abs(g), "cost_r": cost / abs(g)}
                    rows.append(dict(r, variante="V13"))
                    if d == 1:
                        rows.append(dict(r, variante="V14"))
        # V15 1re heure
        k60 = np.flatnonzero(hm < start + 60)
        k61 = np.flatnonzero(hm >= start + 60)
        if len(k60) and len(k61):
            m = C[k60[-1]] - O[0]
            if abs(m) >= 0.5 * A:
                d = -1 if m > 0 else 1
                entry, ex = O[k61[0]], C[-1]
                rows.append({"variante": "V15", "instrument": inst, "day": day, "d": d, "entry": entry, "exit": ex,
                             "R": A, "motif": "Cloture", "gross_r": (ex - entry) * d / A, "cost_r": cost / A})
        # V16 TWAP
        if inst in ("NASDAQ100", "SP500"):
            twap = np.cumsum(C) / np.arange(1, len(C) + 1)
            dev = C - twap
            win = (hm >= start + 60) & (hm < end - 60) & (np.abs(dev) >= 0.5 * A)
            if win.any():
                k = int(win.argmax())
                if k + 1 < len(O):
                    d = -1 if dev[k] > 0 else 1
                    entry, tgt = O[k + 1], twap[k]
                    stop = entry - d * 0.5 * A
                    if (tgt - entry) * d > 0:
                        ex, why = walk(O, H, L, C, k + 1, d, stop, tgt)
                        rows.append({"variante": "V16", "instrument": inst, "day": day, "d": d, "entry": entry,
                                     "exit": ex, "R": 0.5 * A, "motif": why, "gross_r": (ex - entry) * d / (0.5 * A),
                                     "cost_r": cost / (0.5 * A)})
    return rows


def asian_fade(inst, df):
    S = day_slices(df, 0, 960)
    rows = []
    for day, (hm, O, H, L, C) in S.items():
        if day.dayofweek >= 5:
            continue
        rg = hm < 420
        if rg.sum() < 380:
            continue
        hi, lo = H[rg].max(), L[rg].min()
        W = hi - lo
        if W <= 0:
            continue
        idx = np.flatnonzero((hm >= 420) & (hm < 720))
        if len(idx) == 0:
            continue
        sl_lvl, bl_lvl = hi + 0.25 * W, lo - 0.25 * W
        us, ub = H[idx] >= sl_lvl, L[idx] <= bl_lvl
        hit = us | ub
        if not hit.any():
            continue
        j = int(hit.argmax())
        if us[j] and ub[j]:
            continue
        k = idx[j]
        d = -1 if us[j] else 1
        entry = sl_lvl if d == -1 else bl_lvl
        stop = entry - d * 0.5 * W
        tgt = (hi + lo) / 2
        if (L[k] <= stop) if d == 1 else (H[k] >= stop):
            ex, why = stop, "SL"
        else:
            ex, why = walk(O, H, L, C, k + 1, d, stop, tgt)
            if ex is None:
                continue
        rows.append({"variante": "V17", "instrument": inst, "day": day, "d": d, "entry": entry, "exit": ex,
                     "R": 0.5 * W, "motif": why, "gross_r": (ex - entry) * d / (0.5 * W), "cost_r": COST[inst] / (0.5 * W)})
    return rows


def fx_daily_frame(inst):
    df = load(inst, "America/New_York")
    loc = df["time"].dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)
    df["day"] = loc.dt.normalize()
    df["hm"] = (loc.dt.hour * 60 + loc.dt.minute).astype(np.int16)
    return df


# ---------------------------------------------------------------- contrôles
def lookahead_check(b, label):
    x_full = indicators(b)
    cut = b.index[len(b) // 2]
    x_cut = indicators(b[b.index <= cut])
    a, z = x_full.loc[x_cut.index], x_cut
    ok = True
    for col in z.columns:
        u, v = a[col].values.astype(float), z[col].values.astype(float)
        if not np.allclose(np.nan_to_num(u, nan=-9), np.nan_to_num(v, nan=-9), rtol=1e-9, atol=1e-12):
            ok = False
            NOTES.append(f"LOOK-AHEAD suspect {label} {col}")
    return ok


def main():
    rows = []
    for inst in MARKETS:
        if inst in INDICES:
            tz, start, end = INDICES[inst]
            df = load(inst, tz)
            b, miss = daily_bars(df, start, end)
            rows += swing_variants(inst, b, True)
            rows += intraday_index(inst, df, b, start, end)
        else:
            df = fx_daily_frame(inst)
            b, miss = daily_bars(df, 0, 1440, 65 if inst in ("XAUUSD", "XAGUSD") else 5)
            rows += swing_variants(inst, b, False)
            if inst in FX4:
                del df
                gc.collect()
                df = load(inst, "Europe/London")
                rows += asian_fade(inst, df)
        la = lookahead_check(b, inst)
        gp = pd.Series(b.index[1:] - b.index[:-1], index=b.index[1:])
        gp = gp[gp > pd.Timedelta(days=MAXGAP)]
        NOTES.append(f"{inst}: trous > {MAXGAP} j : " + ", ".join(f"{(d - g).date()}→{d.date()}" for d, g in gp.items()))
        NOTES.append(f"{inst}: {len(b)} séances valides {b.index[0].date()}→{b.index[-1].date()}, prix d'exécution "
                     f"manquant {miss}, look-ahead OK={la}, ATR médian {b['atr'].median():.5g}")
        print(NOTES[-1], flush=True)
        del df, b
        gc.collect()
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6g")
    return t


REGLES = {
    "V01": "IBS<0,2 achat clôture, sortie clôture suivante — 4 indices",
    "V02": "IBS<0,2 achat, sortie 1re C>H veille ou 5 séances — 4 indices",
    "V03": "IBS<0,2 achat / >0,8 vente, sortie clôture suivante — or, argent, 4 paires forex",
    "V04": "RSI2<10 & C>SMA200 achat, sortie C>SMA5 — Nasdaq + S&P sur 2011-2026",
    "V05": "RSI2<10 & C>SMA200 achat, sortie C>SMA5 — 4 indices",
    "V06": "RSI2 symétrique (10/90, filtre SMA200, sortie SMA5) — 10 marchés",
    "V07": "Double seven Connors (C>SMA200, plus bas 7 j → plus haut 7 j) — 4 indices",
    "V08": "3 baisses consécutives achat, sortie 1re hausse ou 5 séances — 4 indices",
    "V09": "3 baisses consécutives + C>SMA200, sortie 1re hausse ou 5 séances — 4 indices",
    "V10": "Bollinger(20,2) bas achat, sortie C>SMA20 ou 5 séances — 4 indices",
    "V11": "Bollinger(20,2) symétrique, sortie SMA20 ou 5 séances — or, argent, 4 paires",
    "V12": "Panier indices déclaré : V02 + V05 + V07",
    "V13": "Comblement gap 0,1-1 ATR deux sens, objectif clôture veille, stop |gap| — 4 indices intraday",
    "V14": "Comblement gap baissier seulement (achats) — 4 indices intraday",
    "V15": "Fade 1re heure si |mouvement| ≥ 0,5 ATR, sortie clôture, R=ATR — 4 indices intraday",
    "V16": "Écart au TWAP ≥ 0,5 ATR (10:30-15:00), objectif TWAP, stop 0,5 ATR — Nasdaq + S&P intraday",
    "V17": "Fade range asiatique ±0,25 W, stop 0,5 W, objectif milieu, sortie 16:00 Londres — 4 paires forex",
}


def report(t):
    res = []
    for v, txt in REGLES.items():
        g = t[t["variante"].isin(["V02", "V05", "V07"])] if v == "V12" else t[t["variante"] == v]
        r = evaluate(g.copy(), f"{v} {txt[:38]}")
        r["regles"] = txt
        g2 = g[g["day"] >= "2011-01-01"]
        r["par_instrument"] = {i: {"n": int(len(x)), "e_r_net": round(float((x.gross_r - x.cost_r).mean()), 4)}
                               for i, x in g2.groupby("instrument")}
        r["trades_par_an_moyen"] = round(len(g2) / g2["day"].dt.year.nunique(), 1) if len(g2) else 0
        r["cout_median_r"] = round(float(g2["cost_r"].median()), 4) if len(g2) else None
        res.append(r)
        print(line(r), flush=True)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    NOTES.append(f"Trades swing écartés car chevauchant un trou de données : {SKIPPED}")
    with open(os.path.join(HERE, "controles.txt"), "w") as f:
        f.write("\n".join(NOTES) + "\n")
    return res


if __name__ == "__main__":
    report(main())
