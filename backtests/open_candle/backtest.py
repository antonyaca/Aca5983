"""Backtest « bougie d'ouverture » M15 — sessions Londres 08:00 et New York 09:30 (heure locale).

Usage : python3 backtest.py [XAUUSD|EURUSD|SP500|NASDAQ100 ...]  (défaut : les 4)
Règles : voir README.md du même dossier.
Données : data/<INSTRUMENT>/*.csv.gz (M1, bid, UTC). Les sorties SL/TP sont simulées minute par minute.
Sorties : results/<INSTRUMENT>/trades.csv.gz et results/<INSTRUMENT>/summary.json.
"""
import glob
import json
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))

# Paramètres par instrument (unités de prix de l'instrument).
# marge SL : 0,20 $ sur l'or (~0,01 % du prix), équivalent proportionnel ailleurs.
# coûts aller-retour : spread + slippage + commission.
INSTRUMENTS = {
    "XAUUSD":    {"margin": 0.20,   "spread": 0.30,    "slippage": 0.10,    "commission": 0.07,    "unite": "$"},
    "EURUSD":    {"margin": 0.0001, "spread": 0.00006, "slippage": 0.00002, "commission": 0.00007, "unite": "pip=0.0001"},
    "SP500":     {"margin": 0.50,   "spread": 0.50,    "slippage": 0.25,    "commission": 0.0,     "unite": "point"},
    "NASDAQ100": {"margin": 2.00,   "spread": 1.00,    "slippage": 0.50,    "commission": 0.0,     "unite": "point"},
}
RRS = [1.0, 1.5, 2.0, 3.0]
SESSIONS = {"Londres": ("Europe/London", 8, 0), "New York": ("America/New_York", 9, 30)}
IS_END = pd.Timestamp("2024-01-01", tz="UTC")       # in-sample 2020-2023 / out-of-sample 2024+
CAPITAL_EUR, RISK_EUR = 10_000, 100                  # 1 % du capital de départ, fixe (sans composition)
RISK_PCT = 100 * RISK_EUR / CAPITAL_EUR


def load_m1(inst):
    files = sorted(glob.glob(os.path.join(ROOT, "data", inst, f"{inst}_M1_*.csv.gz")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    df = df[df["time"] >= "2020-01-01"]
    return df.reset_index(drop=True)


def to_m15(m1):
    g = m1.set_index("time").resample("15min", label="left", closed="left")
    m15 = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(),
                        "low": g["low"].min(), "close": g["close"].last(),
                        "n": g["open"].count()}).dropna()
    return m15.reset_index()


def last_fractal_index(flags):
    """Pour chaque i : indice du dernier fractal j <= i (ou -1)."""
    idx = np.where(flags, np.arange(len(flags)), -1)
    return np.maximum.accumulate(idx)


def session_starts(dates, tzname, hh, mm):
    """Heure UTC du début de la bougie de session pour chaque date locale (gère l'heure d'été locale)."""
    tz = ZoneInfo(tzname)
    out = []
    for d in dates:
        local = pd.Timestamp(year=d.year, month=d.month, day=d.day, hour=hh, minute=mm, tz=tz)
        out.append((d, local.tz_convert("UTC")))
    return out


def simulate(hi, lo, op, start, direction, sl, tp):
    """Premier toucher SL/TP à partir de la minute d'entrée. SL prioritaire si les deux dans la même minute.
    Renvoie (indice de sortie, prix de sortie, motif) ou None si toujours ouvert en fin de données."""
    n = len(hi)
    i, chunk = start, 2000
    while i < n:
        j = min(n, i + chunk)
        h, l, o = hi[i:j], lo[i:j], op[i:j]
        if direction == 1:
            hit_sl, hit_tp = l <= sl, h >= tp
        else:
            hit_sl, hit_tp = h >= sl, l <= tp
        any_hit = hit_sl | hit_tp
        if any_hit.any():
            k = int(np.argmax(any_hit))
            idx = i + k
            # gap : l'ouverture de la minute est déjà au-delà du niveau -> sortie à l'ouverture
            if hit_sl[k]:
                gap = (o[k] < sl) if direction == 1 else (o[k] > sl)
                return idx, (o[k] if gap and idx != start else sl), "SL"
            gap = (o[k] > tp) if direction == 1 else (o[k] < tp)
            return idx, (o[k] if gap and idx != start else tp), "TP"
        i = j
        chunk *= 2
    return None


def main(inst):
    cfg = INSTRUMENTS[inst]
    MARGIN = cfg["margin"]
    COST = cfg["spread"] + cfg["slippage"] + cfg["commission"]
    OUT = os.path.join(HERE, "results", inst)
    m1 = load_m1(inst)
    m15 = to_m15(m1)
    t15 = m15["time"].values
    pos15 = {t: k for k, t in enumerate(m15["time"])}
    m1_times = m1["time"].values
    hi, lo, op = m1["high"].values, m1["low"].values, m1["open"].values

    H, L = m15["high"].values, m15["low"].values
    # Fractal confirmé par 2 bougies de chaque côté (strict)
    fl = np.zeros(len(L), bool)
    fh = np.zeros(len(H), bool)
    fl[2:-2] = (L[2:-2] < L[1:-3]) & (L[2:-2] < L[:-4]) & (L[2:-2] < L[3:-1]) & (L[2:-2] < L[4:])
    fh[2:-2] = (H[2:-2] > H[1:-3]) & (H[2:-2] > H[:-4]) & (H[2:-2] > H[3:-1]) & (H[2:-2] > H[4:])
    last_fl, last_fh = last_fractal_index(fl), last_fractal_index(fh)

    dates = sorted({ts.date() for ts in m15["time"] if ts.dayofweek < 5})
    rows = []
    stats_signals = {"doji": 0, "bougie_absente": 0}
    for sess, (tzname, hh, mm) in SESSIONS.items():
        for d, t_sig in session_starts(dates, tzname, hh, mm):
            s = pos15.get(t_sig)
            e = pos15.get(t_sig + pd.Timedelta(minutes=15))
            if s is None or e is None:
                stats_signals["bougie_absente"] += 1
                continue
            o, c = m15.at[s, "open"], m15.at[s, "close"]
            if c == o:
                stats_signals["doji"] += 1
                continue
            direction = 1 if c > o else -1
            t_entry = m15.at[e, "time"]
            start = int(np.searchsorted(m1_times, t_entry.to_datetime64()))
            entry = op[start]
            sl_a = (L[s] - MARGIN) if direction == 1 else (H[s] + MARGIN)
            # Variante B : dernier fractal confirmé au plus tard à la clôture de la bougie signal (j + 2 <= s)
            j = last_fl[s - 2] if direction == 1 else last_fh[s - 2]
            sl_b, fallback = None, True
            if j >= 0:
                cand = (L[j] - MARGIN) if direction == 1 else (H[j] + MARGIN)
                if (direction == 1 and cand < entry) or (direction == -1 and cand > entry):
                    sl_b, fallback = cand, False
            if sl_b is None:
                sl_b = sl_a
            for variant, sl in (("A", sl_a), ("B", sl_b)):
                risk = (entry - sl) * direction
                if risk <= 0:  # variante A invalide si l'entrée a gappé au-delà du SL
                    continue
                for rr in RRS:
                    tp = entry + direction * rr * risk
                    res = simulate(hi, lo, op, start, direction, sl, tp)
                    if res is None:
                        continue
                    k, px, why = res
                    gross_r = (px - entry) * direction / risk
                    rows.append({
                        "session": sess, "date": str(d), "signal_utc": str(t_sig), "entry_utc": str(t_entry),
                        "exit_utc": str(pd.Timestamp(m1_times[k], tz="UTC")), "direction": "BUY" if direction == 1 else "SELL",
                        "sl_variant": variant, "rr": rr, "entry": round(entry, 6), "sl": round(sl, 6), "tp": round(tp, 6),
                        "exit": round(float(px), 6), "exit_reason": why, "risque_prix": round(risk, 6),
                        "fallback_A": bool(fallback) if variant == "B" else False,
                        "gross_r": gross_r, "net_r": gross_r - COST / risk,
                    })

    trades = pd.DataFrame(rows)
    for col in ("entry_utc", "exit_utc"):
        trades[col] = pd.to_datetime(trades[col], utc=True)
    os.makedirs(OUT, exist_ok=True)
    trades.to_csv(os.path.join(OUT, "trades.csv.gz"), index=False, float_format="%.6f")

    summary = {"instrument": inst,
               "parametres": {**cfg, "cout_total": COST, "capital_eur": CAPITAL_EUR, "risque_eur": RISK_EUR,
                              "periode": [str(m1["time"].iloc[0]), str(m1["time"].iloc[-1])]},
               "signaux": stats_signals, "combinaisons": []}

    def stats(t, col):
        if len(t) == 0:
            return None
        t = t.sort_values("exit_utc")
        r = t[col].values
        pos, neg = r[r > 0].sum(), -r[r < 0].sum()
        cum = np.cumsum(r)
        peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
        dd_r = float((peak - cum).max())
        eq = 100 + cum * RISK_PCT
        eq_peak = np.maximum(np.maximum.accumulate(eq), 100)
        dd_pct = float(((eq_peak - eq) / eq_peak).max() * 100)
        streak = best = 0
        for x in r:
            streak = streak + 1 if x < 0 else 0
            best = max(best, streak)
        return {"trades": int(len(r)), "win_rate": float((t["exit_reason"] == "TP").mean() * 100),
                "profit_factor": float(pos / neg) if neg > 0 else None, "esperance_r": float(r.mean()),
                "total_r": float(r.sum()), "max_dd_r": dd_r, "max_dd_pct": dd_pct, "pire_serie": int(best),
                "resultat_eur": float(r.sum() * RISK_EUR), "max_dd_eur": dd_r * RISK_EUR,
                "max_dd_pct_capital": dd_r * RISK_EUR / CAPITAL_EUR * 100}

    sess_sets = {"Londres": ["Londres"], "New York": ["New York"], "Les deux": ["Londres", "New York"]}
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    for sname, sl_list in sess_sets.items():
        for v in ("A", "B"):
            for rr in RRS:
                t = trades[trades["session"].isin(sl_list) & (trades["sl_variant"] == v) & (trades["rr"] == rr)]
                t = t.sort_values("exit_utc")
                combo = {"session": sname, "sl": v, "rr": rr,
                         "risque_median_prix": float(t["risque_prix"].median()),
                         "repli_A_pct": float(t["fallback_A"].mean() * 100) if v == "B" else None}
                for col, lab in (("gross_r", "brut"), ("net_r", "net")):
                    combo[lab] = {
                        "total": stats(t, col),
                        "in_sample": stats(t[t["entry_utc"] < IS_END], col),
                        "out_of_sample": stats(t[t["entry_utc"] >= IS_END], col),
                        "par_annee": {str(y): stats(g, col) for y, g in t.groupby(t["entry_utc"].dt.year)},
                        "par_session": {k: stats(g, col) for k, g in t.groupby("session")},
                        "par_direction": {k: stats(g, col) for k, g in t.groupby("direction")},
                        "par_jour": {jours[k]: stats(g, col) for k, g in t.groupby(pd.to_datetime(t["date"]).dt.dayofweek)},
                    }
                combo["equity"] = {
                    "dates": [x.strftime("%Y-%m-%d") for x in t["exit_utc"]],
                    "brut": np.round(np.cumsum(t["gross_r"].values), 2).tolist(),
                    "net": np.round(np.cumsum(t["net_r"].values), 2).tolist(),
                }
                summary["combinaisons"].append(combo)

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, ensure_ascii=False)
    print(f"{len(trades)} trades simulés. Signaux ignorés : {stats_signals}")


if __name__ == "__main__":
    for name in (sys.argv[1:] or list(INSTRUMENTS)):
        print("==", name)
        main(name.upper())
