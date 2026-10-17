# Ichimoku 9/26/52 — positions de plusieurs jours (17/10/2026)

`python3 backtests/ichimoku/backtest.py` ; règles en tête du script. 5 marchés × M15/H1/H4 × 4 setups × 2 sorties = 120 variantes.

**DAX exclu** : données HistData corrompues en 2021-2023 (cours entre 3 200 et 4 400, niveau de l'Euro Stoxx 50, puis saut à 16 000
le 03/12/2023). Les résultats DAX géants (jusqu'à +900 R sur un trade) sont des artefacts.

Hors DAX, 5 variantes sur 96 passent le critère — de l'ordre de ce que le hasard donne sur 96 essais, aucune avec t ≥ 2 :
- Or H4 croisement TK, sortie Kijun : 183 trades, +9 386 €, PF 1,80 ; mais négatif sans les 5 meilleurs trades (−0,06 R).
- Or H1 cinq conditions, sortie Kijun : 883 trades, +8 099 €, t = 1,74 ; achats +0,29 R, ventes −0,12 R ; 2021-2023 négatifs.
- Or H4 cinq conditions, sortie Kijun : +3 293 € ; négatif sans les 5 meilleurs trades.
- S&P 500 H4 cassure du nuage, TP 1:2 : 91 trades, +1 941 €.
- Nasdaq H1 cassure du nuage, sortie Kijun : +3 409 €, OOS +0,032 R.
Lecture : les résultats « or » reflètent surtout la hausse de l'or 2024-2026 (achats gagnants, ventes perdantes). Pas d'edge robuste.
