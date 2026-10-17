"""Campagne oct. 2026 — famille CASSURE / MOMENTUM / SUIVI DE TENDANCE. Règles écrites AVANT tout calcul.

Cadre : PROTOCOLE.md (100 € par R, coûts lib.COST aller-retour, swap lib.SWAP par nuit calendaire base 360 sur le nominal,
découverte 2011-2018 / validation 2019-2026, critère lib.evaluate). Budget : 22 variantes déclarées ci-dessous (3 non
utilisées sur les 25 autorisées). Aucun paramètre ne sera modifié après lecture des résultats.
Exclusions volontaires : Williams / ORB / pré-market sur S&P 500 déjà invalidés sur 2011-2026 (hors_echantillon), les trois
stratégies Nasdaq déjà validées ne sont pas refaites.

Séances (heure locale) : SP500 / NASDAQ100 New York 09:30-16:00 ; FTSE100 Londres 08:00-16:30 ; NIKKEI225 Tokyo 09:00-15:00 ;
XAUUSD (Williams) New York 08:20-13:30 (séance COMEX) ; forex (Williams) Londres 08:00-16:30.
Une séance est retenue si sa 1re minute existe et si ≥ 90 % des minutes sont présentes (lib.sessions_ny) ; exception
NIKKEI225 : ≥ 50 % (cotations CFD clairsemées avant 2019, une minute absente = pas de tick).
ATR14 « séance » = moyenne des 14 true ranges des séances précédentes (jour J exclu). Séances séparées de > 4 jours : pas de trade.
Exécution M1 : entrée au niveau (ou à l'ouverture de la minute si gap au-delà) ; stop prioritaire ; stop touché dans la minute
d'entrée → perte ; gap au-delà du stop → sortie à l'ouverture de la minute ; deux niveaux dans la même minute → pas de trade.
Stratégies sans stop : 1 R = ATR14 à l'entrée.

A. MOMENTUM INTRADAY (Gao, Han, Li, Zhou 2018 « Market intraday momentum », JFE ; Baltussen, Da, Lammers, Martens 2021 JFE)
   Entrée à l'ouverture de la minute « clôture − 30 min », sortie au dernier cours de la séance. Sens = signe du signal. 1 R = ATR14.
   A1 GHLZ SP500 : signal = cours à ouverture+30 min (clôture de la minute op+29) / clôture de la séance précédente − 1.
   A2 GHLZ NASDAQ100     A3 GHLZ FTSE100     A4 GHLZ NIKKEI225
   A5 BDLM SP500 : signal = cours à clôture−30 min (clôture de la minute précédente) / clôture de la séance précédente − 1.
   A6 BDLM NASDAQ100
   A7 GHLZ SP500 filtre volatilité : seulement si ATR14/prix ≥ médiane de ce ratio sur les 252 séances précédentes.
B. WILLIAMS k = 0,5 transposé (ouverture ± 0,5 × amplitude de la séance précédente, 1er niveau touché, stop = ouverture,
   sortie à la clôture, deux sens) : B1 FTSE100, B2 NIKKEI225, B3 XAUUSD, B4 GBPUSD.
   B5 FTSE100 + filtre SMA200 : achats seulement si clôture veille > moyenne des 200 clôtures précédentes, ventes sinon.
C. ORB 30 min achats seuls (range des 30 premières minutes, achat au franchissement du haut jusqu'à 1 h avant la clôture,
   annulé si le bas casse d'abord, stop = bas du range, sortie clôture) : C1 FTSE100, C2 NIKKEI225.
D. OPENING DRIVE : si |cours op+30 − ouverture| ≥ 0,3 ATR14, entrée à l'ouverture de la minute op+30 dans ce sens,
   stop = extrême opposé des 30 premières minutes, sortie clôture. D1 SP500, D2 FTSE100.
E. CASSURE DU RANGE ASIATIQUE À L'OUVERTURE DE LONDRES (heure de Londres) : range 00:00-07:00 ; 1er franchissement 07:00-12:00 ;
   deux sens ; stop = bord opposé ; sortie 16:00 (dernier cours < 16:00). E1 GBPUSD, E2 EURUSD, E3 XAUUSD.
F. TIME-SERIES MOMENTUM mensuel (Moskowitz, Ooi, Pedersen 2012). Barres journalières « 17:00 New York ».
   À la dernière barre de chaque mois : signe du rendement sur 12 mois (clôture fin de mois / clôture fin de mois −12 − 1).
   Entrée à l'ouverture de la barre suivante, sortie à l'ouverture de la première barre du mois suivant (= entrée suivante).
   1 R = ATR14 journalier à l'entrée ; un trade par marché et par mois ; swap sur les nuits calendaires.
   F1 les 10 marchés MARKETS ; F2 forex + métaux seulement (6 marchés).
G. EXPANSION DE VOLATILITÉ multi-jours (barres 17:00 NY) : si amplitude du jour J > 2 × ATR14 (J exclu) et clôture dans le quart
   haut (bas) de l'amplitude → achat (vente) à l'ouverture de J+1 ; stop = plus bas (haut) de J ; sortie à la clôture de J+5 ;
   gap d'ouverture au-delà du stop → sortie à l'ouverture ; une position à la fois par marché ; swap compris.
   G1 portefeuille SP500, NASDAQ100, FTSE100, NIKKEI225, XAUUSD.
Coûts « jours d'annonce macro ×2 » : non appliqués (pas de calendrier 2011-2019 dans le dépôt) ; le test frais ×2 du critère couvre ce cas.
"""
import gc
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib import load, sessions_ny, evaluate, line, COST, SWAP, MARKETS  # noqa: E402

TZ = {"SP500": "America/New_York", "NASDAQ100": "America/New_York", "FTSE100": "Europe/London", "NIKKEI225": "Asia/Tokyo"}
SESS = {"SP500": (570, 960), "NASDAQ100": (570, 960), "FTSE100": (480, 990), "NIKKEI225": (540, 900)}


# ---------------------------------------------------------------- outils
def exit_price(hm, O, H, L, C, k, d, stop, close_m=10 ** 6):
    if (L[k] <= stop) if d == 1 else (H[k] >= stop):
        return stop
    last = k
    for j in range(k + 1, len(hm)):
        if hm[j] >= close_m:
            break
        last = j
        if (L[j] <= stop) if d == 1 else (H[j] >= stop):
            return O[j] if ((O[j] < stop) if d == 1 else (O[j] > stop)) else stop
    return C[last]


def first_cross(hm, H, L, lo_m, hi_m, up_lvl, dn_lvl):
    idx = np.where((hm >= lo_m) & (hm < hi_m))[0]
    if len(idx) == 0:
        return None
    up = H[idx] > up_lvl if up_lvl is not None else np.zeros(len(idx), bool)
    dn = L[idx] < dn_lvl if dn_lvl is not None else np.zeros(len(idx), bool)
    hit = up | dn
    if not hit.any():
        return None
    j = int(hit.argmax())
    if up[j] and dn[j]:
        return None
    return idx[j], (1 if up[j] else -1)


def session_table(inst, tz, op, cl, frac=0.9):
    df = load(inst, tz)
    S = sessions_ny(df, op, cl, min_frac=frac)
    del df
    gc.collect()
    keys = sorted(S)
    Od = np.array([S[k][1][0] for k in keys]); Hd = np.array([S[k][2].max() for k in keys])
    Ld = np.array([S[k][3].min() for k in keys]); Cd = np.array([S[k][4][-1] for k in keys])
    pc = np.r_[np.nan, Cd[:-1]]
    tr = np.nanmax(np.vstack([Hd - Ld, np.abs(Hd - pc), np.abs(Ld - pc)]), axis=0)
    atr = pd.Series(tr).rolling(14).mean().shift(1).values
    return S, keys, Od, Hd, Ld, Cd, atr


def frame(rows, inst, cols=("variante", "day", "d", "entry", "exit", "risque", "swap")):
    t = pd.DataFrame(rows, columns=list(cols))
    t["instrument"] = inst
    t["gross_r"] = (t["exit"] - t["entry"]) * t["d"] / t["risque"]
    t["cost_r"] = (COST[inst] + t["swap"]) / t["risque"]
    return t


# ---------------------------------------------------------------- A, B, C, D (indices / séance principale)
def run_intraday(inst, want):
    """want : ensemble de codes de variantes à produire pour cet instrument."""
    tz = TZ.get(inst)
    op, cl = SESS.get(inst, (None, None))
    if inst == "XAUUSD":
        tz, op, cl = "America/New_York", 500, 810
    if inst == "GBPUSD":
        tz, op, cl = "Europe/London", 480, 990
    S, keys, Od, Hd, Ld, Cd, atr = session_table(inst, tz, op, cl, 0.5 if inst == "NIKKEI225" else 0.9)
    ratio = atr / np.r_[np.nan, Cd[:-1]]
    ratio_med = pd.Series(ratio).rolling(252, min_periods=252).median().shift(1).values
    sma200 = pd.Series(Cd).rolling(200).mean().shift(1).values  # moyenne des 200 clôtures avant J
    rng = Hd - Ld
    rows = []
    for i in range(1, len(keys)):
        day = keys[i]
        if (day - keys[i - 1]).days > 4 or np.isnan(atr[i]):
            continue
        hm, O, H, L, C = S[day]
        pclose = Cd[i - 1]
        a = atr[i]
        # --- A : momentum intraday (entrée cl-30)
        ke = np.where(hm == cl - 30)[0]
        if len(ke) and ke[0] > 0:
            ke = int(ke[0])
            entry, ex = O[ke], C[-1]
            k30 = np.where(hm < op + 30)[0]
            r1 = C[k30[-1]] / pclose - 1
            rb = C[ke - 1] / pclose - 1
            if r1 != 0 and "GHLZ" in want:
                rows.append(("GHLZ", day, int(np.sign(r1)), entry, ex, a, 0.0))
                if "GHLZ_vol" in want and not np.isnan(ratio_med[i]) and ratio[i] >= ratio_med[i]:
                    rows.append(("GHLZ_vol", day, int(np.sign(r1)), entry, ex, a, 0.0))
            if rb != 0 and "BDLM" in want:
                rows.append(("BDLM", day, int(np.sign(rb)), entry, ex, a, 0.0))
        # --- B : Williams k=0.5
        if "WIL" in want and rng[i - 1] > 0:
            up, dn = O[0] + 0.5 * rng[i - 1], O[0] - 0.5 * rng[i - 1]
            hu, hd = H >= up, L <= dn
            hit = hu | hd
            if hit.any():
                j = int(hit.argmax())
                if not (hu[j] and hd[j]):
                    d = 1 if hu[j] else -1
                    entry = max(O[j], up) if d == 1 else min(O[j], dn)
                    risk = (entry - O[0]) * d
                    if risk > 0:
                        px = exit_price(hm, O, H, L, C, j, d, O[0])
                        rows.append(("WIL", day, d, entry, px, risk, 0.0))
                        if "WIL_sma" in want and not np.isnan(sma200[i]):
                            if (d == 1 and pclose > sma200[i]) or (d == -1 and pclose < sma200[i]):
                                rows.append(("WIL_sma", day, d, entry, px, risk, 0.0))
        # --- C : ORB 30 min achats seuls
        rg = hm < op + 30
        if "ORB" in want and rg.sum() >= (15 if inst == "NIKKEI225" else 27):
            rh, rl = H[rg].max(), L[rg].min()
            r = first_cross(hm, H, L, op + 30, cl - 60 + 1, rh, rl)
            if r and r[1] == 1:
                k = r[0]
                entry = max(O[k], rh)
                if entry - rl > 0:
                    rows.append(("ORB", day, 1, entry, exit_price(hm, O, H, L, C, k, 1, rl), entry - rl, 0.0))
        # --- D : opening drive
        if "DRIVE" in want:
            k = np.where(hm == op + 30)[0]
            if len(k):
                k = int(k[0])
                move = C[k - 1] - O[0]
                if abs(move) >= 0.3 * a:
                    d = 1 if move > 0 else -1
                    entry = O[k]
                    stop = L[:k].min() if d == 1 else H[:k].max()
                    risk = (entry - stop) * d
                    if risk > 0:
                        rows.append(("DRIVE", day, d, entry, exit_price(hm, O, H, L, C, k, d, stop), risk, 0.0))
    del S
    gc.collect()
    return frame(rows, inst)


# ---------------------------------------------------------------- E : range asiatique / ouverture de Londres
def run_asian(inst):
    df = load(inst, "Europe/London")
    S = sessions_ny(df, 0, 960)
    del df
    gc.collect()
    rows = []
    for day in sorted(S):
        hm, O, H, L, C = S[day]
        rg = hm < 420
        if rg.sum() < 0.9 * 420 or not (hm >= 420).any():
            continue
        rh, rl = H[rg].max(), L[rg].min()
        r = first_cross(hm, H, L, 420, 720, rh, rl)
        if not r:
            continue
        k, d = r
        entry = max(O[k], rh) if d == 1 else min(O[k], rl)
        stop = rl if d == 1 else rh
        risk = (entry - stop) * d
        if risk > 0:
            rows.append(("ASIA", day, d, entry, exit_price(hm, O, H, L, C, k, d, stop), risk, 0.0))
    del S
    return frame(rows, inst)


# ---------------------------------------------------------------- barres journalières 17:00 NY
def daily_bars(inst):
    df = load(inst, "America/New_York")
    loc = df["time"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    key = (loc + pd.Timedelta(hours=7)).dt.normalize()
    g = df.groupby(key.values)
    D = pd.DataFrame({"O": g["open"].first(), "H": g["high"].max(), "L": g["low"].min(), "C": g["close"].last(),
                      "n": g.size()})
    del df, loc, key, g
    gc.collect()
    D = D[(D.index.dayofweek < 5) & (D["n"] >= 300)].copy()
    pc = D["C"].shift(1)
    tr = pd.concat([D["H"] - D["L"], (D["H"] - pc).abs(), (D["L"] - pc).abs()], axis=1).max(axis=1)
    D["atr"] = tr.rolling(14).mean().shift(1)   # connu avant la barre
    return D


def swap_cost(inst, d, price, nights):
    rate = SWAP[inst][0] if d == 1 else SWAP[inst][1]
    return price * rate * nights / 360.0


def run_tsmom(inst, D):
    D = D.copy()
    D["ym"] = D.index.to_period("M")
    last = D.groupby("ym").tail(1)            # dernière barre de chaque mois
    pos = {ts: i for i, ts in enumerate(D.index)}
    rows = []
    me = list(last.index)
    for m in range(12, len(me) - 1):
        t0 = me[m]
        sig = D.at[t0, "C"] / D.at[me[m - 12], "C"] - 1
        if sig == 0 or np.isnan(sig):
            continue
        # garde-fou : 12 mois calendaires réels entre les deux points
        if not (330 <= (t0 - me[m - 12]).days <= 400):
            continue
        i_in, i_out = pos[t0] + 1, pos[me[m + 1]] + 1
        if i_out >= len(D):
            continue
        d = 1 if sig > 0 else -1
        entry, ex = D["O"].iloc[i_in], D["O"].iloc[i_out]
        a = D["atr"].iloc[i_in]
        if np.isnan(a) or a <= 0:
            continue
        dd_in, dd_out = D.index[i_in], D.index[i_out]
        nights = (dd_out - dd_in).days
        rows.append(("TSMOM12", dd_in, d, entry, ex, a, swap_cost(inst, d, entry, nights)))
    return frame(rows, inst)


def run_volexp(inst, D):
    O, H, L, C, A = (D[c].values for c in ("O", "H", "L", "C", "atr"))
    idx = D.index
    rows = []
    busy_until = -1
    for i in range(14, len(D) - 6):
        if i <= busy_until or np.isnan(A[i]):
            continue
        rg = H[i] - L[i]
        if rg <= 2 * A[i]:
            continue
        q = (C[i] - L[i]) / rg
        if q >= 0.75:
            d, stop = 1, L[i]
        elif q <= 0.25:
            d, stop = -1, H[i]
        else:
            continue
        if (idx[i + 1] - idx[i]).days > 4:
            continue
        entry = O[i + 1]
        risk = (entry - stop) * d
        if risk <= 0:
            continue
        ex, j_ex = None, i + 5
        for j in range(i + 1, i + 6):
            if j > i + 1 and ((O[j] <= stop) if d == 1 else (O[j] >= stop)):
                ex, j_ex = O[j], j
                break
            if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                ex, j_ex = stop, j
                break
        if ex is None:
            ex = C[i + 5]
        nights = (idx[j_ex] - idx[i + 1]).days + (0 if ex == O[j_ex] and j_ex > i + 1 else 1)
        rows.append(("VOLEXP", idx[i + 1], d, entry, ex, risk, swap_cost(inst, d, entry, nights)))
        busy_until = j_ex
    return frame(rows, inst)


# ---------------------------------------------------------------- orchestration
VARIANTS = [
    ("A1", "GHLZ", ["SP500"], "Momentum intraday GHLZ : signe(rendement veille 16:00→10:00), entrée 15:30 sortie 16:00, 1R=ATR14 — SP500"),
    ("A2", "GHLZ", ["NASDAQ100"], "Momentum intraday GHLZ (idem A1) — NASDAQ100"),
    ("A3", "GHLZ", ["FTSE100"], "Momentum intraday GHLZ : veille 16:30→08:30, entrée 16:00 sortie 16:30 — FTSE100"),
    ("A4", "GHLZ", ["NIKKEI225"], "Momentum intraday GHLZ : veille 15:00→09:30, entrée 14:30 sortie 15:00 — NIKKEI225"),
    ("A5", "BDLM", ["SP500"], "Momentum intraday Baltussen et al. : signe(rendement veille 16:00→15:30), entrée 15:30 sortie 16:00 — SP500"),
    ("A6", "BDLM", ["NASDAQ100"], "Momentum intraday Baltussen et al. (idem A5) — NASDAQ100"),
    ("A7", "GHLZ_vol", ["SP500"], "GHLZ SP500 seulement si ATR14/prix ≥ médiane 252 séances"),
    ("B1", "WIL", ["FTSE100"], "Williams k=0,5, stop ouverture, sortie clôture — FTSE100 08:00-16:30"),
    ("B2", "WIL", ["NIKKEI225"], "Williams k=0,5 — NIKKEI225 09:00-15:00"),
    ("B3", "WIL", ["XAUUSD"], "Williams k=0,5 — XAUUSD séance COMEX 08:20-13:30 NY"),
    ("B4", "WIL", ["GBPUSD"], "Williams k=0,5 — GBPUSD séance Londres 08:00-16:30"),
    ("B5", "WIL_sma", ["FTSE100"], "Williams k=0,5 FTSE100 dans le sens de la SMA200 (clôture veille vs SMA200)"),
    ("C1", "ORB", ["FTSE100"], "ORB 30 min achats seuls, stop bas du range, sortie clôture — FTSE100"),
    ("C2", "ORB", ["NIKKEI225"], "ORB 30 min achats seuls — NIKKEI225"),
    ("D1", "DRIVE", ["SP500"], "Opening drive : |op+30 − ouverture| ≥ 0,3 ATR14 → entrée op+30 dans le sens, stop extrême opposé, sortie clôture — SP500"),
    ("D2", "DRIVE", ["FTSE100"], "Opening drive (idem D1) — FTSE100"),
    ("E1", "ASIA", ["GBPUSD"], "Cassure range asiatique 00:00-07:00 Londres, fenêtre 07:00-12:00, stop bord opposé, sortie 16:00 — GBPUSD"),
    ("E2", "ASIA", ["EURUSD"], "Cassure range asiatique (idem E1) — EURUSD"),
    ("E3", "ASIA", ["XAUUSD"], "Cassure range asiatique (idem E1) — XAUUSD"),
    ("F1", "TSMOM12", list(MARKETS), "Time-series momentum 12 mois, rebalancement mensuel, 1R=ATR14, swap inclus — 10 marchés"),
    ("F2", "TSMOM12", ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD"], "TSMOM 12 mois — forex + métaux (6 marchés)"),
    ("G1", "VOLEXP", ["SP500", "NASDAQ100", "FTSE100", "NIKKEI225", "XAUUSD"], "Expansion de volatilité (amplitude > 2 ATR14, clôture quart extrême), entrée J+1, stop extrême de J, sortie clôture J+5 — 4 indices + or"),
]
assert len(VARIANTS) <= 25


def main():
    # 1) besoins par instrument
    intr, asia, daily = {}, set(), {}
    for code, kind, insts, _ in VARIANTS:
        for inst in insts:
            if kind in ("GHLZ", "GHLZ_vol", "BDLM", "WIL", "WIL_sma", "ORB", "DRIVE"):
                intr.setdefault(inst, set()).add(kind)
                if kind == "GHLZ_vol":
                    intr[inst].add("GHLZ")
                if kind == "WIL_sma":
                    intr[inst].add("WIL")
            elif kind == "ASIA":
                asia.add(inst)
            else:
                daily.setdefault(inst, set()).add(kind)
    trades = []
    for inst, want in intr.items():
        print("intraday", inst, sorted(want), flush=True)
        trades.append(run_intraday(inst, want))
    for inst in sorted(asia):
        print("asie", inst, flush=True)
        trades.append(run_asian(inst))
    for inst, want in daily.items():
        print("journalier", inst, sorted(want), flush=True)
        D = daily_bars(inst)
        if "TSMOM12" in want:
            trades.append(run_tsmom(inst, D))
        if "VOLEXP" in want:
            trades.append(run_volexp(inst, D))
        del D
        gc.collect()
    T = pd.concat(trades, ignore_index=True)
    T.to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for code, kind, insts, regles in VARIANTS:
        t = T[(T["variante"] == kind) & (T["instrument"].isin(insts))].copy()
        r = evaluate(t, f"{code} {kind} {'+'.join(insts) if len(insts) < 4 else str(len(insts)) + ' marchés'}")
        r["regles"] = regles
        r["code"] = code
        tt = t[t["day"] >= "2011-01-01"]
        r["trades_par_an"] = round(len(tt) / max(1, tt["day"].dt.year.nunique()), 1)
        r["cout_median_r"] = float(tt["cost_r"].median()) if len(tt) else None
        r["brut_e_r"] = r["brut"]["e_r"]
        res.append(r)
        print(line(r), f"| {r['trades_par_an']}/an coût~{r['cout_median_r']:.3f}R", flush=True)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
