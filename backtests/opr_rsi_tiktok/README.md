# Or — réplique de l'EA TikTok « OPR_SIMPLE + RSI » (23/10/2026)

`python3 backtests/opr_rsi_tiktok/backtest.py` ; règles en tête du script. Range 7h serveur (GMT+2/+3) en M5,
cassure en clôture M5 filtrée par RSI, SL autre borne, RR 2, 1 trade/jour, 100 $ de risque fixe.

| Test | Trades | Profit (frais 0,10 $) | PF |
|---|---|---|---|
| Paramètres de la vidéo (20/55, RSI 8, 10-60), 2026 | 203 | −133 $ | 0,99 |
| Mêmes paramètres, 2020-2025 | 1 545 | −1 458 $ | 0,99 |
| Meilleur de l'optimisation 2026 (126 720 combinaisons) | 203 | +6 736 $ | 1,60 |
| Ce même réglage, 2020-2025 | 1 547 | −11 435 $ | 0,90 |
| Les 50 meilleurs réglages 2026, en 2020-2025 | — | médiane −13 498 $, 0 sur 50 positif | — |

97 % des combinaisons sont gagnantes en 2026 (année de forte hausse de l'or) : l'optimisation choisit la chance.
Sans filtre RSI : +2 131 $ sur 2020-2025 à 0,10 $ de frais, PF 1,02, négatif à 0,47 $. **Non validé.**
