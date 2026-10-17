# Famille « retour à la moyenne » — campagne oct. 2026

Règles fixées dans le docstring de `run.py` avant tout calcul. 17 variantes testées sur un budget de 25. Toutes figurent dans `results.json` ; les trades sont dans `trades.csv.gz` et les contrôles dans `controles.txt`.
Période 2011-2026, découverte 2011-2018 / validation 2019-2026, critère `lib.evaluate`, 1 R = 100 €. Les stratégies swing sans stop utilisent 1 R = ATR14.
Les données utilisées sont celles corrigées par le coordinateur (marqueur `data_cache/FIXED`).

| Var. | Règles | Trades | E nette (R) | PF | Découv. | Valid. | t | Ans + | Résultat € | DD € | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V01 | IBS<0,2 achat clôture, sortie clôture suivante — 4 indices | 2231 | +0.018 | 1.06 | +0.016 | +0.020 | +0.98 | 8/16 | 4043 | 4458 | rejetée |
| V02 | IBS<0,2 achat, sortie 1re C>H veille ou 5 séances — 4 indices | 1678 | +0.096 | 1.20 | +0.046 | +0.139 | +2.76 | 12/16 | 16032 | 5116 | rejetée |
| V03 | IBS<0,2 achat / >0,8 vente, sortie clôture suivante — or, argent, 4 paires forex | 6893 | -0.047 | 0.82 | -0.036 | -0.059 | -5.98 | 2/16 | -32561 | 34062 | rejetée |
| V04 | RSI2<10 & C>SMA200 achat, sortie C>SMA5 — Nasdaq + S&P sur 2011-2026 | 246 | +0.466 | 2.40 | +0.415 | +0.523 | +5.41 | 12/15 | 11475 | 1119 | **validée** |
| V05 | RSI2<10 & C>SMA200 achat, sortie C>SMA5 — 4 indices | 443 | +0.324 | 1.79 | +0.363 | +0.287 | +4.55 | 10/15 | 14339 | 1931 | **validée** |
| V06 | RSI2 symétrique (10/90, filtre SMA200, sortie SMA5) — 10 marchés | 1562 | +0.069 | 1.15 | +0.044 | +0.094 | +1.92 | 11/16 | 10766 | 4453 | rejetée |
| V07 | Double seven Connors (C>SMA200, plus bas 7 j → plus haut 7 j) — 4 indices | 535 | +0.232 | 1.31 | +0.224 | +0.240 | +2.15 | 10/15 | 12415 | 7483 | rejetée |
| V08 | 3 baisses consécutives achat, sortie 1re hausse ou 5 séances — 4 indices | 753 | +0.117 | 1.35 | +0.026 | +0.206 | +2.76 | 11/16 | 8799 | 3131 | rejetée |
| V09 | 3 baisses consécutives + C>SMA200, sortie 1re hausse ou 5 séances — 4 indices | 488 | +0.148 | 1.48 | +0.079 | +0.206 | +2.97 | 10/15 | 7205 | 2096 | rejetée |
| V10 | Bollinger(20,2) bas achat, sortie C>SMA20 ou 5 séances — 4 indices | 328 | +0.157 | 1.21 | +0.180 | +0.133 | +1.35 | 11/16 | 5151 | 3538 | rejetée |
| V11 | Bollinger(20,2) symétrique, sortie SMA20 ou 5 séances — or, argent, 4 paires | 1223 | -0.108 | 0.84 | -0.113 | -0.103 | -2.35 | 6/16 | -13205 | 16131 | rejetée |
| V12 | Panier indices déclaré : V02 + V05 + V07 | 2656 | +0.161 | 1.31 | +0.137 | +0.183 | +4.87 | 13/16 | 42786 | 14197 | **validée** |
| V13 | Comblement gap 0,1-1 ATR deux sens, objectif clôture veille, stop \|gap\| — 4 indices intraday | 10460 | -0.068 | 0.85 | -0.095 | -0.044 | -7.61 | 1/16 | -71538 | 74061 | rejetée |
| V14 | Comblement gap baissier seulement (achats) — 4 indices intraday | 4537 | -0.066 | 0.86 | -0.087 | -0.046 | -4.75 | 2/16 | -29789 | 31876 | rejetée |
| V15 | Fade 1re heure si \|mouvement\| ≥ 0,5 ATR, sortie clôture, R=ATR — 4 indices intraday | 1249 | -0.030 | 0.89 | -0.057 | -0.008 | -1.54 | 4/16 | -3694 | 4958 | rejetée |
| V16 | Écart au TWAP ≥ 0,5 ATR (10:30-15:00), objectif TWAP, stop 0,5 ATR — Nasdaq + S&P intraday | 1956 | -0.095 | 0.77 | -0.112 | -0.076 | -5.16 | 1/16 | -18534 | 20198 | rejetée |
| V17 | Fade range asiatique ±0,25 W, stop 0,5 W, objectif milieu, sortie 16:00 Londres — 4 paires forex | 10846 | -0.178 | 0.74 | -0.168 | -0.188 | -15.67 | 0/16 | -192820 | 193992 | rejetée |

## Ce qu'on en retient
- **Validées : V04, V05, V12.** Toutes reposent sur le RSI2 de Connors : V04 reprend sur 16 ans le RSI2 Nasdaq + S&P déjà positif sur 2020-2026, V05 l'étend à 4 indices, et le panier V12 contient V05. Ce n'est pas un edge nouveau, mais une confirmation du RSI2 sur 2011-2018, une période qu'il n'avait jamais vue.
- Le retour à la moyenne swing ne fonctionne que **sur les indices actions, à l'achat**. Sur le FTSE, il est faible ou négatif (V02, V07, V08 et le panier V12 y perdent). Le moteur est le Nasdaq et le S&P.
- Sur le forex et les métaux, c'est un échec net : IBS (V03), Bollinger (V11), RSI2 symétrique (côté métaux) et fade du range asiatique (V17) perdent tous. Le fade de V17 perd même en brut.
- En intraday, tout échoue : comblement de gap, fade de la 1re heure et écart au TWAP. C'est cohérent avec le momentum intraday décrit dans la littérature (Gao et al. 2018).
- Proches du seuil, mais non validées : V09 (t = 2,97), V02 (t = 2,76, découverte faible) et V07 (t = 2,15, frais ×2 à peine positifs).

## Mises en garde
- V12 est une union de trades qui se chevauchent (V05 ⊂ V12, même signal du même jour possible dans plusieurs jambes). Son t est gonflé par cette corrélation, et son drawdown de 14 k€ est élevé pour 10 k€ de capital.
- V04 et V05 ne prennent que 16 à 30 trades par an. Avec R = ATR, une perte de 5 à 8 R est possible (krachs de 2018 et 2025).
- Les coûts ×2 des jours d'annonce ne sont pas appliqués : il n'y a pas de calendrier avant 2020, et les exécutions se font à la clôture ou à l'ouverture. Le test frais ×2 couvre ce point.
- Il n'y a pas de volume dans les données, donc V16 utilise un TWAP à la place du VWAP.

## Anomalies de données (à signaler)
1. **Trou général du 17/02/2023 au 31/07/2023** : les indices et le forex n'ont aucune séance valable (seulement des journées partielles de 960 à 1 014 minutes pour le forex et les métaux de mars à juillet). Le Nasdaq et le S&P ont aussi des trous du 17 au 27/02/2017.
2. **Nikkei 2011-2019** : nombreux trous de plusieurs semaines à plusieurs mois (2011-09 → 2012-03, 2012-03 → 2012-10, 2017-06 → 2017-11, etc. ; liste complète dans `controles.txt`). Argent : trous en 2010 ; USDJPY : trous en 2011.
3. **Décalage d'horaire résiduel après correction** : pendant les semaines où les États-Unis et l'Europe ne sont pas encore à la même heure (mars et fin octobre), le Nasdaq n'a aucune minute entre 15:15 et 16:15 NY (ex. 17/03/2026, 29/10/2025). Cela touche environ 15 à 20 séances par an, avec une clôture de séance effective vers 15:14. Cela ressemble à un résidu du bug d'horodatage, avec un changement d'heure européen et non américain. Rien n'a été corrigé localement.
4. Bug de mise en œuvre corrigé (sans changer de variante) : les métaux rouvrent à 18:00 NY. Ma tolérance d'ouverture de 5 minutes écartait toutes leurs séances à partir de 2015 ; elle passe à 18:05 pour l'or et l'argent.
5. Règle de traitement uniforme ajoutée après le constat 1-2 : un trade swing qui chevauche un trou de plus de 7 jours est écarté (42 trades, cf. `controles.txt`), car il était valorisé jusqu'à 239 nuits plus tard.

## Contrôles
- Look-ahead : les indicateurs recalculés sur des données tronquées à mi-période sont identiques (10/10 marchés).
- Vérifié à la main : trade V04 S&P du 10/09/2026 (RSI2 7,47, entrée 7592,83, sortie 7663,78, +1,301 R brut, coût 0,037 R dont swap 0,023) et trade V13 S&P du 02/10/2026 (gap 33,4 pts, ni stop ni objectif touchés, sortie en clôture).
- Fréquences plausibles (V04 : environ 16 trades/an ; V13 : environ 650/an sur 4 indices) ; coût médian de 0,05 à 0,18 R selon la variante.
