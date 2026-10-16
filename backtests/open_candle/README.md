# Backtest « bougie d'ouverture » — XAUUSD M15

Lancer : `python3 backtests/open_candle/backtest.py` (lit `data/XAUUSD/`, écrit `results/`).

## Règles testées
- Bougie signal M15 : Londres 08:00 heure de Londres, New York 09:30 heure de New York (heure d'été gérée localement).
- Clôture > ouverture → BUY à l'ouverture de la bougie suivante ; clôture < ouverture → SELL ; doji → rien. 1 trade max par session et par jour.
- SL A : extrême de la bougie signal ± 0,20 $. SL B : dernier fractal M15 confirmé (2 bougies de chaque côté) ± 0,20 $, repli sur A s'il est du mauvais côté de l'entrée.
- TP = RR × risque, RR ∈ {1 ; 1,5 ; 2 ; 3}. Aucune autre sortie.
- Coûts : 0,30 $ spread + 0,10 $ slippage + 0,07 $ commission = 0,47 $ par trade, déduits du résultat en R.

## Simulation
- M15 reconstruit à partir du M1 (bid). Sorties simulées minute par minute ; SL et TP dans la même minute → SL.
- Gap au-delà d'un niveau → sortie à l'ouverture de la minute.
- In-sample : entrées 2020-2023 ; out-of-sample : 2024 → fin des données.
- Drawdown % : 1 % risqué par trade, sans composition.

## Résultat (16/10/2026, données au 09/10/2026)
Aucune des 24 combinaisons n'est rentable après frais (PF net < 1 partout, en IS comme en OOS sauf Londres · A · RR 3 en OOS, PF 1,03, non significatif).
Avant frais, l'avantage se concentre à Londres (espérance +0,04 à +0,14 R), il est quasi nul à New York (-0,02 à +0,03 R). Dans tous les cas il reste inférieur au coût moyen (~0,19 R par trade).
