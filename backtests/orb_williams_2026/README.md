# ORB 30 min + Williams k = 0,5 — Nasdaq (06/11/2026)

Règles de `tradingview/orb_williams_nasdaq.pine`, données M1 2011 → 30/10/2026, coût 1,5 pt, 100 € par R.
Lancement : `python3 backtest.py <racine du repo> trades.csv`

| | Trades | €/an | DD max | Années + |
|---|---|---|---|---|
| Williams | 2 817 | +814 | 7 697 | 12/16 |
| ORB 30 min | 2 025 | −70 | 8 893 | 9/16 |
| Combiné | 4 842 | +744 | 15 679 | 11/16 |

- Williams : brut +0,09 R (2011-2018) et +0,12 R (2019-2026) ; les frais fixes mangeaient tout avant 2019 (Nasdaq bas).
- ORB : brut +0,02 R en 2011-2018, positif seulement en 2019-2026, à plat sur les 12 derniers mois → **retiré**.
- Williams + RSI2 + 3 baisses (fichiers de `campagne/verification`) : +2 086 €/an, DD 4 996 €, 14/16 années + ;
  2019-2026 : +3 404 €/an, DD 1 859 €. Semaines ≥ +500 € : 6 %.
- Nouvel indicateur : `tradingview/williams_swing_us.pine`.
