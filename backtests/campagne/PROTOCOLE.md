# Campagne de recherche d'edges — protocole (fixé le 17/10/2026, avant tout test)

## Cadre
- Capital 10 000 €, **100 € de risque fixe par trade** (1 R = 100 €), pas d'intérêts composés. CFD.
- Marchés : NASDAQ100, SP500, FTSE100, NIKKEI225, XAUUSD, XAGUSD, EURUSD, GBPUSD, USDJPY, AUDUSD.
  Exclus : DAX (2021-2023 corrompu), WTI (2024-2025 manquant), CAC40 (données depuis 2020 seulement).
- Données : M1 bid HistData, nov. 2010 (indices) / janv. 2010 (métaux, forex) → 09/10/2026. Chargement via `lib.load()`.
- Période testée : 2011-2026. **Découverte 2011-2018 / validation 2019-2026.**

## Coûts (`lib.COST`, `lib.SWAP`)
- Aller-retour : Nasdaq 1,5 pt ; S&P 0,75 ; FTSE 1,5 ; Nikkei 12 ; or 0,47 $ ; argent 0,04 $ ; EURUSD/AUDUSD 0,00015 ; GBPUSD 0,0002 ; USDJPY 0,02.
- Positions gardées la nuit : swap par nuit calendaire (base 360) — indices et métaux 6 %/an à l'achat, 1 %/an à la vente ; forex 2,5 %/an.
- Jours d'annonce macro : coûts ×2.

## Exécution simulée
- Signal sur données connues à l'instant t ; entrée au prix suivant (ouverture de la minute / barre suivante, ou niveau si ordre stop/limite).
- Stop prioritaire sur l'objectif dans la même barre. Gap au-delà du stop → sortie à l'ouverture.
- Stratégies sans stop : 1 R = ATR14 journalier à l'entrée (calculé sur les jours précédents).

## Budget et honnêteté
- **25 variantes maximum par famille**, toutes enregistrées (y compris les échecs) dans `results.json`.
- Règles écrites dans le docstring **avant** de lancer le calcul. Pas d'ajustement de paramètre après lecture des résultats.
- Paramètres « ronds » et standards uniquement (pas d'optimisation fine).

## Critère de validation (`lib.evaluate`, plus dur qu'avant à cause du nombre de tests)
1. ≥ 100 trades sur 2011-2026 ;
2. espérance nette > 0 en découverte (2011-2018) **et** en validation (2019-2026) ;
3. profit factor net ≥ 1,10 ;
4. espérance encore > 0 avec frais doublés ;
5. **t ≥ 3** ;
6. espérance > 0 sans les 10 meilleurs trades ;
7. au moins 60 % d'années positives.

## Contrôle final
Chaque candidat validé est recodé indépendamment par Claude (code séparé) avant d'entrer dans le top 5.
Top 5 classé par résultat annuel / drawdown max, en comparant avec les stratégies Nasdaq déjà validées.
