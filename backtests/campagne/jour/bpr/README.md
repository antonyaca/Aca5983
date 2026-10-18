# BPR à l'ouverture de Londres / New York + retest M1 (captures d'Anto, 18/10/2026)

Règles : `run.py` (fixées avant calcul) — BPR détecté en M5 dans les 90 min après l'ouverture (chevauchement de deux FVG
opposés), sens du 2e FVG, retest M1 dans les 3 h (entrée limite au bord de zone « L » ou après reclôture hors zone « C »),
stop au-delà de l'extrême du mouvement, objectif 1:2 ou 1:1, sortie 16:00 NY, règle d'Anto. 2011-2026.
Contrôle manuel : trade or du 02/09/2026 (Londres) — FVG haussier 07:10, FVG baissier 07:45, zone 4 325,02-4 325,90,
vente au retest 08:02, stop 4 331,18 touché 08:10 : conforme aux bougies brutes.

## Résultat : perdant sur les 16 combinaisons
| Marché | Trades | Brut / trade | Coût médian | Net (meilleure variante) | Jours positifs |
|---|---|---|---|---|---|
| Or | 2 700-3 070 | +0,005 à +0,064 R | 0,19-0,22 R | −0,170 R (C, 1:2) | 40-49 % |
| EURUSD | 2 690-3 150 | +0,003 à +0,025 R | 0,15-0,17 R | −0,146 R | 40-51 % |
| Nasdaq | 2 530-2 900 | −0,019 à +0,019 R | 0,11-0,13 R | −0,165 R | 39-50 % |
| S&P | 2 310-2 630 | +0,021 à +0,052 R | 0,17-0,20 R | −0,181 R | 39-51 % |
Avant frais le BPR vaut un pile ou face ; avec le spread, il perd sur chaque marché et presque chaque année.

## Variante M15 (BPR en M15 dans les 3 h après l'ouverture, retest M1 dans les 4 h) — `python3 run.py M15`
| Marché | Trades | Brut / trade | Net coût fixe (meilleure) | Net coût ∝ prix (Nasdaq) |
|---|---|---|---|---|
| Or | 1 320-1 450 | +0,03 à +0,04 R | −0,131 R | — |
| EURUSD | 1 385-1 520 | +0,02 à +0,07 R | −0,058 R | — |
| Nasdaq | 1 350-1 470 | +0,10 à +0,13 R | −0,026 R | +0,022 à +0,052 R, t ≤ 1,46, 2019-2026 ≈ +0,01 R |
| S&P | 1 170-1 290 | +0,08 à +0,10 R | −0,065 R | — |
Mieux qu'en M5 (moins de frais relatifs), mais aucune variante validée ; sur le Nasdaq l'avantage s'efface après 2019.
