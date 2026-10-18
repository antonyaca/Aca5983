"""Campagne 2 « 1 trade par jour » — UNE moyenne mobile ou UN indicateur classique (dossier moyennes_mobiles).
Règles fixées le 18/10/2026 AVANT tout calcul de résultat. 20 variantes = budget maximum. Paramètres standards uniquement
(20, 50, 200 ; ATR 14 ; RSI 14 ; MACD 12/26/9 ; Supertrend 10/3 ; EMA 9/21), aucun réglage après lecture des résultats.

CADRE COMMUN
- Données : M1 bid corrigées (lib.load, UTC). Marchés : les 10 de lib.MARKETS.
- Séances (heure locale, heure d'été comprise) : NASDAQ100 et SP500 09:30-16:00 New York ; FTSE100 08:00-16:30 Londres ;
  NIKKEI225 09:00-15:00 Tokyo ; XAUUSD, XAGUSD, EURUSD, GBPUSD, USDJPY, AUDUSD 08:00-17:00 Londres. Jours ouvrés.
  Séance retenue si sa 1re minute existe au plus 5 min après l'ouverture et si >= 90 % de ses minutes sont présentes
  (filtre qualité des données, comme lib.sessions_ny). day = date locale de la séance (même date civile pour Tokyo,
  Londres puis New York, dans cet ordre chronologique).
- Bougies : H1 = heures pleines UTC (= heures pleines locales), M15 = quarts d'heure UTC, agrégées depuis les M1 présentes.
  Journée (indicateurs journaliers) = clôture 17:00 New York (convention CFD/forex), journées >= 600 minutes seulement.
- Indicateurs (formules TradingView) : SMA = moyenne simple des clôtures ; EMA = ewm(span, adjust=False) ; ATR14 = moyenne
  de Wilder du True Range ; RSI14 de Wilder ; MACD 12/26/9 (EMA12 - EMA26, signal = EMA9 du MACD) ; Supertrend 10/3
  (ATR10 de Wilder, bandes hl2 +/- 3 ATR avec cliquet, comme ta.supertrend).
- Pas de look-ahead : un indicateur n'est lu que sur des bougies CLOSES. Tendance journalière = clôture de la dernière
  journée complète (terminée à 17:00 NY, avant la séance) comparée à sa SMA n : au-dessus -> achats seulement, en dessous ->
  ventes seulement, égalité ou valeur absente -> pas de trade. Valeurs H1 « à l'ouverture » = dernière H1 close à l'heure
  d'ouverture (ex. bougie 08:00-09:00 pour l'ouverture 09:30 NY). Un signal sur une bougie close à l'instant c est exécuté
  à l'ouverture de la 1re minute >= c (au plus 5 min de retard, sinon ignoré).
- Ordres : stop et objectif fixes posés à l'entrée. Stop prioritaire sur l'objectif dans la même minute (minute d'entrée
  comprise) ; gap au-delà du stop -> sortie à l'ouverture de la minute ; objectif exécuté au niveau exact. Sinon sortie à la
  clôture de la dernière minute de la séance (aucune position la nuit -> pas de swap).
- 1 R = |entrée - stop| (100 €). gross_r = sens x (sortie - entrée) / R ; cost_r = lib.COST x m / R avec m = 2 si la date
  New York de l'entrée est un jour d'annonce US (NFP, CPI, FOMC officiels 2020+ ; avant 2020, NFP = 1er vendredi du mois,
  même calendrier que la campagne métaux/forex), sinon 1.
- Candidats : par marché, un trade à la fois ; après une sortie pendant la minute j, le candidat suivant est le 1er signal
  entrant à une minute > j (t_out = fin de la minute de sortie). Signaux intraday : bougie close à c avec
  ouverture < c <= fin de séance - 60 min.
- Portefeuille : candidats des 10 marchés réunis ; lib.regle_anto prend le 1er signal du jour tous marchés confondus (ex
  aequo départagés dans l'ordre de lib.MARKETS) puis, s'il perd, le 1er signal entrant après sa sortie. Par marché :
  lib.regle_anto sur les seuls candidats du marché. Évaluation : lib.evaluate + lib.stats_jour sur les trades pris.

VARIANTES
A. Entrée à heure fixe = ouverture de la séance, dans le sens de la tendance (1 candidat par marché et par jour).
V01 Tendance SMA20 journalière ; stop 1 x ATR14 H1 ; objectif 1 R ; sinon sortie fin de séance.
V02 Tendance SMA50 journalière ; stop 1 x ATR14 H1 ; objectif 1 R.
V03 Tendance SMA20 journalière ; stop 0,5 x ATR14 journalier ; objectif 1 R.
V04 Tendance SMA50 journalière ; stop 0,5 x ATR14 journalier ; objectif 1 R.
V05 Tendance EMA200 H1 (clôture de la dernière H1 close vs son EMA200) ; stop 1 x ATR14 H1 ; objectif 1 R.
V06 Tendance EMA200 H1 ; stop 0,5 x ATR14 journalier ; objectif 1 R.
V07 Tendance SMA20 journalière ; stop 0,5 x ATR14 journalier ; pas d'objectif (sortie fin de séance ou stop).
V08 Tendance SMA20 journalière ; stop 0,5 x ATR14 journalier ; objectif 2 R.
V09 Tendance SMA200 journalière ; stop 0,5 x ATR14 journalier ; objectif 1 R.
B. Signal pendant la séance (le 1er de la séance est pris par la règle du jour ; les suivants servent au 2e trade).
V10 Croisement EMA9 / EMA21 en M15 (EMA9 passe au-dessus -> achat, au-dessous -> vente) dans le sens de la tendance
    SMA20 journalière ; stop 0,5 x ATR14 journalier ; objectif 1 R.
V11 Même signal ; stop 1 x ATR14 H1 (dernière H1 close à l'entrée) ; objectif 1 R.
V12 Repli sur l'EMA20 H1 en tendance EMA200 H1 : achat si la H1 close a clôture > EMA200, EMA20 > EMA200, plus bas <=
    EMA20 et clôture > EMA20 ; vente symétrique ; stop 0,5 x ATR14 journalier ; objectif 1 R.
V13 Retournement du Supertrend 10/3 H1 (dans le sens du nouveau Supertrend, sans autre filtre) ; stop = ligne du
    Supertrend de la bougie signal (pas de trade si l'entrée est déjà au-delà) ; objectif 1 R.
V14 Même signal, seulement dans le sens de la tendance SMA20 journalière.
V15 Croisement MACD 12/26/9 H1 (MACD passe au-dessus de son signal -> achat, au-dessous -> vente), sans filtre ; stop 0,5 x
    ATR14 journalier ; objectif 1 R.
V16 Même signal, seulement dans le sens de la tendance SMA20 journalière.
V17 RSI14 H1 qui sort d'une zone dans le sens de la tendance SMA20 journalière : achat quand il repasse au-dessus de 30
    (précédente < 30 <= actuelle) en tendance haussière ; vente quand il repasse sous 70 en tendance baissière ; stop
    0,5 x ATR14 journalier ; objectif 1 R.
V18 RSI14 H1, lecture « momentum » : achat quand il franchit 70 à la hausse en tendance haussière ; vente quand il
    franchit 30 à la baisse en tendance baissière ; stop 0,5 x ATR14 journalier ; objectif 1 R.
V19 Clôture H1 qui recroise l'EMA20 H1 (au-dessus -> achat, au-dessous -> vente) dans le sens de la tendance SMA20
    journalière ; stop 0,5 x ATR14 journalier ; objectif 1 R.
C. Témoin sans indicateur (mesure ce qu'apporte la moyenne mobile).
V20 Achat systématique à l'ouverture de la séance ; stop 0,5 x ATR14 journalier ; objectif 1 R.
"""
import gc
import importlib.util
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CAMP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAMP)
import lib  # noqa: E402

SESS = {"NASDAQ100": ("America/New_York", 570, 960), "SP500": ("America/New_York", 570, 960),
        "FTSE100": ("Europe/London", 480, 990), "NIKKEI225": ("Asia/Tokyo", 540, 900)}
for _m in ("XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD"):
    SESS[_m] = ("Europe/London", 480, 1020)
MAXLAG = 5          # retard maximal d'exécution (minutes)
MIN_FRAC = 0.9      # part minimale des minutes de la séance présentes
RANK = {m: i for i, m in enumerate(lib.MARKETS)}

# ---------- calendrier des annonces US (même source et même approximation que metaux_forex/run.py)
_spec = importlib.util.spec_from_file_location(
    "ev", os.path.join(os.path.dirname(CAMP), "events", "backtest.py"))
_ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ev)
_mac = set(pd.to_datetime(list(_ev.NFP) + list(_ev.CPI) + list(_ev.FOMC)))
for _y in range(2010, 2020):
    for _mo in range(1, 13):
        _d = pd.Timestamp(_y, _mo, 1)
        _mac.add(_d + pd.Timedelta(days=(4 - _d.dayofweek) % 7))
MACRO = {int((d - pd.Timestamp("1970-01-01")).days) for d in _mac}

RULES = {
    "V01": dict(kind="open", trend="sma20", sl="atrh1", tp=1.0),
    "V02": dict(kind="open", trend="sma50", sl="atrh1", tp=1.0),
    "V03": dict(kind="open", trend="sma20", sl="atrd05", tp=1.0),
    "V04": dict(kind="open", trend="sma50", sl="atrd05", tp=1.0),
    "V05": dict(kind="open", trend="ema200h1", sl="atrh1", tp=1.0),
    "V06": dict(kind="open", trend="ema200h1", sl="atrd05", tp=1.0),
    "V07": dict(kind="open", trend="sma20", sl="atrd05", tp=None),
    "V08": dict(kind="open", trend="sma20", sl="atrd05", tp=2.0),
    "V09": dict(kind="open", trend="sma200", sl="atrd05", tp=1.0),
    "V10": dict(kind="m15", sig="ema921", trend="sma20", sl="atrd05", tp=1.0),
    "V11": dict(kind="m15", sig="ema921", trend="sma20", sl="atrh1", tp=1.0),
    "V12": dict(kind="h1", sig="pullback20", trend=None, sl="atrd05", tp=1.0),
    "V13": dict(kind="h1", sig="st", trend=None, sl="st", tp=1.0),
    "V14": dict(kind="h1", sig="st", trend="sma20", sl="st", tp=1.0),
    "V15": dict(kind="h1", sig="macd", trend=None, sl="atrd05", tp=1.0),
    "V16": dict(kind="h1", sig="macd", trend="sma20", sl="atrd05", tp=1.0),
    "V17": dict(kind="h1", sig="rsi_zone", trend="sma20", sl="atrd05", tp=1.0),
    "V18": dict(kind="h1", sig="rsi_mom", trend="sma20", sl="atrd05", tp=1.0),
    "V19": dict(kind="h1", sig="cross20", trend="sma20", sl="atrd05", tp=1.0),
    "V20": dict(kind="open", trend="long", sl="atrd05", tp=1.0),
}
LABELS = {
    "V01": "Ouverture, SMA20 J, SL 1 ATR H1, TP 1R", "V02": "Ouverture, SMA50 J, SL 1 ATR H1, TP 1R",
    "V03": "Ouverture, SMA20 J, SL 0,5 ATR J, TP 1R", "V04": "Ouverture, SMA50 J, SL 0,5 ATR J, TP 1R",
    "V05": "Ouverture, EMA200 H1, SL 1 ATR H1, TP 1R", "V06": "Ouverture, EMA200 H1, SL 0,5 ATR J, TP 1R",
    "V07": "Ouverture, SMA20 J, SL 0,5 ATR J, sans TP", "V08": "Ouverture, SMA20 J, SL 0,5 ATR J, TP 2R",
    "V09": "Ouverture, SMA200 J, SL 0,5 ATR J, TP 1R", "V10": "EMA9/21 M15 + SMA20 J, SL 0,5 ATR J",
    "V11": "EMA9/21 M15 + SMA20 J, SL 1 ATR H1", "V12": "Repli EMA20 H1 (EMA200 H1), SL 0,5 ATR J",
    "V13": "Supertrend 10/3 H1, SL ligne ST", "V14": "Supertrend 10/3 H1 + SMA20 J, SL ligne ST",
    "V15": "MACD H1, SL 0,5 ATR J", "V16": "MACD H1 + SMA20 J, SL 0,5 ATR J",
    "V17": "RSI14 H1 sortie 30/70 + SMA20 J", "V18": "RSI14 H1 momentum 70/30 + SMA20 J",
    "V19": "Clôture H1 x EMA20 H1 + SMA20 J", "V20": "Témoin : achat à l'ouverture, SL 0,5 ATR J",
}
COLS = ["instrument", "day", "t_in", "t_out", "d", "entry", "stop", "tp", "exit", "R", "gross_r", "cost_r", "sortie"]


# ---------------------------------------------------------------- indicateurs (formules TradingView)
def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


def rma(x, n):
    """Moyenne de Wilder (ta.rma), amorcée sur la 1re valeur."""
    return pd.Series(x).ewm(alpha=1.0 / n, adjust=False).mean().values


def true_range(h, l, c):
    pc = np.r_[np.nan, c[:-1]]
    return np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc)))


def rsi(c, n=14):
    d = np.diff(c, prepend=c[0])
    au, ad = rma(np.clip(d, 0, None), n), rma(np.clip(-d, 0, None), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(ad == 0, 100.0, 100.0 - 100.0 / (1.0 + au / ad))


def supertrend(h, l, c, n=10, f=3.0):
    """ta.supertrend : renvoie (ligne, sens) avec sens +1 = haussier (ligne = bande basse), -1 = baissier."""
    atr = rma(true_range(h, l, c), n)
    hl2 = (h + l) / 2
    ub, lb = hl2 + f * atr, hl2 - f * atr
    N = len(c)
    fub, flb = ub.copy(), lb.copy()
    dirn = np.empty(N, np.int8)
    line = np.empty(N)
    dirn[0], line[0] = -1, ub[0]
    for i in range(1, N):
        flb[i] = lb[i] if (lb[i] > flb[i - 1] or c[i - 1] < flb[i - 1]) else flb[i - 1]
        fub[i] = ub[i] if (ub[i] < fub[i - 1] or c[i - 1] > fub[i - 1]) else fub[i - 1]
        if dirn[i - 1] == -1:                      # la ligne précédente était la bande haute
            dirn[i] = 1 if c[i] > fub[i] else -1
        else:
            dirn[i] = -1 if c[i] < flb[i] else 1
        line[i] = flb[i] if dirn[i] == 1 else fub[i]
    return line, dirn


def prev(x):
    return np.r_[np.nan, x[:-1]]


def to_min(idx):
    return idx.tz_localize(None).values.astype("datetime64[m]").astype(np.int64)


# ---------------------------------------------------------------- marché
class Market:
    def __init__(self, inst):
        self.inst = inst
        tz, self.o_hm, self.e_hm = SESS[inst]
        df = lib.load(inst, "UTC")
        t = pd.DatetimeIndex(df["time"])
        self.O, self.H, self.L, self.C = (df[c].values.astype(float) for c in ("open", "high", "low", "close"))
        del df
        self.utc = to_min(t)
        self.ny = to_min(t.tz_convert("America/New_York"))
        self.loc = self.ny if tz == "America/New_York" else to_min(t.tz_convert(tz))
        del t
        self.N = len(self.utc)
        self._daily()
        self._h1()
        self._m15()
        self._sessions()

    def _bars(self, width):
        k = self.utc // width
        st = np.r_[0, np.flatnonzero(np.diff(k)) + 1]
        en = np.r_[st[1:], len(k)]
        return ((k[st] + 1) * width, np.maximum.reduceat(self.H, st), np.minimum.reduceat(self.L, st), self.C[en - 1])

    def _daily(self):
        td = (self.ny + 420) // 1440                       # journée de trading (clôture 17:00 NY)
        self.td = td
        st = np.r_[0, np.flatnonzero(np.diff(td)) + 1]
        en = np.r_[st[1:], len(td)]
        keep = (en - st) >= 600
        h = np.maximum.reduceat(self.H, st)[keep]
        l = np.minimum.reduceat(self.L, st)[keep]
        c = self.C[en - 1][keep]
        self.d_ids, self.d_close = td[st][keep], c
        self.d_sma = {n: pd.Series(c).rolling(n).mean().values for n in (20, 50, 200)}
        self.d_atr = rma(true_range(h, l, c), 14)

    def _h1(self):
        ct, h, l, c = self._bars(60)
        self.h_ct, self.h_c = ct, c
        e20, e200 = ema(c, 20), ema(c, 200)
        self.h_ema200 = e200
        self.h_atr = rma(true_range(h, l, c), 14)
        r = rsi(c, 14)
        macd = ema(c, 12) - ema(c, 26)
        sig = ema(macd, 9)
        self.h_stl, std = supertrend(h, l, c, 10, 3.0)
        std_p = np.r_[std[0], std[:-1]]
        mp, sp_, rp, cp, ep = prev(macd), prev(sig), prev(r), prev(c), prev(e20)
        self.h_sig = {
            "pullback20": np.where((c > e200) & (e20 > e200) & (l <= e20) & (c > e20), 1,
                                   np.where((c < e200) & (e20 < e200) & (h >= e20) & (c < e20), -1, 0)),
            "st": np.where(std != std_p, std, 0).astype(int),
            "macd": np.where((macd > sig) & (mp <= sp_), 1, np.where((macd < sig) & (mp >= sp_), -1, 0)),
            "rsi_zone": np.where((rp < 30) & (r >= 30), 1, np.where((rp > 70) & (r <= 70), -1, 0)),
            "rsi_mom": np.where((rp < 70) & (r >= 70), 1, np.where((rp > 30) & (r <= 30), -1, 0)),
            "cross20": np.where((c > e20) & (cp <= ep), 1, np.where((c < e20) & (cp >= ep), -1, 0)),
        }
        self.h_k, self.h_lag = self._entry_idx(ct)

    def _m15(self):
        ct, h, l, c = self._bars(15)
        e9, e21 = ema(c, 9), ema(c, 21)
        p9, p21 = prev(e9), prev(e21)
        self.q_ct = ct
        self.q_sig = np.where((e9 > e21) & (p9 <= p21), 1, np.where((e9 < e21) & (p9 >= p21), -1, 0))
        self.q_k, self.q_lag = self._entry_idx(ct)

    def _entry_idx(self, ct):
        k = np.searchsorted(self.utc, ct, "left")
        kc = np.minimum(k, self.N - 1)
        lag = np.where(k < self.N, self.utc[kc] - ct, 10 ** 9)
        return kc, lag

    def _sessions(self):
        loc = self.loc
        days = np.unique(loc // 1440)
        days = days[((days + 3) % 7) < 5]                  # 1970-01-01 = jeudi -> lundi = 0
        a, b = days * 1440 + self.o_hm, days * 1440 + self.e_hm
        i0, iE = np.searchsorted(loc, a), np.searchsorted(loc, b)
        i0c = np.minimum(i0, self.N - 1)
        ok = (i0 < self.N) & ((loc[i0c] - a) <= MAXLAG) & ((iE - i0) >= MIN_FRAC * (self.e_hm - self.o_hm))
        days, a, b, i0, iE = days[ok], a[ok], b[ok], i0[ok], iE[ok]
        off = loc[i0] - self.utc[i0]                        # décalage local - UTC du jour
        o_utc, e_utc = a - off, b - off
        pos = np.searchsorted(self.d_ids, self.td[i0], "left") - 1   # dernière journée complète AVANT la séance
        self.S = dict(n=len(days), day=days, i0=i0, iE=iE, pos=pos,
                      ib_open=np.searchsorted(self.h_ct, self.utc[i0], "right") - 1,
                      lo_h=np.searchsorted(self.h_ct, o_utc, "right"), hi_h=np.searchsorted(self.h_ct, e_utc - 60, "right"),
                      lo_q=np.searchsorted(self.q_ct, o_utc, "right"), hi_q=np.searchsorted(self.q_ct, e_utc - 60, "right"))

    def trend(self, s, key):
        if key is None:
            return None
        if key == "long":
            return 1
        if key == "ema200h1":
            ib = self.S["ib_open"][s]
            v = self.h_c[ib] - self.h_ema200[ib] if ib >= 0 else np.nan
        else:
            pos = self.S["pos"][s]
            v = self.d_close[pos] - self.d_sma[int(key[3:])][pos] if pos >= 0 else np.nan
        return int(np.sign(v)) if np.isfinite(v) else 0


# ---------------------------------------------------------------- simulation
def simulate(O, H, L, C, k, iE, d, stop, tp):
    """Entrée à O[k] ; stop prioritaire (minute d'entrée comprise) ; gap au-delà du stop -> ouverture ; objectif au niveau ;
    sinon clôture de la minute iE-1. Renvoie (prix de sortie, indice de la minute de sortie, type)."""
    lo, hi = L[k:iE], H[k:iE]
    n = iE - k
    if d == 1:
        hs = np.flatnonzero(lo <= stop)
        ht = np.flatnonzero(hi >= tp) if tp is not None else hs[:0]
    else:
        hs = np.flatnonzero(hi >= stop)
        ht = np.flatnonzero(lo <= tp) if tp is not None else hs[:0]
    js = int(hs[0]) if len(hs) else n
    jt = int(ht[0]) if len(ht) else n
    if js < n and js <= jt:
        j = k + js
        o = O[j]
        return (o if (j > k and (o - stop) * d < 0) else stop), j, "SL"
    if jt < n:
        return tp, k + jt, "TP"
    return C[iE - 1], iE - 1, "FIN"


def gen(m, cfg):
    S = m.S
    kind, sl, tpm, tkey = cfg["kind"], cfg["sl"], cfg["tp"], cfg.get("trend")
    if kind == "h1":
        sig_all, kk, lag, lo_a, hi_a = m.h_sig[cfg["sig"]], m.h_k, m.h_lag, S["lo_h"], S["hi_h"]
    elif kind == "m15":
        sig_all, kk, lag, lo_a, hi_a = m.q_sig, m.q_k, m.q_lag, S["lo_q"], S["hi_q"]
    cost = lib.COST[m.inst]
    rows = []
    for s in range(S["n"]):
        i0, iE, pos = int(S["i0"][s]), int(S["iE"][s]), int(S["pos"][s])
        if pos < 0:
            continue
        tr = m.trend(s, tkey)
        if kind == "open":
            if not tr:
                continue
            sigs = [(i0, tr, -1)]
        else:
            if tkey is not None and not tr:
                continue
            bs = np.arange(lo_a[s], hi_a[s])
            bs = bs[sig_all[bs] != 0]
            sigs = []
            for bb in bs:
                d = int(sig_all[bb])
                if (tkey is not None and d != tr) or kk[bb] >= iE or lag[bb] > MAXLAG:
                    continue
                sigs.append((int(kk[bb]), d, int(bb)))
        nxt = i0
        for k, d, bb in sigs:
            if k < nxt:
                continue
            entry = m.O[k]
            if sl == "atrd05":
                stop = entry - d * 0.5 * m.d_atr[pos]
            elif sl == "atrh1":
                ib = int(np.searchsorted(m.h_ct, m.utc[k], "right")) - 1
                stop = entry - d * m.h_atr[ib] if ib >= 0 else np.nan
            else:                                          # ligne du Supertrend de la bougie signal
                stop = m.h_stl[bb]
            risk = (entry - stop) * d
            if not np.isfinite(risk) or risk <= 0:
                continue
            tp = entry + d * tpm * risk if tpm else None
            px, j, why = simulate(m.O, m.H, m.L, m.C, k, iE, d, stop, tp)
            mult = 2.0 if int(m.ny[k] // 1440) in MACRO else 1.0
            rows.append((m.inst, int(S["day"][s]), int(m.utc[k]), int(m.utc[j]) + 1, d, entry, stop,
                         np.nan if tp is None else tp, px, risk, d * (px - entry) / risk, cost * mult / risk, why))
            nxt = j + 1
    t = pd.DataFrame(rows, columns=COLS)
    t["day"] = pd.to_datetime(t["day"], unit="D")
    t["t_in"] = pd.to_datetime(t["t_in"], unit="m")
    t["t_out"] = pd.to_datetime(t["t_out"], unit="m")
    return t


# ---------------------------------------------------------------- évaluation
def regles(key):
    doc = __doc__.split("\nVARIANTES\n")[1]
    out, cur, head = {}, None, ""
    for ln in doc.splitlines():
        if ln[:1] == "V" and ln[1:3].isdigit():
            cur = ln[:3]
            out[cur] = head + " | " + ln
        elif ln.startswith("    ") and cur:
            out[cur] += " " + ln.strip()
        elif ln.strip():
            head, cur = ln.strip(), None
    return out[key]


def entry(v, scope, cand, taken):
    r = lib.evaluate(taken, f"{v} {LABELS[v]} [{scope}]")
    r["variante"], r["portee"], r["regles"] = v, scope, regles(v)
    r["jour"] = lib.stats_jour(taken)
    c = cand[cand["day"] >= lib.START]
    tt = taken[taken["day"] >= lib.START]
    yrs = (lib.DATA_END - lib.START).days / 365.25
    r["candidats"] = int(len(c))
    r["trades_par_an"] = round(len(tt) / yrs, 1)
    r["cout_median_r"] = round(float(tt["cost_r"].median()), 4) if len(tt) else None
    n_days = tt["day"].nunique()
    r["jours_avec_2_trades_pct"] = round(float((len(tt) - n_days) / n_days * 100), 1) if n_days else None
    r["sorties_pct"] = {k: round(float(x) * 100, 1) for k, x in tt["sortie"].value_counts(normalize=True).items()}
    if scope == "PORTEFEUILLE":
        r["trades_par_instrument"] = {k: int(x) for k, x in tt["instrument"].value_counts().items()}
    return r


def selftest():
    """Contrôle du moteur sur des barres synthétiques (aucune donnée de marché)."""
    O = np.array([100, 100, 101, 99, 103, 100.0])
    H = np.array([100.5, 101, 102, 99.5, 104, 100.5])
    L = np.array([99.5, 99.8, 100.5, 97, 102, 99.5])
    C = np.array([100, 101, 101.5, 98, 103.5, 100.0])
    # achat à 100, stop 99, objectif 101 : minute 1 touche l'objectif (H=101), le stop n'est pas touché (L=99.8)
    assert simulate(O, H, L, C, 0, 6, 1, 99.0, 101.0) == (101.0, 1, "TP")
    # achat à 100, stop 99.6, objectif 101 : minute 0 touche le stop (L=99.5) -> stop prioritaire dès la minute d'entrée
    assert simulate(O, H, L, C, 0, 6, 1, 99.6, 101.0) == (99.6, 0, "SL")
    # achat à 101 (minute 2), stop 100, objectif 103.5 : gap à 99 en minute 3 -> sortie à l'ouverture 99
    assert simulate(O, H, L, C, 2, 6, 1, 100.0, 103.5) == (99.0, 3, "SL")
    # vente à 101 (minute 2), stop 104.5, objectif 97.5 : minute 3 touche 97 -> objectif au niveau exact
    assert simulate(O, H, L, C, 2, 6, -1, 104.5, 97.5) == (97.5, 3, "TP")
    # vente à 103 (minute 4), stop 105, objectif 99 : rien touché -> clôture de la dernière minute (100)
    assert simulate(O, H, L, C, 4, 6, -1, 105.0, 99.0) == (100.0, 5, "FIN")
    # achat à 103 (minute 4), stop 102.5 et objectif 103.9 touchés dans la même minute -> stop
    assert simulate(O, H, L, C, 4, 6, 1, 102.5, 103.9) == (102.5, 4, "SL")
    # sans objectif
    assert simulate(O, H, L, C, 0, 6, 1, 90.0, None) == (100.0, 5, "FIN")
    # Supertrend : série montante puis chute -> le sens doit passer à -1
    c = np.r_[np.linspace(100, 120, 60), np.linspace(120, 90, 30)]
    line, dirn = supertrend(c + 0.5, c - 0.5, c, 10, 3.0)
    assert dirn[59] == 1 and dirn[-1] == -1 and line[59] < c[59] and line[-1] > c[-1]
    print("selftest OK")


def main():
    cands = {v: [] for v in RULES}
    for inst in lib.MARKETS:
        t0 = time.time()
        m = Market(inst)
        for v, cfg in RULES.items():
            cands[v].append(gen(m, cfg))
        print(f"{inst:10} séances {m.S['n']:5d}  ({time.time() - t0:.0f} s)", flush=True)
        del m
        gc.collect()
    os.makedirs(os.path.join(HERE, "trades"), exist_ok=True)
    res = []
    for v in RULES:
        allc = pd.concat([x for x in cands[v] if len(x)], ignore_index=True)
        allc["rang"] = allc["instrument"].map(RANK)
        allc = allc.sort_values(["day", "t_in", "rang"], kind="stable").reset_index(drop=True)
        allc.drop(columns="rang").to_csv(os.path.join(HERE, "trades", f"{v}.csv.gz"), index=False, float_format="%.6f")
        for scope in ["PORTEFEUILLE"] + lib.MARKETS:
            c = allc if scope == "PORTEFEUILLE" else allc[allc["instrument"] == scope]
            taken = lib.regle_anto(c)
            r = entry(v, scope, c, taken)
            res.append(r)
            print(lib.line(r), "|", lib.line_jour(r["jour"]) if r["jour"] else "-", flush=True)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
