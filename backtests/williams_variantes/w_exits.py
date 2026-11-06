import glob, sys, numpy as np, pandas as pd
ROOT=sys.argv[1]; COST=1.5
df=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{ROOT}/data/NASDAQ100/NASDAQ100_M1_*.csv.gz"))])
df["time"]=pd.to_datetime(df["time"],utc=True); df=df.drop_duplicates("time").sort_values("time")
ny=df.time.dt.tz_convert("America/New_York"); df["m"]=ny.dt.hour*60+ny.dt.minute; df["d"]=ny.dt.date
df=df[(df.m>=570)&(df.m<960)]
# variantes : (nom, heure sortie NY en min, TP en R, BE après +xR, trailing en R)
V=[("Clôture 22h (réf.)",960,None,None,None)]
for hh,lab in [(660,"17h"),(720,"18h"),(780,"19h"),(840,"20h"),(900,"21h")]: V.append((f"Sortie {lab} Paris",hh,None,None,None))
for tp in [1,1.5,2,3]: V.append((f"TP {tp}R sinon 22h",960,tp,None,None))
V.append(("Stop à BE après +1R",960,None,1,None)); V.append(("Stop à BE après +0,5R",960,None,0.5,None))
V.append(("Trailing 1R",960,None,None,1.0)); V.append(("Trailing 1,5R",960,None,None,1.5))
res={v[0]:[] for v in V}; prev=None
for d,g in df.groupby("d"):
    if len(g)<300: prev=None; continue
    o,h,l,c,m=g.open.values,g.high.values,g.low.values,g.close.values,g.m.values
    if prev:
        op=o[0]; up=op+.5*prev; dn=op-.5*prev
        for i in range(len(g)):
            hu,hd=h[i]>=up,l[i]<=dn
            if hu and hd: break
            if hu or hd:
                s=1 if hu else -1; e=up if hu else dn; R=abs(e-op)
                for name,tx,tp,be,tr in V:
                    stop=op; best=0.0; r=None
                    for j in range(i,len(g)):
                        if m[j]>=tx: r=s*(o[j]-e)/R; break
                        lo=s*(l[j]-e)/R if s==1 else s*(h[j]-e)/R   # pire excursion
                        hi=s*(h[j]-e)/R if s==1 else s*(l[j]-e)/R   # meilleure
                        sr=s*(stop-e)/R
                        if lo<=sr: r=sr; break
                        if tp and hi>=tp and j>i: r=tp; break
                        best=max(best,hi) if j>i else best
                        if be and best>=be: stop=max(stop,e) if s==1 else min(stop,e)
                        if tr and best>0: ns=e+s*(best-tr)*R; stop=max(stop,ns) if s==1 else min(stop,ns)
                    if r is None: r=s*(c[-1]-e)/R
                    res[name].append((pd.Timestamp(d),r-COST/R))
                break
    prev=h.max()-l.min()
for name,_,_,_,_ in V:
    t=pd.DataFrame(res[name],columns=["day","r"]); t=t[t.day>="2011-01-01"]; t["eur"]=t.r*100
    def s(x):
        eq=x.eur.cumsum(); return x.r.mean(), x.eur.sum()/((x.day.max()-x.day.min()).days/365.25), (eq.cummax()-eq).max(), x.r.mean()/x.r.std()*np.sqrt(len(x))
    a=s(t); b=s(t[t.day<"2019"]); c2=s(t[t.day>="2019"])
    y=t.groupby(t.day.dt.year).eur.sum()
    print(f"{name:24} E={a[0]:+.3f} t={a[3]:+.2f} €/an={a[1]:+6.0f} DD={a[2]:5.0f} | 11-18 E={b[0]:+.3f} | 19-26 E={c2[0]:+.3f} €/an={c2[1]:+5.0f} | ans+ {(y>0).sum()}/16 win {100*(t.r>0).mean():.0f}%")
