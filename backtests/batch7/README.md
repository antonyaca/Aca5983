# Lot 7 — 5 stratégies M5/M15 (17/10/2026)

`python3 backtests/batch7/strategies.py` ; règles en tête du script. DAX exclu.

**Nouvel edge : cassure du pré-marché (04:00-09:30 NY), sortie 16:00.**
- Nasdaq deux sens : 1 686 trades, +0,071 R, PF 1,14, +11 970 €, DD 3 590 €, IS +0,055 / OOS +0,094, frais ×2 OOS +0,080, t = 2,15.
- Nasdaq achats seuls : +8 954 €, PF 1,21, t = 2,32. S&P 500 achats seuls : +5 806 €, PF 1,14 (validé aussi).
- Tient sans les 5 meilleurs trades (+0,047 R). Positif 6 années sur 7 (2023 ≈ 0).
- Avec ORB + Williams Nasdaq : +33 961 € (au lieu de +21 991 €), 2024+ +13 851 €, DD 3 594 €, 65 % de mois positifs, un trade tous les jours.

Rejetées : ORB or COMEX, NR7 M15 (Nasdaq, or), retour à la moyenne asiatique (EURUSD, or : fortement négatif), prix moyen 11:00 (OOS ≈ 0).
