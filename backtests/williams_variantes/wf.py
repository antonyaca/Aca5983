import sys, itertools, json, numpy as np, pandas as pd, multiprocessing as mp
sys.argv = ["wvar.py", "/home/claude/aca5983", "NASDAQ100", "{}"]
src = open("wvar.py").read(); src = src[:src.index("V = {\"Référence\": {}}")]
exec(src)
grid = list(itertools.product([0.4, 0.5], [690, 960], [None, 1.0], [None, 0.1], [None, "sma200"], [0, 1]))
def one(g):
    k, tm, tr, gp, trd, re = g
    p = dict(REF); p.update(k=k, tmax=tm, trail=tr, trend=trd, reentry=re)
    if gp: p.update(gapf="big", gapthr=gp)
    t = run(p); t["cfg"] = str(g); return t
if __name__ == "__main__":
    with mp.Pool(min(8, mp.cpu_count())) as pool: res = pool.map(one, grid)
    allt = pd.concat(res); allt.to_pickle("wf_trades.pkl")
    allt["y"] = allt.day.dt.year
    # walk-forward : chaque année Y (2015+), choisir la config au meilleur ratio (€ total / DD) sur 2011..Y-1, la jouer sur Y
    def score(x):
        eq = x.sort_values("day").r.cumsum(); dd = (eq.cummax().clip(lower=0) - eq).max()
        return x.r.sum() / max(dd, 1)
    picks, oos = [], []
    for Y in range(2015, 2027):
        past = allt[allt.y < Y]
        best = past.groupby("cfg").apply(score).idxmax()
        picks.append((Y, best)); oos.append(allt[(allt.y == Y) & (allt.cfg == best)])
    o = pd.concat(oos)
    eq = (o.r * 100).cumsum(); dd = (eq.cummax().clip(lower=0) - eq).max()
    yr = o.groupby("y").r.sum() * 100
    print("Choix année par année :"); [print(" ", Y, c) for Y, c in picks]
    print(f"WALK-FORWARD 2015-2026 : {len(o)} trades, E={o.r.mean():+.3f} R, t={o.r.mean()/o.r.std()*np.sqrt(len(o)):.2f}, "
          f"€/an={yr.mean():+.0f}, DD={dd:.0f} €, années+ {(yr>0).sum()}/{len(yr)}")
    print({int(k): round(v) for k, v in yr.items()})
    # classement in-sample complet pour info
    sc = allt.groupby("cfg").apply(lambda x: pd.Series(dict(n=len(x), E=x.r.mean(), an=x.r.sum()*100/15.83, ratio=score(x))))
    print(sc.sort_values("ratio", ascending=False).head(8).round(3).to_string())
    ref = allt[(allt.cfg == str((0.5, 960, None, None, None, 0))) & (allt.y >= 2015)]
    e2 = (ref.r*100).cumsum(); print(f"Référence actuelle 2015-2026 : €/an={ref.r.sum()*100/12:+.0f}, DD={(e2.cummax().clip(lower=0)-e2).max():.0f}")
