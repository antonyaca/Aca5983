"""Micro-scalping +2/−1 filtré par RSI / Stochastique en M1 (demande d'Anto, 22/10/2026). Règles fixées AVANT calcul.

Marchés et frais aller-retour « bas coût » :
- EURUSD compte raw spread + commission : 0,8 pip (0,1 pip de spread + ≈ 7 $/lot de commission ≈ 0,7 pip).
- Nasdaq en micro-future MNQ : 0,75 pt (≈ 1 tick d'écart + commission ≈ 1,2 $ ÷ 2 $/pt).
Indicateurs M1 : RSI 14 (Wilder) et Stochastique %K 14 lissé 3. Signaux à la clôture de la minute, entrée à l'ouverture
de la suivante, à l'ENTRÉE dans la zone (la minute précédente n'y était pas) :
  RSI : < 30 → achat, > 70 → vente ; STOCH : < 20 → achat, > 80 → vente ; LES 2 : les deux conditions ensemble.
Trade : stop = u, objectif = 2 u (le « +2 / −1 ») ; u EURUSD ∈ {3, 5, 10 pips} ; u Nasdaq ∈ {10, 20 pts}. Stop prioritaire ;
sortie au plus tard 120 minutes après. Un trade à la fois. Toutes heures ; résultats par session (heure de Paris) :
Asie 00-08, Londres 08-14, New York 14-22, soir 22-24.
Jugement : lib.evaluate sur chaque combinaison ; la meilleure de 2011-2018 est rejugée sur 2019-2026.
"""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); sys.path.insert(0, C)
import lib  # noqa
COSTS = {"EURUSD": 0.00008, "NASDAQ100": 0.75}
US = {"EURUSD": (0.0003, 0.0005, 0.0010), "NASDAQ100": (10, 20)}


def session(h):
    return "Asie" if h < 8 else ("Londres" if h < 14 else ("New York" if h < 22 else "soir"))


rows = []
for inst in ("EURUSD", "NASDAQ100"):
    df = lib.load(inst, "Europe/Paris")
    T = df["time"].values.astype("datetime64[m]").astype(np.int64)
    O, Hh, L, Cc = (df[c].values for c in ("open", "high", "low", "close")); hm = df["hm"].values; day = df["day"].values
    cs = pd.Series(Cc); d = cs.diff()
    rsi = (100 - 100 / (1 + d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean() / (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean())).values
    ll, hh = pd.Series(L).rolling(14).min(), pd.Series(Hh).rolling(14).max()
    k = (100 * (cs - ll) / (hh - ll)).rolling(3).mean().values
    sig = {"RSI": np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0)),
           "STOCH": np.where(k < 20, 1, np.where(k > 80, -1, 0))}
    sig["LES 2"] = np.where((sig["RSI"] == sig["STOCH"]), sig["RSI"], 0)
    for name, s in sig.items():
        new = np.flatnonzero((s != 0) & (np.r_[0, s[:-1]] != s))
        new = new[(new + 121 < len(T))]
        for u in US[inst]:
            busy = -1
            for i in new:
                e = i + 1
                if e <= busy or T[e] - T[i] != 1 or T[e + 119] - T[e] > 150:
                    continue
                dd = int(s[i]); entry = O[e]; stop = entry - dd * u; tp = entry + dd * 2 * u
                hs, ls = Hh[e:e + 120], L[e:e + 120]
                sh = (ls <= stop) if dd == 1 else (hs >= stop); th = (hs >= tp) if dd == 1 else (ls <= tp)
                ks = np.argmax(sh) if sh.any() else 999; kt = np.argmax(th) if th.any() else 999
                if ks == 999 and kt == 999:
                    g, x = (Cc[e + 119] - entry) * dd / u, e + 119
                elif ks <= kt:
                    g, x = -1.0, e + ks
                else:
                    g, x = 2.0, e + kt
                busy = x
                rows.append((inst, name, u, session(int(hm[e] // 60)), day[e], g, COSTS[inst] / u))
    print(inst, "ok", flush=True)
t = pd.DataFrame(rows, columns=["instrument", "filtre", "u", "session", "day", "gross_r", "cost_r"])
t["day"] = pd.to_datetime(t["day"])
t.to_csv(os.path.join(H, "scalp_rsi_stoch.csv.gz"), index=False, float_format="%.5f")
t["net"] = t.gross_r - t.cost_r
tab = t.groupby(["instrument", "filtre", "u", "session"]).agg(trades=("net", "size"), brut=("gross_r", "mean"), net=("net", "mean"),
                                                              reussite=("gross_r", lambda x: (x > 0).mean() * 100))
print(tab.round(3).to_string())
disc = t[t.day < lib.SPLIT].groupby(["instrument", "filtre", "u", "session"]).net.agg(["mean", "size"])
disc = disc[disc["size"] >= 300]
best = disc["mean"].idxmax()
g = t[(t.instrument == best[0]) & (t.filtre == best[1]) & (t.u == best[2]) & (t.session == best[3])]
r = lib.evaluate(g, f"MEILLEURE 2011-2018 : {best}")
print("\n", lib.line(r))
print(f"Combinaisons positives après frais en 2011-2018 : {(disc['mean'] > 0).sum()}/{len(disc)}")
