"""Filtres pré-enregistrés sur les 3 stratégies qui ont montré quelque chose.

A. ORB 30 min Nasdaq, achats seuls, sortie 16:00            (contrôle : S&P 500, mêmes règles)
B. Range asiatique XAUUSD, sortie 16:30 Londres              (contrôle : EURUSD)
C. Gap fade Nasdaq, gap ≥ 0,5 ATR                            (contrôle : S&P 500)

Protocole (identique pour les trois, fixé avant lecture) :
- Filtres candidats ci-dessous ; tous les seuils calculés sur l'in-sample (2020-2023) du marché concerné.
- Un filtre est retenu s'il améliore l'espérance nette IS du marché principal d'au moins +0,03 R,
  garde ≥ 40 % des trades IS, ET améliore aussi l'espérance nette IS du marché de contrôle.
- Filtres retenus combinés (ET logique). Validation finale : E nette > 0 en IS et en OOS, PF net ≥ 1,10,
  E nette OOS > 0 avec frais doublés.
- Portefeuille : toutes les versions validées tradées ensemble, 100 € par trade.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BT, "batch2"))
from strategies import load, COST, IS_END, st  # noqa: E402

STRATS = {
    "A": {"nom": "ORB 30 min Nasdaq, achats seuls", "src": "intraday", "reg": "ORB 30 min · sortie clôture",
          "main": "NASDAQ100", "ctrl": "SP500", "tz": "America/New_York", "rth": (570, 960), "buy_only": True},
    "B": {"nom": "Range asiatique or", "src": "batch2", "reg": "Range asiatique · sortie clôture",
          "main": "XAUUSD", "ctrl": "EURUSD", "tz": "Europe/London", "rth": (0, 1440), "buy_only": False},
    "C": {"nom": "Gap fade Nasdaq (≥ 0,5 ATR)", "src": "batch2", "reg": "Gap fade · gap ≥ 0,5 ATR",
          "main": "NASDAQ100", "ctrl": "SP500", "tz": "America/New_York", "rth": (570, 960), "buy_only": False},
}
_cache = {}


def daily(inst, tz, rth):
    key = (inst, tz)
    if key not in _cache:
        days = load(inst, tz)
        rows = []
        for d in sorted(days):
            g = days[d]
            s = g[(g["hm"] >= rth[0]) & (g["hm"] < rth[1])]
            if len(s) < 200:
                continue
            o = s[s["hm"] == rth[0]]["open"]
            rows.append({"day": pd.Timestamp(d), "high": s["high"].max(), "low": s["low"].min(),
                         "close": s["close"].iloc[-1], "open": o.iloc[0] if len(o) else np.nan})
        x = pd.DataFrame(rows).set_index("day")
        prev = x["close"].shift(1)
        tr = pd.concat([x["high"] - x["low"], (x["high"] - prev).abs(), (x["low"] - prev).abs()], axis=1).max(axis=1)
        x["prev_close"] = prev
        x["atr"] = tr.rolling(14).mean().shift(1)
        x["sma50"] = x["close"].rolling(50).mean().shift(1)
        x["gap"] = x["open"] - prev
        _cache[key] = x
    return _cache[key]


def trades(code, inst):
    s = STRATS[code]
    if s["src"] == "intraday":
        t = pd.read_csv(os.path.join(BT, "intraday", "results", inst, "trades.csv.gz"), parse_dates=["day"])
    else:
        t = pd.read_csv(os.path.join(BT, "batch2", "results", "trades.csv.gz"), parse_dates=["day"])
        t = t[t["instrument"] == inst]
    t = t[t["reglage"] == s["reg"]].copy()
    if s["buy_only"]:
        t = t[t["direction"] == "BUY"]
    t["net_r"] = t["gross_r"] - COST[inst] / t["risque"]
    t["net2_r"] = t["gross_r"] - 2 * COST[inst] / t["risque"]
    t["dir"] = np.where(t["direction"] == "BUY", 1, -1)
    f = daily(inst, s["tz"], s["rth"])
    t = t.join(f[["prev_close", "atr", "sma50", "gap"]], on="day").dropna(subset=["atr", "sma50"])
    t["range_atr"] = t["range"] / t["atr"]
    t["atr_pct"] = t["atr"] / t["prev_close"]
    t["is"] = t["day"] < IS_END
    return t.sort_values("day")


def masks(code, t):
    s = STRATS[code]
    ref = t[t["is"]]
    q1, q2 = ref["range_atr"].quantile([1 / 3, 2 / 3])
    vm = ref["atr_pct"].median()
    hm = ref["entry_hm"].median()
    trend = np.sign(t["prev_close"] - t["sma50"])
    m = {
        "Sens de la tendance (SMA 50)": t["dir"] == trend,
        "Contre la tendance (SMA 50)": t["dir"] != trend,
        "Volatilité haute (ATR % > médiane)": t["atr_pct"] > vm,
        "Volatilité basse (ATR % ≤ médiane)": t["atr_pct"] <= vm,
        "Range ou gap petit (tiers bas / ATR)": t["range_atr"] <= q1,
        "Range ou gap grand (tiers haut / ATR)": t["range_atr"] >= q2,
    }
    if code != "C":
        m["Entrée tôt (avant la médiane)"] = t["entry_hm"] <= hm
        m["Entrée tard (après la médiane)"] = t["entry_hm"] > hm
    if not s["buy_only"]:
        m["Achats seulement"] = t["dir"] == 1
        m["Ventes seulement"] = t["dir"] == -1
    if code == "A":
        m["Gap d'ouverture haussier"] = t["gap"] > 0
        m["Gap d'ouverture baissier"] = t["gap"] < 0
    return m


def full(t):
    r = t["net_r"].values
    o = t[~t["is"]]
    return {"total": st(r), "is": st(t[t["is"]]["net_r"].values), "oos": st(o["net_r"].values),
            "oos_x2": float(o["net2_r"].mean()) if len(o) else None,
            "par_annee": {str(y): round(float(g["net_r"].mean()), 3) for y, g in t.groupby(t["day"].dt.year)}}


def valid(x):
    return bool(x["is"] and x["oos"] and x["is"]["e_r"] > 0 and x["oos"]["e_r"] > 0
                and (x["total"]["pf"] or 0) >= 1.10 and (x["oos_x2"] or -1) > 0)


def fmt(x):
    return f"{x['trades']:>4}t {x['e_r']:+.3f}R {x['resultat_eur']:>7.0f}€" if x else "   -"


def main():
    report, finals = {}, {}
    for code, s in STRATS.items():
        tm, tc = trades(code, s["main"]), trades(code, s["ctrl"])
        mm, mc = masks(code, tm), masks(code, tc)
        bm, bc = full(tm), full(tc)
        print(f"\n=== {code} · {s['nom']} — base {s['main']} IS {fmt(bm['is'])} OOS {fmt(bm['oos'])} | contrôle {s['ctrl']} IS {fmt(bc['is'])}")
        rows, kept = [], []
        for name in mm:
            a = full(tm[mm[name].values]); c = full(tc[mc[name].values])
            ok = (a["is"] is not None and c["is"] is not None
                  and a["is"]["trades"] >= 0.4 * bm["is"]["trades"]
                  and a["is"]["e_r"] - bm["is"]["e_r"] >= 0.03 and c["is"]["e_r"] > bc["is"]["e_r"])
            if ok:
                kept.append(name)
            rows.append({"filtre": name, "retenu": ok, "principal": a, "controle": c})
            print(f"{'*' if ok else ' '} {name:38} IS {fmt(a['is'])} OOS {fmt(a['oos'])} | ctrl IS {fmt(c['is'])}")
        m = np.ones(len(tm), bool)
        for name in kept:
            m &= mm[name].values
        ft = tm[m]
        fin = full(ft)
        fin["valide"] = valid(fin)
        base_valid = valid(bm)
        print(f"  Retenus : {kept or 'aucun'} → final IS {fmt(fin['is'])} OOS {fmt(fin['oos'])} PF {fin['total']['pf']:.2f} "
              f"x2 {fin['oos_x2']:+.3f} DD {fin['total']['max_dd_eur']:.0f}€ {'VALIDÉ' if fin['valide'] else 'non validé'} "
              f"(base {'validée' if base_valid else 'non validée'})")
        print("  par année", fin["par_annee"])
        report[code] = {"nom": s["nom"], "base": bm, "base_valide": base_valid, "filtres": rows, "retenus": kept, "final": fin}
        if fin["valide"]:
            finals[code] = ft.assign(strategie=code)
        elif base_valid:
            finals[code] = tm.assign(strategie=code)

    if finals:
        p = pd.concat(finals.values()).sort_values("day")
        port = full(p)
        r = p.groupby("day")["net_r"].sum()
        cum = r.cumsum().values
        port["max_dd_eur_jour"] = float((np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max() * 100)
        port["composants"] = list(finals)
        report["portefeuille"] = port
        print(f"\nPORTEFEUILLE {list(finals)} : {fmt(port['total'])} IS {fmt(port['is'])} OOS {fmt(port['oos'])} "
              f"PF {port['total']['pf']:.2f} DD {port['max_dd_eur_jour']:.0f}€ ; par année {port['par_annee']}")
        p[["day", "strategie", "direction", "risque", "gross_r", "net_r"]].to_csv(
            os.path.join(HERE, "portefeuille_trades.csv"), index=False, float_format="%.5f")
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
