"""Règle NFP de l'or appliquée SANS CHANGEMENT aux jours CPI et FOMC (piste n° 3 de la recherche, 18/10/2026).
Règles fixées AVANT calcul.

Règle (code events/backtest.py, inchangé) : range des 30 minutes avant l'annonce ; 1er franchissement entre l'annonce et
+2 h 30 (sans dépasser 15:30 NY) ; deux sens ; stop = bord opposé ; sorties TP 1:2 ou clôture 16:00 ; coûts ×2.
Annonces : CPI 08:30 NY, 2011-2026 (BLS : 2011-2019 = archive des communiqués relevée par l'agent forex_or ;
2020-2026 = events/backtest.py). FOMC 14:00 NY, 2013-2026 seulement : en 2011-2012 le communiqué sortait à 12:30 ou
14:15 (vérifié dans les données : pic de volatilité de l'or à 14:00 chaque année à partir de 2013, ailleurs avant).
Rappel validé : NFP or (même règle) 160 trades, +0,565 R, t 4,56.
Jugement : lib.evaluate sur CPI seul, FOMC seul, CPI + FOMC, et NFP + CPI + FOMC (TP 1:2 = réglage validé du NFP).
"""
import importlib.util, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.dirname(os.path.dirname(HERE))
BT = os.path.dirname(CAMP)
sys.path.insert(0, CAMP)
import lib  # noqa


def load_module(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


ev = load_module("ev_bt", os.path.join(BT, "events", "backtest.py"))
src = open(os.path.join(CAMP, "jour", "forex_or", "run.py")).read()
ns = {}
exec(src[src.index('CPI_BLS = """'):src.index("assert len(NFP_2011_2019)")], {}, ns)
CPI = ns["CPI_2011_2019"] + list(ev.CPI)
FOMC = [d for d in ns["FOMC_2011_2019"] if d >= "2013-01-01"] + list(ev.FOMC)
assert len(set(CPI)) == len(CPI) and len(set(FOMC)) == len(FOMC)
ev.EVENTS = {"CPI": (CPI, 510), "FOMC": (FOMC, 840)}
ev.COST = {"XAUUSD": 0.47 * 2}
ev.load_m1 = lambda inst, tz: lib.load(inst, tz)


def main():
    rows, miss = ev.run("XAUUSD")
    print("annonces sans données suffisantes :", miss)
    t = pd.DataFrame(rows)
    nf = pd.read_csv(os.path.join(CAMP, "nfp_2011", "trades_XAUUSD.csv.gz"), parse_dates=["day"])
    nf = nf[nf.reglage.str.startswith("avant")].copy()
    nf["evenement"] = "NFP"; nf["sortie"] = np.where(nf.reglage.str.contains("TP"), "TP 1:2", "clôture 16:00")
    out = []
    for ex in ("TP 1:2", "clôture 16:00"):
        a = t[t.sortie == ex]; b = nf[nf.sortie == ex]
        groups = [("CPI", a[a.evenement == "CPI"]), ("FOMC 2013+", a[a.evenement == "FOMC"]), ("CPI + FOMC", a),
                  ("NFP + CPI + FOMC", pd.concat([a, b[a.columns.intersection(b.columns)]]))]
        for lab, g in groups:
            r = lib.evaluate(g, f"Or {lab} · {ex}"); s = lib.stats_jour(g)
            r["jour"] = s; out.append(r)
            print(lib.line(r), "|", f"{len(g) / 15.77:.0f} trades/an")
    t.to_csv(os.path.join(HERE, "or_cpi_fomc_trades.csv.gz"), index=False, float_format="%.6f")
    json.dump(out, open(os.path.join(HERE, "or_cpi_fomc.json"), "w"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
