# Campagne 2 « 1 trade par jour » — protocole (fixé le 18/10/2026, avant tout test)

## Demande d'Anto
Une stratégie SIMPLE (une règle, un indicateur simple au maximum), **1 trade par jour, un 2e seulement si le 1er est
perdant**, sur n'importe quel marché, avec le plus possible de jours positifs. Objectif affiché : 50 à 100 €/jour.

## Cadre (inchangé)
- 10 000 €, **100 € de risque par trade** (1 R), pas de composés. CFD. Données M1 2011-2026 corrigées (`lib.load`).
- Marchés : NASDAQ100, SP500, FTSE100, NIKKEI225, XAUUSD, XAGUSD, EURUSD, GBPUSD, USDJPY, AUDUSD.
- Coûts `lib.COST` (+ swap `lib.SWAP` si nuit), ×2 les jours d'annonce quand applicable.
- Découverte 2011-2018 / validation 2019-2026.

## Simulation
- Générer TOUS les trades candidats de la stratégie, un à la fois (pas de chevauchement), avec colonnes
  `day, t_in, t_out, gross_r, cost_r` (+ `instrument`, `d`, ...).
- Appliquer `lib.regle_anto(t)` → trades réellement pris (1er du jour ; 2e seulement si le 1er perd).
- Évaluer **les trades pris** avec `lib.evaluate` ET les journées avec `lib.stats_jour` / `lib.line_jour`.
- Stratégie multi-marchés autorisée : la règle prend alors le 1er signal du jour tous marchés confondus.

## Validation (stricte, inchangée)
`lib.evaluate(...)["valide"]` : ≥ 100 trades, E > 0 en découverte ET validation, PF ≥ 1,10, E > 0 frais ×2, t ≥ 3,
E > 0 sans top 10, ≥ 60 % d'années positives. Les statistiques journalières (jours positifs, €/jour, pire série) servent
au classement, PAS à la validation : un taux de jours positifs élevé avec une espérance ≤ 0 est un piège.

## Budget et honnêteté
- **20 variantes maximum par agent**, toutes enregistrées (y compris les échecs), règles écrites AVANT le calcul.
- Paramètres ronds et standards, aucune optimisation après lecture des résultats.
- Pas de look-ahead ; vérifier quelques trades à la main ; signaler les anomalies de données
  (trou 17/02-31/07/2023 tous marchés ; S&P incomplet 2012-2014 et 2017 ; Nikkei clairsemé avant 2019).
