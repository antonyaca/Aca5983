# Noise area sur le S&P 500, coûts de futures (02/11/2026)

Lancer : `python3 backtests/campagne/noise_area_sp500/run.py`. Règles identiques à `noise_area/` (Nasdaq) ; seuls changent
le marché (S&P 500, celui de l'étude) et les coûts (CFD 0,75 pt · MES 0,7 pt · ES 0,6 pt, proportionnels au prix).

**Aucune variante validée, mais nettement meilleur que sur le Nasdaq (t 1,0) : seul le critère t ≥ 3 échoue.**

| Variante | Coût | Trades | E nette | PF | t | €/an | DD max | Ans + |
|---|---|---|---|---|---|---|---|---|
| V1 deux sens | CFD | 2 948 | +0,035 R | 1,17 | 2,68 | +660 | 2 079 € | 12/16 |
| V1 deux sens | ES | 2 948 | +0,039 R | 1,19 | 2,95 | +727 | 1 956 € | 12/16 |
| V4 achats seuls + règle Anto | CFD | 1 331 | +0,041 R | 1,23 | 2,54 | +342 | 854 € | 13/16 |
| V4 achats seuls + règle Anto | ES | 1 330 | +0,044 R | 1,25 | 2,78 | +368 | 811 € | 13/16 |

- Positif en découverte (2011-2018) ET en validation (2019-2026), encore positif avec frais ×2 et sans les 10 meilleurs trades.
- Futures vs CFD : +0,004 à +0,005 R par trade seulement.
- Point d'alerte : 2025 et 2026 négatifs pour V1 (−311 € et −1 087 €).
- Données S&P incomplètes 2012-2014 et 2017 (jours écartés) : moins de trades, t plus faible qu'avec des données complètes.

Statut : **en observation** (comme le pré-market Nasdaq).
