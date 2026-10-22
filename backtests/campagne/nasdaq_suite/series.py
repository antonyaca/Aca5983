"""Pires séries du robot NasdaqValides (100 € par trade, coût ∝ prix + swap, 2011-2026)."""
import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(H, "drawdown.py")).read(); exec(src[:src.index("rows = []")])
t = combos["W-B + RSI2<20 + 3 baisses"]; t = t[t.day >= lib.START].sort_values("day")
x = ((t.gross_r - t.cost_r) * 100).values
# plus longue série de trades perdants consécutifs et sa perte
best_n = best_loss = run_n = run_loss = 0; worst_loss_run = 0
for v in x:
    if v < 0: run_n += 1; run_loss += v
    else: run_n = run_loss = 0
    best_n = max(best_n, run_n); worst_loss_run = min(worst_loss_run, run_loss)
cum = np.cumsum(x); peak = np.maximum.accumulate(np.r_[0, cum])[1:]; dd = peak - cum
i = int(dd.argmax()); j = int(np.argmax(cum[:i + 1] == peak[i]))
rec = np.flatnonzero(cum[i:] >= peak[i]); k = i + int(rec[0]) if len(rec) else None
d = t.day.values
print(f"Plus longue série de trades perdants : {best_n} trades ; pire perte cumulée en série : {worst_loss_run:.0f} €")
print(f"Plus grosse baisse du compte (drawdown) : {dd.max():.0f} € — du {pd.Timestamp(d[j]):%d/%m/%Y} au {pd.Timestamp(d[i]):%d/%m/%Y}"
      + (f", récupérée le {pd.Timestamp(d[k]):%d/%m/%Y}" if k is not None else ", pas encore récupérée"))
p = pd.Series(x, index=t.day.values).groupby(level=0).sum()
full = p.reindex(pd.bdate_range(lib.START, lib.DATA_END), fill_value=0)
m = full.resample("ME").sum(); neg = (m < 0).astype(int)
r = mx = 0; lossm = 0; worstm = 0
for v, s in zip(neg.values, m.values):
    r = r + 1 if v else 0; lossm = lossm + s if v else 0; mx = max(mx, r); worstm = min(worstm, lossm)
print(f"Plus longue série de mois négatifs : {mx} mois ; pire perte en mois négatifs consécutifs : {worstm:.0f} €")
cm = m.cumsum(); ddm = (cm.cummax() - cm)
print(f"Plus longue période sans nouveau sommet : {int(((cm < cm.cummax()).astype(int).groupby((cm >= cm.cummax()).cumsum()).sum()).max())} mois")
print(f"Pire jour : {full.min():.0f} € ; pire trade : {x.min():.0f} €")
