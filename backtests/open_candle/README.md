# Backtest « bougie d'ouverture » — M15 (XAUUSD, EURUSD, SP500, NASDAQ100)

Lancer : `python3 backtests/open_candle/backtest.py [INSTRUMENT ...]` (lit `data/<INSTRUMENT>/`, écrit `results/<INSTRUMENT>/`).
Capital 10 000 €, risque fixe 100 € par trade (1 %, sans composition).

## Règles testées
- Bougie signal M15 : Londres 08:00 heure de Londres, New York 09:30 heure de New York (heure d'été gérée localement).
- Clôture > ouverture → BUY à l'ouverture de la bougie suivante ; clôture < ouverture → SELL ; doji → rien. 1 trade max par session et par jour.
- SL A : extrême de la bougie signal ± 0,20 $. SL B : dernier fractal M15 confirmé (2 bougies de chaque côté) ± 0,20 $, repli sur A s'il est du mauvais côté de l'entrée.
- TP = RR × risque, RR ∈ {1 ; 1,5 ; 2 ; 3}. Aucune autre sortie.
- Coûts aller-retour (spread + slippage + commission) et marge du stop, voir `INSTRUMENTS` dans le script :
  XAUUSD 0,30 + 0,10 + 0,07 $, marge 0,20 $ · EURUSD 0,6 + 0,2 + 0,7 pip, marge 1 pip · SP500 0,50 + 0,25 pt, marge 0,5 pt · NASDAQ100 1,0 + 0,5 pt, marge 2 pt.

## Simulation
- M15 reconstruit à partir du M1 (bid). Sorties simulées minute par minute ; SL et TP dans la même minute → SL.
- Gap au-delà d'un niveau → sortie à l'ouverture de la minute.
- In-sample : entrées 2020-2023 ; out-of-sample : 2024 → fin des données.
- Drawdown % : 1 % risqué par trade, sans composition.

## Résultat (16/10/2026, données au 09/10/2026)
Aucune des 96 combinaisons (4 marchés × 24 réglages) n'a un profit factor net > 1 sur 2020-2026.
- XAUUSD : seul marché avec un avantage brut constant (Londres, IS et OOS), mais plus petit que les coûts. Meilleur net : Londres · SL A · RR 3, −17 171 €.
- EURUSD : un seul avantage brut stable, New York · SL B · RR 3 (+0,07 R en IS, +0,08 R en OOS), mais insuffisant après frais : −12 145 €.
- SP500 : aucun avantage brut stable ; meilleur net New York · SL A · RR 1, −18 363 €.
- NASDAQ100 : aucun avantage brut stable ; meilleur net New York · SL B · RR 3, −5 655 € (2024-2026 : quasi nul, PF 1,01).
