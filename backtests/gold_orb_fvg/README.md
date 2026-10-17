# Or — ORB 30 min New York + retest de FVG M1 (17/10/2026)

`python3 backtests/gold_orb_fvg/backtest.py` ; règles en tête du script (fixées avant le test).
12 variantes : sorties A (1R), B (50 % à 1R + BE, reste à 2R), C (50 % à 1R + BE, reste à 22h) × filtre EMA 200 M15 ou non
× stop libre ou ≥ 1,5 $. 287 à 665 trades selon la variante, 2020 → 10/2026.

**Aucune variante validée ; toutes négatives, déjà avant frais** (−0,03 à −0,14 R/trade brut).
Meilleure : B + EMA 200 + stop ≥ 1,5 $ : −6 037 €, PF 0,65. Pire : C sans filtre : −29 599 €.
Stop médian 1,9-2,6 $ : les frais (0,47 $) pèsent 0,18 à 0,25 R par trade. Le filtre EMA et le stop minimum réduisent la perte
sans la supprimer. Vérification manuelle d'un trade (02/04/2024) conforme aux règles.
