"""Exemples visuels (22/10/2026) : 2 trades Williams Nasdaq (gagnant / perdant) + 1 trade RSI2, sur données réelles."""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); sys.path.insert(0, C)
import lib  # noqa

INK, MUTED, GRID = "#1f2328", "#6b7280", "#e5e7eb"
UP, DOWN = "#2f6fbb", "#9aa3ad"          # bougies : hausse bleue, baisse grise (neutres)
ENTRY, STOP, TP = "#1d4ed8", "#c2410c", "#15803d"
df = lib.load("NASDAQ100", "America/New_York")


def candles(ax, x, o, h, l, c, w=0.6):
    for xi, oi, hi, li, ci in zip(x, o, h, l, c):
        col = UP if ci >= oi else DOWN
        ax.plot([xi, xi], [li, hi], color=col, lw=1)
        ax.add_patch(plt.Rectangle((xi - w / 2, min(oi, ci)), w, max(abs(ci - oi), 1e-9), color=col))


def williams(day, fname, titre):
    days = sorted(df[(df.hm >= 570) & (df.hm < 960)].day.unique())
    k = days.index(np.datetime64(day))
    prev = df[(df.day == days[k - 1]) & (df.hm >= 570) & (df.hm < 960)]
    g = df[(df.day == days[k]) & (df.hm >= 570) & (df.hm < 960)].copy()
    amp = prev.high.max() - prev.low.min(); op = g.open.iloc[0]; lvl = op + amp / 2; R = lvl - op; half = lvl + R / 2
    # replay minute par minute
    hm, O, Hh, L, Cc = (g[c].values for c in ("hm", "open", "high", "low", "close"))
    ke = int(np.argmax(Hh >= lvl)); entry = max(O[ke], lvl); stop = op; kp = kx = None; res = None
    for j in range(ke, len(hm)):
        if L[j] <= stop:
            kx, px = j, stop; break
        if kp is None and Hh[j] >= entry + R / 2:
            kp = j; stop = entry; continue
    if kx is None:
        kx, px = len(hm) - 1, Cc[-1]
    gross = (0.5 * 0.5 + 0.5 * (px - entry) / R) if kp is not None else (px - entry) / R
    # bougies M5 en heure de Paris
    g["paris"] = g.time.dt.tz_convert("Europe/Paris")
    m5 = g.set_index("paris")[["open", "high", "low", "close"]].resample("5min").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    x = np.arange(len(m5))
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=130)
    candles(ax, x, m5.open, m5.high, m5.low, m5.close)
    def xi(j):
        t = g.paris.iloc[j].floor("5min"); return int(np.searchsorted(m5.index, t))
    ax.axhline(op, color=STOP, lw=1.5, ls="--"); ax.text(len(x) + 0.5, op, f" STOP = ouverture\n {op:,.0f}".replace(",", " "), color=STOP, va="center", fontsize=9)
    ax.axhline(lvl, color=ENTRY, lw=1.5); ax.text(len(x) + 0.5, lvl, f" ACHAT = ouverture + amplitude/2\n {lvl:,.0f}".replace(",", " "), color=ENTRY, va="center", fontsize=9)
    ax.axhline(entry + R / 2, color=TP, lw=1.5, ls=":"); ax.text(len(x) + 0.5, entry + R / 2, f" +0,5 R : on encaisse 50 %\n {entry + R/2:,.0f}".replace(",", " "), color=TP, va="center", fontsize=9)
    ax.scatter([xi(ke)], [entry], s=90, color=ENTRY, zorder=5, marker="^"); ax.annotate("① achat", (xi(ke), entry), xytext=(-60, 25), textcoords="offset points", color=INK, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED))
    if kp is not None:
        ax.scatter([xi(kp)], [entry + R / 2], s=80, color=TP, zorder=5); ax.annotate("② moitié encaissée,\nstop remonté à l'entrée", (xi(kp), entry + R / 2), xytext=(40, -45), textcoords="offset points", color=INK, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED))
    lab = "③ stop touché" if (kx < len(hm) - 1) else "③ fermeture à 21h59"
    ax.scatter([xi(kx)], [px], s=80, color=STOP if px <= op + 1e-6 else INK, zorder=5); ax.annotate(lab, (xi(kx), px), xytext=(-40, -35), textcoords="offset points", color=INK, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED))
    ticks = [i for i, t in enumerate(m5.index) if t.minute == 0 or (t.hour, t.minute) == (15, 30)]
    ax.set_xticks(ticks); ax.set_xticklabels([m5.index[i].strftime("%Hh%M") for i in ticks], color=MUTED, fontsize=9)
    ax.tick_params(axis="y", colors=MUTED, labelsize=9); ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID); ax.set_xlim(-1, len(x) + 14)
    eur = gross * 100
    ax.set_title(f"{titre} — {pd.Timestamp(day):%d/%m/%Y}\nAmplitude de la veille {amp:,.0f} pts → niveau à {amp/2:,.0f} pts au-dessus de l'ouverture · "
                 f"Résultat : {gross:+.2f} R soit {eur:+.0f} € pour 100 € de risque (avant frais)".replace(",", " "),
                 loc="left", fontsize=11, color=INK)
    ax.set_xlabel("Nasdaq 100, bougies M5, heure de Paris", color=MUTED, fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(H, fname)); plt.close(fig)
    return gross


def rsi2(day, fname):
    s = df[(df.hm >= 570) & (df.hm <= 955)].groupby("day").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
    c = s.c; d = c.diff()
    rsi = 100 - 100 / (1 + d.clip(lower=0).ewm(alpha=0.5, adjust=False).mean() / (-d.clip(upper=0)).ewm(alpha=0.5, adjust=False).mean())
    sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
    i = s.index.get_loc(pd.Timestamp(day)); j = i + 1
    while not c.iloc[j] > sma5.iloc[j]:
        j += 1
    w = s.iloc[i - 25:j + 8]; x = np.arange(len(w)); off = i - 25
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 6.4), dpi=130, gridspec_kw={"height_ratios": [3, 1]}, sharex=True)
    candles(ax, x, w.o, w.h, w.l, w.c)
    ax.plot(x, sma5.iloc[off:off + len(w)], color=TP, lw=1.6, label="SMA 5 (sortie)")
    ax.plot(x, sma200.iloc[off:off + len(w)], color=MUTED, lw=1.6, ls="--", label="SMA 200 (filtre : prix au-dessus)")
    ax.scatter([i - off], [c.iloc[i]], s=110, marker="^", color=ENTRY, zorder=5)
    ax.annotate(f"① RSI(2) = {rsi.iloc[i]:.0f} (< 20) et prix > SMA 200\n→ achat à 21h55 à {c.iloc[i]:,.0f}".replace(",", " "), (i - off, c.iloc[i]), xytext=(-170, -55), textcoords="offset points", fontsize=10, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.scatter([j - off], [c.iloc[j]], s=90, color=TP, zorder=5)
    ax.annotate(f"② clôture au-dessus de la SMA 5\n→ vente à 21h55 à {c.iloc[j]:,.0f}".replace(",", " "), (j - off, c.iloc[j]), xytext=(30, -70), textcoords="offset points", fontsize=10, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED))
    pc = c.shift(); atr = pd.concat([s.h - s.l, (s.h - pc).abs(), (s.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean()
    g = (c.iloc[j] - c.iloc[i]) / atr.iloc[i]
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=MUTED)
    ax2.plot(x, rsi.iloc[off:off + len(w)], color=ENTRY, lw=1.6); ax2.axhline(20, color=STOP, lw=1, ls="--"); ax2.text(len(x) - 0.5, 22, "seuil 20", color=STOP, fontsize=9, ha="right")
    ax2.set_ylim(0, 100); ax2.set_ylabel("RSI (2)", color=MUTED, fontsize=9)
    ax2.text(0, 2, "Chaque passage sous 20 (avec prix > SMA 200) est un signal ; un seul trade est montré ici.", color=MUTED, fontsize=8.5)
    for a in (ax, ax2):
        a.tick_params(colors=MUTED, labelsize=9); a.grid(axis="y", color=GRID, lw=0.8); a.set_axisbelow(True)
        for sp in ("top", "right", "left"): a.spines[sp].set_visible(False)
        a.spines["bottom"].set_color(GRID)
    ticks = list(range(0, len(w), 5)); ax2.set_xticks(ticks); ax2.set_xticklabels([w.index[k].strftime("%d/%m") for k in ticks])
    ax.set_title(f"Exemple 3 — RSI2 Nasdaq (graphique journalier) · tenu {j - i} séances · résultat {g:+.2f} R soit {g*100:+.0f} € pour 100 € de risque (avant frais)",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout(); fig.savefig(os.path.join(H, fname)); plt.close(fig)


print(williams("2026-09-21", "exemple1_williams_gagnant.png", "Exemple 1 — Williams Nasdaq, trade gagnant"))
print(williams("2026-07-02", "exemple2_williams_perdant.png", "Exemple 2 — Williams Nasdaq, trade perdant"))
rsi2("2026-09-10", "exemple3_rsi2.png")
