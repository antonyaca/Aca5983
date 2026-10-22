"""Scalping M5 « −10 € / +10 € » (objectif = stop, 1:1) filtré RSI / Stochastique (Anto, 22/10/2026). Règles AVANT calcul.
Bougies M5 ; RSI 14 (Wilder) et Stochastique %K 14 lissé 3 sur M5 ; entrée à l'ouverture de la bougie M5 suivante quand
l'indicateur ENTRE en zone (RSI < 30 / > 70 ; Stoch < 20 / > 80 ; « LES 2 » = les deux) → achat en survente,
vente en surachat. Stop = objectif = u ; u Nasdaq ∈ {20, 40 pts} ; u EURUSD ∈ {10, 20 pips}. Stop prioritaire dans la
bougie ; sortie au plus tard 24 bougies (2 h) après. Un trade à la fois.
Frais bas : MNQ 0,75 pt ; EURUSD raw spread + commission 0,8 pip. Sessions (Paris) : Asie 00-08, Londres 08-14,
New York 14-22 ; 22 h-minuit EXCLU (bascule forex : spread réel non visible dans les données, cf. scalp_rsi_stoch).
Jugement lib.evaluate ; meilleure combinaison de 2011-2018 rejugée sur 2019-2026.
"""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); sys.path.insert(0, C)
import lib  # noqa
COSTS = {"EURUSD": 0.00008, "NASDAQ100": 0.75}
US = {"EURUSD": (0.0010, 0.0020), "NASDAQ100": (20, 40)}
rows = []
for inst in ("EURUSD", "NASDAQ100"):
    df = lib.load(inst)
    m5 = df.set_index("time")[["open", "high", "low", "close"]].resample("5min").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    loc = m5.index.tz_convert("Europe/Paris"); hour = loc.hour.values; day = loc.tz_localize(None).normalize().values
    T = (m5.index.values.astype("datetime64[m]").astype(np.int64))
    O, Hh, L, Cc = (m5[c].values for c in ("open", "high", "low", "close"))
    cs = pd.Series(Cc); d = cs.diff()
    rsi = (100 - 100 / (1 + d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean() / (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean())).values
    k = (100 * (cs - pd.Series(L).rolling(14).min()) / (pd.Series(Hh).rolling(14).max() - pd.Series(L).rolling(14).min())).rolling(3).mean().values
    sig = {"RSI": np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0)), "STOCH": np.where(k < 20, 1, np.where(k > 80, -1, 0))}
    sig["LES 2"] = np.where(sig["RSI"] == sig["STOCH"], sig["RSI"], 0)
    for name, s in sig.items():
        new = np.flatnonzero((s != 0) & (np.r_[0, s[:-1]] != s)); new = new[new + 25 < len(T)]
        for u in US[inst]:
            busy = -1
            for i in new:
                e = i + 1
                if e <= busy or hour[e] >= 22 or T[e] - T[i] != 5 or T[e + 23] - T[e] > 150:
                    continue
                dd = int(s[i]); en = O[e]; st = en - dd * u; tp = en + dd * u
                hs, ls = Hh[e:e + 24], L[e:e + 24]
                sh = (ls <= st) if dd == 1 else (hs >= st); th = (hs >= tp) if dd == 1 else (ls <= tp)
                ks = np.argmax(sh) if sh.any() else 99; kt = np.argmax(th) if th.any() else 99
                if ks == 99 and kt == 99:
                    g, x = (Cc[e + 23] - en) * dd / u, e + 23
                elif ks <= kt:
                    g, x = -1.0, e + ks
                else:
                    g, x = 1.0, e + kt
                busy = x
                sess = "Asie" if hour[e] < 8 else ("Londres" if hour[e] < 14 else "New York")
                rows.append((inst, name, u, sess, day[e], g, COSTS[inst] / u))
    print(inst, "ok", flush=True)
t = pd.DataFrame(rows, columns=["instrument", "filtre", "u", "session", "day", "gross_r", "cost_r"]); t["day"] = pd.to_datetime(t.day)
t.to_csv(os.path.join(H, "scalp_m5.csv.gz"), index=False, float_format="%.5f")
t["net"] = t.gross_r - t.cost_r
print(t.groupby(["instrument", "filtre", "u", "session"]).agg(trades=("net", "size"), brut=("gross_r", "mean"), net=("net", "mean"),
      reussite=("gross_r", lambda x: (x > 0).mean() * 100)).round(3).to_string())
disc = t[t.day < lib.SPLIT].groupby(["instrument", "filtre", "u", "session"]).net.agg(["mean", "size"]); disc = disc[disc["size"] >= 300]
best = disc["mean"].idxmax()
g = t[(t.instrument == best[0]) & (t.filtre == best[1]) & (t.u == best[2]) & (t.session == best[3])]
print("\n", lib.line(lib.evaluate(g, f"MEILLEURE 2011-2018 : {best[0]} {best[1]} {best[2]} {best[3]}")))
print(f"Combinaisons positives après frais en 2011-2018 : {(disc['mean'] > 0).sum()}/{len(disc)}")
