# Campagne de recherche d'edges — résultat (17/10/2026)

Protocole : `PROTOCOLE.md` (critère durci : t ≥ 3, découverte 2011-2018 ET validation 2019-2026 positives, frais ×2,
sans top 10, ≥ 60 % d'années positives). 4 familles, 79 variantes testées par 4 agents + revalidation des stratégies existantes.

## Deux bugs de données trouvés et corrigés pendant la campagne
1. HistData horodate en heure murale de New York (heure d'été incluse), pas en EST fixe → +1 h l'été dans tous les
   backtests intraday antérieurs (`scripts/fix_timezone.py`).
2. Depuis 2019, l'horloge source suit l'heure d'été européenne → ~3 semaines/an encore décalées (`scripts/fix_timezone2.py`).
Vérifié après correction : pause quotidienne et ouverture au bon horaire chaque année, sur chaque marché.
Tous les résultats ci-dessous sont recalculés sur les données corrigées. L'indicateur TradingView et le robot MT5 ne sont
pas concernés (ils lisent l'heure réelle de la bourse).

## Top 5 (2011-2026, 100 € par trade)

| # | Stratégie | Trades | €/an | DD max | t | Statut |
|---|---|---|---|---|---|---|
| 1 | **RSI2 Nasdaq + S&P** (achat RSI2 < 10 au-dessus de la SMA200, sortie clôture > SMA5) | 251 | 739 | 860-1 270 | 5,8 | ✔ validé, recodé indépendamment, tient aussi en exécution à l'ouverture J+1 |
| 2 | **NFP or** (range 08:00-08:30 NY, cassure, stop bord opposé, TP 1:2) | 160 | 574 | 717 | 4,6 | ✔ validé, 2011-2019 hors échantillon t 2,65 ; **sensible au slippage** (> 2 $ par trade → nul) |
| 3 | **Williams k = 0,5 Nasdaq** (intraday) | 2 881 | 1 350 | 4 199 | 3,4 | ✔ validé avec coût proportionnel au prix ; avec 1,5 pt fixe en 2011 (Nasdaq ≈ 2 300) : t 1,8 |
| 4 | **3 baisses consécutives Nasdaq + S&P** (sortie 1re hausse ou 5 séances) | 386 | 542 | 1 283 | 4,0 | ✔ validé en fin de séance ; t 2,1 seulement en exécution à l'ouverture J+1 → le plus fragile |
| 5 | Pré-market Nasdaq | 3 735 | ≈ 1 150 | 3 586 | 2,3 | ✘ en observation (positif mais non significatif 2011-2019) |

Déclassés : **ORB 30 min Nasdaq** (nul sur 2011-2019, +6 455 € seulement sur 2020-2026 une fois l'heure corrigée),
NFP Nasdaq (non significatif hors échantillon), fin de mois (ne tient pas sur 16 ans).

## Portefeuille des 4 validées (`verification/portefeuille.py`)
+50 457 € sur 2011-2026 ≈ **3 200 €/an**, drawdown max 2 910 €, 65 % de mois positifs, **16 années positives sur 16**,
pire mois −1 182 €.

## Rien trouvé dans
Momentum intraday, time-series momentum (mangé par le swap), cassure du range asiatique, Gotobi USDJPY, fix WM/Reuters,
fix de l'or, séances or/argent, ratio or/argent, gaps, fade 1re heure, TWAP, Bollinger forex, effets de calendrier
(FOMC et veille de férié prometteurs mais t < 2).

## Anomalies de données restantes
Trou du 17/02 au 31/07/2023 (≈ 30 % des minutes manquantes, tous marchés) ; S&P incomplet 2012-2014 et 2017 ;
Nikkei clairsemé avant 2019.
