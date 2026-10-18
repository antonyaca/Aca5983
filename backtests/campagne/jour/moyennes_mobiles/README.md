# 1 trade par jour avec UNE moyenne mobile ou UN indicateur classique (18/10/2026)

Protocole : `../PROTOCOLE.md`. Les 20 règles (budget maximum) sont écrites dans la docstring de `run.py` avant tout calcul,
avec des paramètres standards uniquement. Cadre : 10 marchés, 2011-2026, 100 € par R, frais `lib.COST` (×2 les jours
d'annonce US), sortie au plus tard en fin de séance (pas de swap). On applique la règle d'Anto (`lib.regle_anto`) puis
`lib.evaluate` et `lib.stats_jour`. Chaque règle est testée en portefeuille (1er signal du jour, tous marchés confondus)
et sur chaque marché séparément, soit 220 évaluations.

## Verdict : aucune règle validée (0 sur 20 ; 0 évaluation validée sur 220)

| Var. | Règle | Trades | E nette (R) | t | Jours + | €/jour | Pire série (j) | Meilleur marché : E (t) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| V01 | Ouverture, SMA20 J, SL 1 ATR H1, TP 1R | 5 987 | −0,145 | −11,2 | 49,8 % | −21,07 | 11 | AUDUSD −0,090 (−5,7) | ✘ |
| V02 | Ouverture, SMA50 J, SL 1 ATR H1, TP 1R | 6 013 | −0,139 | −10,8 | 48,9 % | −20,37 | 10 | XAUUSD −0,101 (−6,4) | ✘ |
| V03 | Ouverture, SMA20 J, SL 0,5 ATR J, TP 1R | 5 661 | −0,062 | −5,9 | 53,7 % | −8,51 | 8 | XAUUSD −0,013 (−1,1) | ✘ |
| V04 | Ouverture, SMA50 J, SL 0,5 ATR J, TP 1R | 5 690 | −0,067 | −6,4 | 52,9 % | −9,32 | 9 | XAUUSD −0,013 (−1,1) | ✘ |
| V05 | Ouverture, EMA200 H1, SL 1 ATR H1, TP 1R | 5 949 | −0,121 | −9,4 | 50,9 % | −17,47 | 11 | FTSE100 −0,075 (−4,6) | ✘ |
| V06 | Ouverture, EMA200 H1, SL 0,5 ATR J, TP 1R | 5 615 | −0,038 | −3,6 | 55,0 % | −5,13 | 9 | XAUUSD +0,003 (+0,2) | ✘ |
| V07 | Ouverture, SMA20 J, SL 0,5 ATR J, sans TP | 5 703 | −0,057 | −4,7 | 53,6 % | −7,85 | 9 | XAUUSD −0,013 (−0,9) | ✘ |
| V08 | Ouverture, SMA20 J, SL 0,5 ATR J, TP 2R | 5 702 | −0,057 | −4,9 | 53,8 % | −7,87 | 9 | XAUUSD −0,020 (−1,4) | ✘ |
| V09 | Ouverture, SMA200 J, SL 0,5 ATR J, TP 1R | 5 612 | −0,054 | −5,1 | 54,2 % | −7,33 | 10 | NASDAQ100 −0,023 (−1,7) | ✘ |
| V10 | Croisement EMA9/21 M15 + SMA20 J, SL 0,5 ATR J | 5 238 | −0,050 | −5,2 | 52,3 % | −6,38 | 12 | SP500 −0,035 (−2,1) | ✘ |
| V11 | Croisement EMA9/21 M15 + SMA20 J, SL 1 ATR H1 | 5 864 | −0,166 | −13,0 | 51,0 % | −23,70 | 9 | EURUSD −0,103 (−5,7) | ✘ |
| V12 | Repli sur EMA20 H1 (tendance EMA200 H1) | 5 332 | −0,063 | −6,7 | 51,6 % | −8,19 | 10 | NASDAQ100 −0,022 (−1,6) | ✘ |
| V13 | Retournement Supertrend 10/3 H1, SL ligne ST | 4 488 | −0,029 | −3,5 | 50,5 % | −3,14 | 13 | NASDAQ100 −0,010 (−0,7) | ✘ |
| V14 | Supertrend 10/3 H1 + SMA20 J | 2 792 | −0,027 | −2,7 | 48,8 % | −1,85 | 12 | NASDAQ100 +0,021 (+1,0) | ✘ |
| V15 | Croisement MACD 12/26/9 H1 | 5 204 | −0,035 | −3,7 | 53,4 % | −4,38 | 8 | GBPUSD −0,003 (−0,2) | ✘ |
| V16 | Croisement MACD H1 + SMA20 J | 4 566 | −0,044 | −4,5 | 50,9 % | −4,89 | 10 | NASDAQ100 −0,015 (−0,8) | ✘ |
| V17 | RSI14 H1 sort de 30/70 + SMA20 J | 2 246 | −0,053 | −4,0 | 48,7 % | −2,89 | 16 | FTSE100 +0,018 (+0,5) | ✘ |
| V18 | RSI14 H1 franchit 70/30 (momentum) + SMA20 J | 3 287 | −0,018 | −1,5 | 50,6 % | −1,47 | 11 | FTSE100 +0,001 (0,0) | ✘ |
| V19 | Clôture H1 qui recroise l'EMA20 H1 + SMA20 J | 5 042 | −0,053 | −5,5 | 52,1 % | −6,47 | 11 | NASDAQ100 −0,013 (−0,8) | ✘ |
| V20 | Témoin : achat à l'ouverture, sans indicateur | 5 661 | −0,056 | −5,3 | 54,5 % | −7,71 | 9 | NASDAQ100 −0,014 (−1,1) | ✘ |

Les 7 premières colonnes chiffrées concernent le portefeuille. « Jours + » = part des jours tradés qui finissent positifs.
Le détail des 220 évaluations est dans `results.json`.

## Les 3 meilleures non validées (toutes sur un seul marché, toutes loin du critère)
1. **V14 Nasdaq** (Supertrend H1 dans le sens de la SMA20 J) : 604 trades, E +0,021 R, t 1,0, PF 1,11 ; −0,019 en
   2011-2018 contre +0,065 en 2019-2026 ; négative avec frais ×2 ; +82 €/an ; DD 1 425 € ; 54 % de jours positifs.
2. **V17 FTSE** (RSI sort de 30/70) : 271 trades, E +0,018, t 0,45 ; −0,032 puis +0,056 ; +31 €/an.
3. **V14 S&P** : 488 trades, E +0,010, t 0,39 ; −0,023 puis +0,039 ; +30 €/an.

Les trois perdent sur 2011-2018 et ne gagnent qu'après 2019, avec un t inférieur à 1 : c'est du bruit, pas un avantage.

## Ce qu'on apprend
- **Avant frais, il n'y a rien à exploiter.** L'espérance brute en portefeuille va de −0,02 à +0,04 R selon la règle.
  Les frais médians coûtent 0,03 à 0,05 R avec un stop de 0,5 ATR journalier, et 0,10 à 0,20 R avec un stop
  de 1 ATR H1 : toutes les règles finissent donc négatives.
- **La moyenne mobile n'apporte rien par rapport au témoin.** Acheter à l'ouverture sans aucun filtre (V20) fait aussi bien
  que la tendance SMA20 (V03) : −0,056 contre −0,062 R en portefeuille. Sur le Nasdaq, le témoin fait même mieux :
  −0,014 contre −0,045 R.
- **Les stops serrés (1 ATR H1) aggravent les pertes** : V01, V02, V05 et V11 font de −0,12 à −0,17 R par trade.
- **Le taux de jours positifs plafonne à 49-55 %**, et comme l'espérance est négative, ce taux ne sert à rien
  (c'est le piège signalé dans le protocole).

## Vérifications (`verif.py`, sortie complète dans `verif_log.txt`)
- Autotest du moteur sur données synthétiques (stop prioritaire, gap, objectif, fin de séance) : réussi.
- **26 trades sur 26 recalculés à l'identique** pour 13 règles et les 10 marchés, avec un code séparé. Les données M1 sont
  coupées juste avant l'entrée, les bougies refaites avec `resample`, les indicateurs (EMA, Wilder, RSI, MACD, Supertrend
  d'après le code Pine) recodés en boucles, et la sortie rejouée minute par minute. C'est la preuve qu'il n'y a pas de
  look-ahead.
- Règle du jour : 0 anomalie (au plus 2 trades par jour, un 2e trade seulement après une perte et après la sortie du 1er).
- Nombre de trades plausible : environ 250 par an et par marché pour les entrées à l'ouverture, et 17 à 200 par an pour
  les signaux intraday. Toutes les entrées tombent dans les fenêtres horaires prévues.

## Anomalies
- **XAGUSD** : le coût de 0,04 $ représente 0,15 R (médiane) avec un stop de 0,5 ATR J, et environ 0,5 R avec 1 ATR H1.
  Les t descendent jusqu'à −29 : l'argent en intraday n'est pas jouable à ce coût.
- **Nikkei** : très peu de séances complètes avant 2020 (7 en 2011, 0 en 2012, 27 à 170 par an de 2013 à 2019). Ses
  résultats viennent donc surtout de 2020-2026.
- **USDJPY 2011** : 134 séances de Londres complètes seulement. **S&P** incomplet en 2012-2014 et 2017.
  **Trou de 2023** : environ 140 séances au lieu de 250.
- **Le portefeuille des règles à heure fixe (V01-V09, V20) se réduit à 3 marchés.** Le 1er trade est le Nikkei quand il
  a des données, sinon le FTSE (premier des marchés de Londres dans l'ordre `lib.MARKETS`, qui départage les ex aequo de
  08:00). Le 2e trade est le FTSE ou le Nasdaq. Les autres marchés n'y entrent presque jamais. Pour cette famille, les
  résultats par marché sont plus parlants que le portefeuille.

## Fichiers
`run.py` (règles et calcul), `results.json` (220 évaluations : `lib.evaluate` + `jour` + `regles`),
`trades/Vxx.csv.gz` (tous les trades candidats), `run_log.txt`, `verif.py`, `verif_log.txt`.
