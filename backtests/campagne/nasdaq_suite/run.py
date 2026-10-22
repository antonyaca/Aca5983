"""Nasdaq — 3 pistes d'amélioration (22/10/2026). Règles fixées AVANT calcul. Coûts : proportionnel 1,25 pb (convention
qui valide le Williams) ET fixe 1,5 pt ; swap lib.SWAP (achat 6 %/an, vente 1 %/an). Critère : lib.evaluate.

1. FILTRE DE VOLATILITÉ sur le Williams : ne prendre le trade que si ATR5 > ATR50 (ATR journaliers de la séance
   09:30-15:55, calculés sur les séances PRÉCÉDENTES). Appliqué au Williams sortie 16:00 (trade 1) et au Williams
   « régulier » V04 (50 % à +0,5 R, stop à l'entrée, règle d'Anto). Comparaison avec la version sans filtre.
2. VERSIONS VENTE des swings (barres et exécution identiques à verification/verif_swing.py, 15:55 NY) :
   2a RSI2 vente : RSI2 > 90 et clôture < SMA200 → vente ; rachat dès clôture < SMA5.
   2b 3 hausses vente : 3 clôtures consécutives en hausse et clôture < SMA200 → vente ; rachat à la 1re clôture en baisse
      ou après 5 séances.
3. ROBUSTESSE DU RSI2 ACHAT (voisinage du réglage validé, pas d'optimisation) : RSI2 < 5 ; RSI2 < 20 ; RSI3 < 10 ;
   tous avec clôture > SMA200 et sortie clôture > SMA5. RSI de Wilder (lissage 1/n).
1 R = ATR14 pour les swings ; risque Williams = distance ouverture-niveau.
"""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); sys.path.insert(0, C)
import lib  # noqa
src = open(os.path.join(C, "verification", "verif_swing.py")).read()
ns = {"__file__": os.path.join(C, "verification", "verif_swing.py")}; exec(src[:src.index("out = {}")], ns)
b = ns["bars"]("NASDAQ100")
PV = os.path.join(C, "jour", "plan_valides")


def costs(t, entry_col="entry", risk_col="risque"):
    return {"∝ prix": t[entry_col] * 1.25e-4 / t[risk_col], "fixe": 1.5 / t[risk_col]}


def show(t, label, extra_cost=None):
    for cname in ("∝ prix", "fixe"):
        c = costs(t)[cname] + (extra_cost if extra_cost is not None else 0)
        u = t.assign(cost_r=c.values)
        r = lib.evaluate(u, f"{label} · {cname}")
        s = lib.stats_jour(u)
        print(lib.line(r), f"| jours+ {s['jours_positifs_pct_jours_trades']:.0f}% | {s['eur_par_an']:+d} €/an")


# ---------------- 1. filtre de volatilité
pc = b.C.shift()
tr = pd.concat([b.H - b.L, (b.H - pc).abs(), (b.L - pc).abs()], axis=1).max(axis=1)
ok = (tr.rolling(5).mean() > tr.rolling(50).mean()).shift(1).fillna(False)
w = pd.read_csv(os.path.join(PV, "williams_2e_chance_trades.csv.gz"), parse_dates=["day"]); w = w[w.n == 1]
v = pd.read_csv(os.path.join(PV, "verif_v04_trades.csv.gz"), parse_dates=["day"])
print("== 1. Filtre ATR5 > ATR50 (part des jours retenus : %.0f %%)" % (ok[ok.index >= "2011"].mean() * 100))
for name, t in (("Williams clôture", w), ("Williams régulier V04", v)):
    show(t, f"{name} sans filtre")
    show(t[t.day.map(ok).fillna(False).astype(bool).values], f"{name} + filtre volatilité")


# ---------------- 2 et 3. swings
def rsi(c, n):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def swing(es, xs, maxd, d):
    days, Cc, atr = b.index, b.C.values, b.atr.values
    sl, ss = lib.SWAP["NASDAQ100"]; rows = []; i = 0; n = len(b)
    while i < n - 2:
        if not es[i] or not np.isfinite(atr[i]):
            i += 1; continue
        j = i + 1
        while j < n and not (xs[j] or (maxd and j - i >= maxd)):
            j += 1
        if j >= n - 1:
            break
        if ((days[i + 1:j + 1] - days[i:j]).days > 7).any():
            i = j + 1; continue
        nights = (days[j] - days[i]).days; R = atr[i]
        rows.append({"day": days[i], "entry": Cc[i], "risque": R, "gross_r": (Cc[j] - Cc[i]) * d / R,
                     "swap_r": Cc[i] * (sl if d == 1 else ss) * nights / 360 / R})
        i = j + 1
    return pd.DataFrame(rows)


c = b.C; sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
r2 = b.rsi
print("\n== 2. Versions vente")
t = swing(((r2 > 90) & (c < sma200)).values, (c < sma5).values, None, -1); show(t, "RSI2 vente", t.swap_r)
up3 = (c > c.shift()) & (c.shift() > c.shift(2)) & (c.shift(2) > c.shift(3))
t = swing((up3 & (c < sma200)).values, (c < c.shift()).values, 5, -1); show(t, "3 hausses vente", t.swap_r)
print("\n== 3. Voisinage du RSI2 achat")
t = swing(((r2 < 10) & (c > sma200)).values, (c > sma5).values, None, 1); show(t, "RSI2 < 10 (référence validée)", t.swap_r)
for lab, cond in (("RSI2 < 5", rsi(c, 2) < 5), ("RSI2 < 20", rsi(c, 2) < 20), ("RSI3 < 10", rsi(c, 3) < 10)):
    t = swing((cond & (c > sma200)).values, (c > sma5).values, None, 1); show(t, lab, t.swap_r)
