"""Filtres sur l'ORB 30 min · sortie clôture (Nasdaq, contrôle sur S&P 500).

Protocole fixé avant de lire les résultats :
- Filtres candidats définis à l'avance (liste FILTERS), seuils calculés sur l'in-sample (2020-2023) uniquement.
- Règle de sélection : un filtre est retenu s'il améliore l'espérance nette in-sample du Nasdaq d'au moins +0,03 R,
  garde au moins 40 % des trades, ET améliore aussi l'in-sample du S&P 500 (contrôle indépendant).
- Les filtres retenus sont combinés, puis jugés sur l'out-of-sample (2024-2026) sans aucun ajustement.
Sortie : results/filters.json
"""
import json
import os

import numpy as np
import pandas as pd

from backtest import IS_END, daily_atr, load, rth_days, COSTS, RISK_EUR

HERE = os.path.dirname(os.path.abspath(__file__))
REG = "ORB 30 min · sortie clôture"


def features(inst):
    df = load(inst)
    days = rth_days(df)
    atr, close = daily_atr(days)
    keys = sorted(days)
    cl = pd.Series([close[k] for k in keys], index=keys)
    sma50 = cl.rolling(50).mean().shift(1)            # jours précédents uniquement
    prev = cl.shift(1)
    first_open = {k: days[k][days[k]["hm"] == 570]["open"].iloc[0] if (days[k]["hm"] == 570).any() else np.nan for k in keys}
    t = pd.read_csv(os.path.join(HERE, "results", inst, "trades.csv.gz"), parse_dates=["day"])
    t = t[t["reglage"] == REG].copy()
    d = t["day"].dt.date
    t["dir"] = np.where(t["direction"] == "BUY", 1, -1)
    t["prev_close"] = d.map(prev)
    t["sma50"] = d.map(sma50)
    t["atr"] = d.map(atr)
    t["gap"] = d.map(first_open) - t["prev_close"]
    t["or_atr"] = t["range"] / t["atr"]
    t["atr_pct"] = t["atr"] / t["prev_close"]
    t = t.dropna(subset=["sma50", "atr", "gap"])
    t["is"] = t["day"] < IS_END
    return t


def filters_for(t, ref):
    """ref = in-sample du même marché, pour les seuils."""
    q1, q2 = ref["or_atr"].quantile([1 / 3, 2 / 3])
    med_vol = ref["atr_pct"].median()
    trend = np.sign(t["prev_close"] - t["sma50"])
    return {
        "Dans le sens de la tendance (SMA 50)": t["dir"] == trend,
        "Contre la tendance (SMA 50)": t["dir"] != trend,
        "Gap d'ouverture dans le même sens": np.sign(t["gap"]) == t["dir"],
        "Gap d'ouverture en sens inverse": np.sign(t["gap"]) == -t["dir"],
        "Entrée avant 11:00": t["entry_hm"] < 660,
        "Entrée après 11:00": t["entry_hm"] >= 660,
        "Range étroit (tiers bas range/ATR)": t["or_atr"] <= q1,
        "Range large (tiers haut range/ATR)": t["or_atr"] >= q2,
        "Volatilité haute (ATR % > médiane)": t["atr_pct"] > med_vol,
        "Volatilité basse (ATR % ≤ médiane)": t["atr_pct"] <= med_vol,
        "Achats seulement": t["dir"] == 1,
        "Ventes seulement": t["dir"] == -1,
    }


def st(x):
    r = x["net_r"].values
    if len(r) == 0:
        return {"trades": 0}
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    cum = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.concatenate([[0], cum]))[1:] - cum).max())
    return {"trades": int(len(r)), "esperance_net_r": float(r.mean()), "pf_net": float(pos / neg) if neg else None,
            "resultat_eur": float(r.sum() * RISK_EUR), "max_dd_eur": dd * RISK_EUR, "win_rate": float((r > 0).mean() * 100)}


def main():
    data = {inst: features(inst) for inst in ("NASDAQ100", "SP500")}
    masks = {inst: filters_for(t, t[t["is"]]) for inst, t in data.items()}
    base = {inst: {"is": st(t[t["is"]]), "oos": st(t[~t["is"]])} for inst, t in data.items()}
    rows, selected = [], []
    for name in masks["NASDAQ100"]:
        row = {"filtre": name}
        for inst, t in data.items():
            m = masks[inst][name]
            row[inst] = {"is": st(t[t["is"] & m]), "oos": st(t[~t["is"] & m])}
        nq, sp = row["NASDAQ100"]["is"], row["SP500"]["is"]
        keep = (nq["trades"] >= 0.4 * base["NASDAQ100"]["is"]["trades"]
                and nq["esperance_net_r"] - base["NASDAQ100"]["is"]["esperance_net_r"] >= 0.03
                and sp["trades"] > 0 and sp["esperance_net_r"] > base["SP500"]["is"]["esperance_net_r"])
        row["retenu"] = bool(keep)
        if keep:
            selected.append(name)
        rows.append(row)

    combo = {}
    for inst, t in data.items():
        m = np.ones(len(t), bool)
        for name in selected:
            m &= masks[inst][name].values
        tt = t[m]
        combo[inst] = {"is": st(tt[tt["is"]]), "oos": st(tt[~tt["is"]]),
                       "par_annee": {str(y): st(g) for y, g in tt.groupby(tt["day"].dt.year)},
                       "cout_x2_oos": float((tt[~tt["is"]]["gross_r"] - 2 * COSTS[inst] / tt[~tt["is"]]["risque"]).mean()) if len(tt[~tt["is"]]) else None}
        tt[["day", "direction", "entry", "exit", "motif", "risque", "gross_r", "net_r"]].to_csv(
            os.path.join(HERE, "results", inst, "orb30_filtre_trades.csv"), index=False)
    out = {"base": base, "filtres": rows, "retenus": selected, "combinaison": combo}
    with open(os.path.join(HERE, "results", "filters.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    def fmt(s):
        return f"{s['trades']:>4}t {s.get('esperance_net_r', 0):+.3f}R {s.get('resultat_eur', 0):>7.0f}€"
    print("BASE  NQ IS", fmt(base["NASDAQ100"]["is"]), "| OOS", fmt(base["NASDAQ100"]["oos"]),
          "|| SP IS", fmt(base["SP500"]["is"]), "| OOS", fmt(base["SP500"]["oos"]))
    for r in rows:
        print(f"{'*' if r['retenu'] else ' '} {r['filtre']:38} NQ IS {fmt(r['NASDAQ100']['is'])} | OOS {fmt(r['NASDAQ100']['oos'])} || SP IS {fmt(r['SP500']['is'])} | OOS {fmt(r['SP500']['oos'])}")
    print("Retenus :", selected)
    for inst, c in combo.items():
        print(inst, "IS", fmt(c["is"]), "OOS", fmt(c["oos"]), "DD", round(c["oos"].get("max_dd_eur", 0)), "coût x2 OOS", c["cout_x2_oos"])
        print("   ", {y: round(v["esperance_net_r"], 3) for y, v in c["par_annee"].items()})


if __name__ == "__main__":
    main()
