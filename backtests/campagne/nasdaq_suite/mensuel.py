"""Gain mensuel du robot NasdaqValides (Williams régulier achat si > SMA200 + RSI2<20 + 3 baisses), 100 € par trade,
coût ∝ prix + swap, gains comptés au jour d'entrée. 2011-2026."""
import os, sys
import pandas as pd
H = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(H, "drawdown.py")).read()
exec(src[:src.index("rows = []")])
t = combos["W-B + RSI2<20 + 3 baisses"]; t = t[t.day >= lib.START]
m = ((t.gross_r - t.cost_r) * 100).groupby([t.day.dt.year, t.day.dt.month]).sum().unstack().reindex(columns=range(1, 13)).fillna(0).round(0).astype(int)
m.columns = ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"]
m["TOTAL"] = m.sum(axis=1)
m.to_csv(os.path.join(H, "mensuel.csv"))
print(m.to_markdown())
v = m.drop(columns="TOTAL").values.flatten()[:-2]   # nov-déc 2026 non écoulés
print(f"\nmoyenne {v.mean():.0f} €/mois | médiane {pd.Series(v).median():.0f} | mois positifs {(v>0).mean()*100:.0f} % | pire mois {v.min()} | meilleur {v.max()}")
