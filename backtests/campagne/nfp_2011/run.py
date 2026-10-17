"""NFP hors échantillon 2011-2019 (règle NFP inchangée, backtests/nfp/backtest.py), données corrigées (vrai UTC).

Dates 2011-2019 : calendrier officiel BLS, archive https://www.bls.gov/bls/news-release/empsit.htm (108 publications,
dont le 22/10/2013 décalé par le shutdown). Réglages jugés : ceux validés sur 2020-2026 après correction horaire
(range 08:00-08:30, TP 1:2 et clôture 16:00, Nasdaq et or). Coûts doublés (spread d'annonce), comme l'original.
"""
import importlib.util, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(HERE)
sys.path.insert(0, CAMP)
import lib  # noqa
spec = importlib.util.spec_from_file_location("nfp_bt", os.path.join(os.path.dirname(CAMP), "nfp", "backtest.py"))
nfp = importlib.util.module_from_spec(spec); spec.loader.exec_module(nfp)
BLS_2011_2019 = """2011-01-07 2011-02-04 2011-03-04 2011-04-01 2011-05-06 2011-06-03 2011-07-08 2011-08-05 2011-09-02 2011-10-07 2011-11-04 2011-12-02
2012-01-06 2012-02-03 2012-03-09 2012-04-06 2012-05-04 2012-06-01 2012-07-06 2012-08-03 2012-09-07 2012-10-05 2012-11-02 2012-12-07
2013-01-04 2013-02-01 2013-03-08 2013-04-05 2013-05-03 2013-06-07 2013-07-05 2013-08-02 2013-09-06 2013-10-22 2013-11-08 2013-12-06
2014-01-10 2014-02-07 2014-03-07 2014-04-04 2014-05-02 2014-06-06 2014-07-03 2014-08-01 2014-09-05 2014-10-03 2014-11-07 2014-12-05
2015-01-09 2015-02-06 2015-03-06 2015-04-03 2015-05-08 2015-06-05 2015-07-02 2015-08-07 2015-09-04 2015-10-02 2015-11-06 2015-12-04
2016-01-08 2016-02-05 2016-03-04 2016-04-01 2016-05-06 2016-06-03 2016-07-08 2016-08-05 2016-09-02 2016-10-07 2016-11-04 2016-12-02
2017-01-06 2017-02-03 2017-03-10 2017-04-07 2017-05-05 2017-06-02 2017-07-07 2017-08-04 2017-09-01 2017-10-06 2017-11-03 2017-12-08
2018-01-05 2018-02-02 2018-03-09 2018-04-06 2018-05-04 2018-06-01 2018-07-06 2018-08-03 2018-09-07 2018-10-05 2018-11-02 2018-12-07
2019-01-04 2019-02-01 2019-03-08 2019-04-05 2019-05-03 2019-06-07 2019-07-05 2019-08-02 2019-09-06 2019-10-04 2019-11-01 2019-12-06""".split()
assert len(BLS_2011_2019) == 108
nfp.NFP = BLS_2011_2019 + nfp.NFP
nfp.load_m1 = lambda inst, tz: lib.load(inst, tz)
out = {}
for inst in ("NASDAQ100", "XAUUSD"):
    rows, miss = nfp.run(inst)
    t = pd.DataFrame(rows)
    print(inst, "publications sans données suffisantes :", len(miss))
    for reg, g in t[t["reglage"].str.startswith("avant")].groupby("reglage"):
        g = g.sort_values("day"); x = g["gross_r"] - g["cost_r"]
        a, b = x[g["day"] < "2020-01-01"], x[g["day"] >= "2020-01-01"]
        r = lib.evaluate(g, f"{inst} {reg}")
        r["2011-2019"] = {"n": len(a), "e_r": round(a.mean(), 3), "eur": round(a.sum() * 100),
                          "t": round(a.mean() / a.std() * np.sqrt(len(a)), 2)}
        r["2020-2026"] = {"n": len(b), "e_r": round(b.mean(), 3), "eur": round(b.sum() * 100)}
        out[f"{inst} {reg}"] = r
        print(lib.line(r)); print("   2011-2019 :", r["2011-2019"], "| 2020-2026 :", r["2020-2026"])
    t.to_csv(os.path.join(HERE, f"trades_{inst}.csv.gz"), index=False)
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=1, default=float)
