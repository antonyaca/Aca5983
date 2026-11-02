# Cassure ATR depuis l'ouverture façon Unger — Nasdaq (02/11/2026)

Lancer : `python3 backtests/campagne/unger_atr/run.py` (règles et coûts dans le docstring, fixés avant calcul).

Niveaux = ouverture 09:30 NY ± k × ATR14 de séance ; 1er niveau touché ; stop = ouverture ; sortie 16:00 ; 1 trade/jour.
Coûts A/R proportionnels au prix, calés sur les tarifs actuels (Nasdaq ≈ 28 400) : CFD Pepperstone 1,7 pt · MNQ 1,25 pt · NQ 0,95 pt.

| Variante (coût CFD) | Trades | E nette | t | €/an | DD max | Ans + | Validé |
|---|---|---|---|---|---|---|---|
| W Williams k 0,5 × range veille (réf.) | 2 893 | +0,087 R | 3,99 | +1 599 | 3 650 | 15/16 | ✔ |
| U2 ATR k 0,25 | 3 691 | +0,087 R | 3,21 | +2 032 | 4 056 | 13/16 | ✔ |
| U1 ATR k 0,5 | 2 560 | +0,050 R | 2,69 | +817 | 2 095 | 13/16 | ✘ (t < 3) |
| U3 ATR k 1,0 | 743 | +0,016 R | 0,80 | ≈ 0 | 1 070 | 9/16 | ✘ |
| U4 ATR k 0,5 achat seul | 1 328 | +0,045 R | 2,04 | +390 | 1 380 | 13/16 | ✘ |
| U5 ATR k 0,5 vente seule | 1 361 | +0,049 R | 1,72 | +430 | 1 983 | 13/16 | ✘ |

- Futures vs CFD : +0,003 à +0,008 R par trade seulement (MNQ ≈ CFD à petite taille ; NQ un peu mieux).
- L'ATR ne fait pas mieux que l'amplitude de la veille : le Williams reste la meilleure version (t plus élevé, 15 années positives sur 16).
- U2 gagne plus par an mais avec 38 % de jours positifs, une pire série de 20 jours et 3 années négatives (2015, 2020, 2026).
- Hypothèse de coût CFD plus douce que la convention du dépôt (1,25 pb ≈ 3,5 pt au niveau actuel) : avec celle-ci, le Williams sort à +0,074 R (voir jour/plan_valides).
