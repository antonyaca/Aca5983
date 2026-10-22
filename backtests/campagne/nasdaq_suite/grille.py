"""Renforcement en perte (« moyenne à la baisse » / grille), demande d'Anto 22/10/2026. Règles fixées AVANT calcul.
Nasdaq M5, frais MNQ 0,75 pt par position. Taille : 1 € par point et par position.
Signal : RSI 14 M5 entre en survente (< 30) → achat ; entre en surachat (> 70) → vente (comme scalp_m5).
Renforcement : une position de plus à chaque recul de 20 pts depuis la 1re entrée, jusqu'à N positions au total.
Sortie de TOUTES les positions quand le gain cumulé atteint +20 € (objectif du panier), OU stop de panier, OU
fin de séance 22:00 Paris. Variantes : N ∈ {1, 3, 5} ; stop panier ∈ {aucun (seulement la fin de séance),
recul de (N+1) × 20 pts depuis la 1re entrée}. N = 1 = sans renforcement (référence).
Mesures : % de paniers gagnants, € moyen par panier, pire panier, total 16 ans, drawdown.
"""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); sys.path.insert(0, C)
import lib  # noqa
df = lib.load("NASDAQ100")
m5 = df.set_index("time")[["open", "high", "low", "close"]].resample("5min").agg(
    {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
loc = m5.index.tz_convert("Europe/Paris"); hour = loc.hour.values; day = loc.tz_localize(None).normalize().values
O, Hh, L, Cc = (m5[c].values for c in ("open", "high", "low", "close"))
cs = pd.Series(Cc); d = cs.diff()
rsi = (100 - 100 / (1 + d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean() / (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean())).values
s = np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0))
new = np.flatnonzero((s != 0) & (np.r_[0, s[:-1]] != s))
STEP, TP_EUR, COST = 20.0, 20.0, 0.75
res = []
for N in (1, 3, 5):
    for stop_mode in ("fin de séance", "stop panier"):
        busy = -1; out = []
        for i in new:
            e = i + 1
            if e <= busy or e >= len(Cc) - 1 or hour[e] >= 21 or day[e] < np.datetime64("2011-01-01"):
                continue
            dd = int(s[i]); p0 = O[e]; entries = [p0]
            hard = p0 - dd * (N + 1) * STEP if stop_mode == "stop panier" else None
            j = e; px = None
            while j < len(Cc) and day[j] == day[e] and hour[j] < 22:
                worst = L[j] if dd == 1 else Hh[j]; best = Hh[j] if dd == 1 else L[j]
                # renforts touchés dans la bougie (au niveau)
                while len(entries) < N and ((worst <= p0 - dd * STEP * len(entries)) if dd == 1 else (worst >= p0 - dd * STEP * len(entries))):
                    entries.append(p0 - dd * STEP * len(entries))
                if hard is not None and ((worst <= hard) if dd == 1 else (worst >= hard)):
                    px = hard; break
                avg = np.mean(entries); need = avg + dd * TP_EUR / len(entries)   # prix où le panier gagne +20 €
                if (best >= need) if dd == 1 else (best <= need):
                    px = need; break
                j += 1
            if px is None:
                j = j - 1; px = Cc[j]
            busy = j
            pnl = sum((px - en) * dd for en in entries) - COST * len(entries)
            out.append((day[e], pnl, len(entries)))
        t = pd.DataFrame(out, columns=["day", "pnl", "positions"])
        cum = t.pnl.cumsum(); ddm = (cum.cummax().clip(lower=0) - cum).max()
        res.append({"renforts max": N, "sortie": stop_mode, "paniers": len(t), "gagnants %": (t.pnl > 0).mean() * 100,
                    "€ moyen": t.pnl.mean(), "pire panier €": t.pnl.min(), "total 16 ans €": t.pnl.sum(), "drawdown €": ddm,
                    "2011-2018 €": t[t.day < np.datetime64("2019-01-01")].pnl.sum(), "2019-2026 €": t[t.day >= np.datetime64("2019-01-01")].pnl.sum()})
r = pd.DataFrame(res)
print(r.round(1).to_string(index=False))
r.to_csv(os.path.join(H, "grille.csv"), index=False)
