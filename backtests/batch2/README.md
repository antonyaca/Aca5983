# Lot 2 — range asiatique, ORB Londres, gap fade (16/10/2026)

Lancer : `python3 backtests/batch2/strategies.py`. Règles détaillées en tête du script.
Critère fixé avant les tests : E nette > 0 en IS et en OOS, PF net global ≥ 1,10, E nette OOS > 0 avec frais doublés.

**Résultat : aucune des 16 variantes ne passe le critère.**
- Plus proche : range asiatique XAUUSD, sortie 16:30 Londres — +0,031 R/trade, PF 1,07, IS +0,016 R, OOS +0,053 R, +4 685 € sur 1 518 trades, DD 4 352 €. Échoue sur le PF (< 1,10).
- Gap fade Nasdaq (gap ≥ 0,5 ATR) : PF 1,08, IS ≈ 0 : non concluant.
- ORB Londres (or, EURUSD) et range asiatique EURUSD : négatifs après frais.
