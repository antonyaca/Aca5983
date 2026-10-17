"""« Scalping PullBack Tool R1.1 » (JustUncleL) — backtest. Règles fixées le 17/10/2026 AVANT tout calcul.

Signal (copie fidèle du Pine, réglages par défaut, Heikin Ashi activé) :
- Bougies Heikin Ashi : haC = (O+H+L+C)/4 ; haO = (haO[1]+haC[1])/2 ; haH = max(H, haO, haC) ; haL = min(L, haO, haC).
- PAC : pacC = EMA34(haC), pacU = EMA34(haH), pacL = EMA34(haL). fastEMA = EMA89(haC), mediumEMA = EMA200(haC).
- Tendance = +1 si fast > medium et pacL > medium ; −1 si fast < medium et pacU < medium ; sinon 0.
- pacExitU = haO < pacU et haC > pacU et (barres depuis haC < pacC) ≤ 3 ; pacExitL symétrique.
- Buy = tendance +1 et pacExitU ; Sell = tendance −1 et pacExitL.
- État TradeDirection du script : passe à 1 sur Buy (si 0), revient à 0 quand haC < pacC (idem vente).
  Signal = passage de 0 à ±1 (exactement l'alerte BUY/SELL du script).
Exécution (ajoutée, car le script n'en donne pas) :
- Entrée à l'ouverture RÉELLE de la bougie suivante. Stop = pacL (achat) / pacU (vente) de la bougie du signal ;
  pas de trade si l'entrée est déjà au-delà du stop.
- Sorties testées : A = objectif 1 R ; B = objectif 2 R ; C = sortie quand le script repasse à 0 (haC recroise pacC),
  à l'ouverture de la bougie suivante. Stop prioritaire dans la bougie ; gap au-delà → ouverture.
- Fenêtres : indices = séance principale (entrées jusqu'à 30 min avant la clôture, sortie forcée à la clôture) :
  Nasdaq/S&P 09:30-16:00 NY, FTSE 08:00-16:30 Londres, Nikkei 09:00-15:00 Tokyo. Forex et métaux : entrées
  03:00-15:30 NY (Londres + New York), sortie forcée à 16:55 NY. Un trade à la fois par marché et par réglage.
- Indicateurs calculés en continu sur toutes les bougies disponibles. Unités : M5 et M15.
Coûts lib.COST aller-retour (pas de swap : aucune position gardée la nuit). 100 € par R. Critère : lib.evaluate.
6 réglages (2 unités × 3 sorties) × 10 marchés, jugés par marché ET en portefeuille.
"""
import json, os, sys
import numpy as np, pandas as pd
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import lib  # noqa

SESS = {"NASDAQ100": ("America/New_York", 570, 960), "SP500": ("America/New_York", 570, 960),
        "FTSE100": ("Europe/London", 480, 990), "NIKKEI225": ("Asia/Tokyo", 540, 900)}
FXM = ("America/New_York", 180, 1015)   # entrées 03:00-15:30 (1015-75+... voir ENTRY_END), sortie 16:55


def ema(x, n):
    a = 2 / (n + 1)
    y = lfilter([a], [1, -(1 - a)], x, zi=[x[0] * (1 - a)])[0]
    return y


def bars(inst, tf):
    df = lib.load(inst)
    s = df.set_index("time")[["open", "high", "low", "close"]]
    b = s.resample(f"{tf}min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return b


def signals(b):
    O, H, L, C = (b[c].values for c in ("open", "high", "low", "close"))
    haC = (O + H + L + C) / 4
    # haO_t = 0.5 haO_{t-1} + 0.5 haC_{t-1}
    haO = np.empty_like(haC); haO[0] = (O[0] + C[0]) / 2
    haO[1:] = lfilter([0.5], [1, -0.5], haC[:-1], zi=[0.5 * haO[0]])[0]
    haH, haL = np.maximum.reduce([H, haO, haC]), np.minimum.reduce([L, haO, haC])
    pacC, pacU, pacL = ema(haC, 34), ema(haH, 34), ema(haL, 34)
    fast, med = ema(haC, 89), ema(haC, 200)
    trend = np.where((fast > med) & (pacL > med), 1, np.where((fast < med) & (pacU < med), -1, 0))
    below, above = haC < pacC, haC > pacC
    # barres depuis la dernière clôture HA sous (au-dessus de) pacC
    idx = np.arange(len(haC))
    last_b = pd.Series(np.where(below, idx, np.nan)).ffill().values
    last_a = pd.Series(np.where(above, idx, np.nan)).ffill().values
    exU = (haO < pacU) & (haC > pacU) & ((idx - last_b) <= 3)
    exL = (haO > pacL) & (haC < pacL) & ((idx - last_a) <= 3)
    buy, sell = (trend == 1) & exU, (trend == -1) & exL
    td = np.zeros(len(haC), np.int8); st = 0
    for i in range(len(haC)):
        if st == 1 and below[i]: st = 0
        elif st == -1 and above[i]: st = 0
        elif st == 0 and buy[i]: st = 1
        elif st == 0 and sell[i]: st = -1
        td[i] = st
    prev = np.r_[0, td[:-1]]
    sig = np.where((prev == 0) & (td != 0), td, 0)
    return sig, td, pacU, pacL


def simulate(inst, b, tf):
    tz, op, cl = SESS.get(inst, FXM)
    loc = b.index.tz_convert(tz)
    hm = (loc.hour * 60 + loc.minute).values
    day = loc.tz_localize(None).normalize().values
    O, H, L, C = (b[c].values for c in ("open", "high", "low", "close"))
    sig, td, pacU, pacL = signals(b)
    entry_end = cl - (30 if inst in SESS else 85)          # indices : 30 min avant clôture ; FX/métaux : 15:30 NY
    exit_t = cl if inst in SESS else 1015                  # 16:55 NY pour FX/métaux
    rows = {k: [] for k in ("A 1R", "B 2R", "C sortie PAC")}
    n = len(O)
    for ex in rows:
        i, busy_until = 0, -1
        cand = np.flatnonzero(sig != 0)
        for i in cand:
            e = i + 1
            if e >= n or e <= busy_until:
                continue
            if day[e] != day[i] or not (op <= hm[e] < entry_end) or hm[e] < op:
                continue
            d = int(sig[i]); stop = pacL[i] if d == 1 else pacU[i]
            entry = O[e]; risk = (entry - stop) * d
            if risk <= 0:
                continue
            tp = entry + d * risk * (1 if ex == "A 1R" else 2) if ex != "C sortie PAC" else None
            px, j = None, e
            while j < n:
                if day[j] != day[e] or hm[j] >= exit_t:
                    px = O[j] if day[j] == day[e] else C[j - 1]; break
                if (L[j] <= stop) if d == 1 else (H[j] >= stop):
                    px = O[j] if (j > e and ((O[j] < stop) if d == 1 else (O[j] > stop))) else stop; break
                if tp is not None and ((H[j] >= tp) if d == 1 else (L[j] <= tp)):
                    px = O[j] if (j > e and ((O[j] > tp) if d == 1 else (O[j] < tp))) else tp; break
                if ex == "C sortie PAC" and td[j] == 0 and j + 1 < n:
                    j += 1
                    px = O[j] if day[j] == day[e] and hm[j] < exit_t else C[j - 1]; break
                j += 1
            if px is None:
                break
            busy_until = j
            rows[ex].append({"instrument": inst, "tf": f"M{tf}", "sortie": ex, "day": pd.Timestamp(day[e]), "d": d,
                             "entry": entry, "exit": px, "risque": risk,
                             "gross_r": (px - entry) * d / risk, "cost_r": lib.COST[inst] / risk})
    return [r for v in rows.values() for r in v]


def main():
    allrows = []
    for inst in lib.MARKETS:
        for tf in (5, 15):
            b = bars(inst, tf)
            allrows += simulate(inst, b, tf)
        print(inst, "ok", flush=True)
    t = pd.DataFrame(allrows)
    t.to_csv(os.path.join(HERE, "trades.csv.gz"), index=False, float_format="%.6f")
    res = []
    for (tf, ex), g in t.groupby(["tf", "sortie"]):
        r = lib.evaluate(g, f"PORTEFEUILLE {tf} {ex}"); r["regles"] = f"{tf} {ex} 10 marchés"; res.append(r); print(lib.line(r))
        for inst, gi in g.groupby("instrument"):
            r = lib.evaluate(gi, f"  {inst} {tf} {ex}"); r["regles"] = f"{tf} {ex} {inst}"
            r["risque_median_cout_r"] = float(gi["cost_r"].median()); res.append(r); print(lib.line(r), f"coût médian {gi['cost_r'].median():.2f} R")
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
