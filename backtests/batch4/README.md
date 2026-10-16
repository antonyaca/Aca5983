# Lot 4 — stratégies publiées (16/10/2026)

Sources : Zarattini, Aziz & Barbon (2024) « Beat the Market » (noise area, SPY) ; Larry Williams (cassure de volatilité) ;
réplication indépendante de l'ORB 5 min de Zarattini & Aziz (mql5.com, 2026) : brut reproduit, net ≈ 0.
Règles exactes en tête de `strategies.py`. Critère inchangé. 100 € par R.

Validées : uniquement sur le Nasdaq.
- Williams k = 0,5, deux sens : 1 189 trades, +0,052 R, PF 1,13, +6 200 €, DD 1 304 €, IS +0,044 / OOS +0,063, frais x2 OOS +0,050.
- Williams k = 0,5, achats seuls : +3 176 €, DD 1 067 €.
- Noise area, achats seuls : +3 343 €, PF 1,26, mais OOS faible (+0,017 R).
Rejetées : tout sur S&P 500 et DAX.

Avec l'ORB Nasdaq achats (corrélation journalière 0,25) : ORB + Williams = +21 991 €, OOS +7 326 €, DD 2 500 €.
