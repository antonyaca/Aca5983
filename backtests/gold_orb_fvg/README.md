# Or — ORB 30 min New York + retest de FVG M1 (17/10/2026)

`python3 backtests/gold_orb_fvg/backtest.py` ; règles en tête du script (fixées avant le test).
12 variantes : sorties A (1R), B (50 % à 1R + BE, reste à 2R), C (50 % à 1R + BE, reste à 22h) × filtre EMA 200 M15 ou non
× stop libre ou ≥ 1,5 $. 287 à 665 trades selon la variante, 2020 → 10/2026.

**Aucune variante validée ; toutes négatives, déjà avant frais** (−0,03 à −0,14 R/trade brut).
Meilleure : B + EMA 200 + stop ≥ 1,5 $ : −6 037 €, PF 0,65. Pire : C sans filtre : −29 599 €.
Stop médian 1,9-2,6 $ : les frais (0,47 $) pèsent 0,18 à 0,25 R par trade. Le filtre EMA et le stop minimum réduisent la perte
sans la supprimer. Vérification manuelle d'un trade (02/04/2024) conforme aux règles.

## Amélioration testée : cassure et FVG en M5 / M15 (12 variantes de plus)
`python3 backtests/gold_orb_fvg/backtest.py 1 5 15` (M1 identique au premier test : contrôle de non-régression OK).
- M5 : stop médian 3,8 $, frais 0,12 R ; **positif avant frais** (+0,10 à +0,11 R avec EMA 200, taux de réussite 55 %) mais
  **négatif après frais** : meilleure variante C + EMA 200 = −934 €, PF 0,95. Brut en forte baisse : +0,18 R en 2020-2023,
  +0,01 à +0,03 R depuis 2024. Coût d'équilibre (calcul exact, moyenne de brut / moyenne de 1/risque) : 0,33-0,38 $ sur
  2020-2026 mais seulement 0,07-0,16 $ sur 2024-2026 (hypothèse retenue : 0,47 $). Non exploitable.
- M15 : ≈ 0 avant frais, négatif après (−2 231 à −4 301 €).
Aucune variante validée sur 24 au total.
