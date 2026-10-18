# Forex + métaux, « 1 trade par jour » (Londres / New York) : 17 variantes sur 20, 0 validée

Règles : docstring de `run.py`, écrite avant tout calcul de résultat (seuls des diagnostics de coût avaient été faits).
Résultats complets : `results.json` (`lib.evaluate` des trades pris après `lib.regle_anto`, `jour` = `lib.stats_jour`, `regles`, diagnostics par marché).
Candidats et trades pris : `trades/Vxx.csv.gz` (colonne `pris`). Contrôle indépendant : `verif.py`.

Cadre : EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD et XAGUSD mis en commun. On prend le 1er signal du jour tous marchés confondus, puis un 2e trade seulement si le 1er perd.
Entrées entre 08:00 Londres et 12:00 NY, sortie forcée à 16:00 NY. 100 € par R. Coûts `lib.COST`, doublés les jours NFP, CPI et FOMC (calendrier officiel 2011-2026).
Un signal est ignoré si son coût dépasse 0,10 R. Découverte 2011-2018, validation 2019-2026.

| Var. | Règle | Trades | E brute (R) | E nette (R) | Coût méd. (R) | t | Jours + | €/jour | €/an | DD max | Pire série | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| V01 | Cassure 1re H1 Londres, TP 1:1 | 5391 | +0,036 | -0,038 | 0,0717 | -2,92 | 52 % | -5,00 € | -1 304 € | 22 816 € | 8 j | ✘ rejetée (7/8 critères ratés) |
| V02 | Cassure 1re H1 Londres, TP 1:2 | 5668 | +0,046 | -0,029 | 0,0718 | -1,74 | 51 % | -3,99 € | -1 043 € | 21 334 € | 10 j | ✘ rejetée (7/8 critères ratés) |
| V03 | PDH/PDL rejet 1er contact, 1:1 | 3688 | -0,041 | -0,091 | 0,0433 | -7,05 | 47 % | -8,15 € | -2 127 € | 33 883 € | 11 j | ✘ rejetée (7/8 critères ratés) |
| V04 | PDH/PDL cassure 1er contact, 1:2 | 3686 | +0,034 | -0,016 | 0,0434 | -1,07 | 48 % | -1,41 € | -368 € | 8 608 € | 11 j | ✘ rejetée (6/8 critères ratés) |
| V05 | Pivots P/R1/S1 rebond, 1:1 | 4408 | -0,018 | -0,068 | 0,043 | -5,65 | 47 % | -7,23 € | -1 888 € | 29 935 € | 11 j | ✘ rejetée (7/8 critères ratés) |
| V06 | Nombres ronds 00/50 rejet, 1:1 | 4565 | -0,052 | -0,098 | 0,0401 | -8,38 | 45 % | -10,87 € | -2 837 € | 44 996 € | 21 j | ✘ rejetée (7/8 critères ratés) |
| V07 | Nombres ronds 00/50 cassure, 1:2 | 4448 | +0,048 | +0,003 | 0,0399 | +0,20 | 49 % | +0,30 € | 78 € | 5 793 € | 9 j | ✘ rejetée (6/8 critères ratés) |
| V08 | Range NY 08:00-09:30 cassure, hors annonces, 1:1 | 4146 | +0,006 | -0,055 | 0,0625 | -4,34 | 48 % | -5,54 € | -1 447 € | 23 232 € | 13 j | ✘ rejetée (7/8 critères ratés) |
| V09 | Frankfurt 07:00-08:00 cassure, 1:1 | 5206 | +0,020 | -0,059 | 0,0755 | -4,32 | 51 % | -7,41 € | -1 933 € | 31 720 € | 9 j | ✘ rejetée (7/8 critères ratés) |
| V10 | Tendance SMA20 + 08:00 Londres (2e 08:00 NY), 1:1 | 4495 | +0,013 | -0,037 | 0,0431 | -3,00 | 51 % | -4,05 € | -1 057 € | 17 682 € | 11 j | ✘ rejetée (7/8 critères ratés) |
| V11 | PDH/PDL cassure sens tendance, 1:2 | 2504 | +0,038 | -0,012 | 0,0441 | -0,69 | 47 % | -0,75 € | -196 € | 6 885 € | 9 j | ✘ rejetée (7/8 critères ratés) |
| V12 | Cassure 1re H1 Londres sens tendance, 1:1 | 4059 | +0,015 | -0,061 | 0,0727 | -4,00 | 50 % | -5,97 € | -1 559 € | 27 023 € | 11 j | ✘ rejetée (7/8 critères ratés) |
| V13 | Pivots rebond sens tendance, 1:1 | 3519 | -0,013 | -0,063 | 0,0433 | -4,82 | 48 % | -5,38 € | -1 403 € | 22 455 € | 12 j | ✘ rejetée (7/8 critères ratés) |
| V14 | Nombres ronds rejet sens tendance, 1:1 | 3482 | -0,062 | -0,108 | 0,0397 | -8,36 | 45 % | -9,16 € | -2 392 € | 37 948 € | 12 j | ✘ rejetée (7/8 critères ratés) |
| V15 | Plus haut/bas semaine préc. rejet, 1:1 | 1494 | -0,114 | -0,164 | 0,0442 | -8,34 | 42 % | -5,97 € | -1 559 € | 25 175 € | 15 j | ✘ rejetée (7/8 critères ratés) |
| V16 | PDH/PDL rejet sens tendance, 1:1 | 2442 | -0,033 | -0,083 | 0,0431 | -5,34 | 48 % | -4,94 € | -1 289 € | 20 566 € | 15 j | ✘ rejetée (7/8 critères ratés) |
| V17 | Cassure 1re H1 Londres, stop/TP 0,5 ATR | 5049 | +0,010 | -0,039 | 0,0422 | -3,48 | 49 % | -4,75 € | -1 240 € | 21 670 € | 11 j | ✘ rejetée (7/8 critères ratés) |

## Ce qu'on apprend
- **Les niveaux cassent plus souvent qu'ils ne rebondissent.** Tous les rejets au 1er contact ont un résultat brut négatif, avant même les frais :
  PDH/PDL −0,041 R, pivots −0,018 R, chiffres ronds −0,052 R, plus haut/bas de la semaine précédente −0,114 R. Le filtre de tendance n'y change rien (V13, V14, V16).
- **Les cassures ont un léger avantage brut, de +0,03 à +0,05 R** (ORB 1re H1 Londres, PDH/PDL, chiffres ronds). C'est à peu près le montant des frais (0,04 à 0,075 R) :
  le net revient à 0 ou devient négatif. La meilleure variante, V07 (cassure des chiffres ronds, 1:2), fait +0,003 R par trade (t 0,2).
- Tendance SMA20 avec entrée à heure fixe (V10) : +0,013 R brut, donc aucun avantage. Range NY 08:00-09:30 (V08) : +0,006 R brut. Frankfurt (V09) : +0,020 R brut pour 0,075 R de coût.
- Les jours positifs vont de 42 à 52 % partout. Avec un objectif 1:1 ou 1:2 et un brut proche de zéro, on reste mécaniquement autour d'un jour sur deux. On est loin des 50-100 €/jour visés.

## Pistes non validées (à pré-enregistrer avant tout nouveau test)
1. **Cassure des plus hauts/bas hebdomadaires.** Le rejet (V15) perd entre −0,06 et −0,16 R brut sur chacun des 6 marchés.
   L'ordre inverse (cassure 1:1, même stop et même objectif de 0,5 ATR) gagnerait donc environ +0,11 R brut, soit +0,07 R net, par symétrie approximative.
   C'est une déduction faite APRÈS lecture des résultats, pas un test : à coder séparément, puis à confirmer sur des données encore jamais vues (suivi en temps réel).
2. Sous-résultats par marché (ce sont 102 sous-tests, donc probablement du bruit) : V07 sur l'or, +0,084 R net (t 2,8, 889 candidats) ; V04 sur USDJPY, +0,050 R net (t 1,9).

## Anomalies et contrôles
- « SL 1 ATR H1 » a été remplacé par 0,5 ATR journalier avant tout calcul : l'ATR H1 de 08:00 Londres coûte 0,10 à 0,25 R en forex, et jusqu'à 1,15 R sur l'argent.
- Argent : un stop de 0,5 ATR coûte 0,10 à 0,33 R sur 2012-2023. Le filtre de coût élimine donc la plupart des signaux, et il ne reste que 49 à 255 trades pris selon la variante.
- Or 2025-2026 : le coût fixe de 0,47 $ devient presque nul (0,01 à 0,02 R, ATR de 50 à 105 $), ce qui avantage la fin de la période de validation.
- Trou de données du 17/02 au 31/07/2023 (environ 30 % des minutes manquent) : la sortie se fait sur la minute disponible suivante, à l'ouverture s'il y a un gap.
- V10 : tous les marchés entrent à la même minute. La priorité va à la tendance la plus forte ; sans cela, EURUSD serait toujours choisi.
- Recalcul indépendant (`verif.py`, autre code) de 13 trades tirés au hasard dans V01, V03, V10 et V15, dont un jour d'annonce à coûts ×2 : **13 sur 13 identiques** (entrée, sortie, brut, coût).
  Le code contrôle aussi, par des assertions : indicateurs calculés sur la veille uniquement, entrées dans les fenêtres, sorties avant 16:00 NY, risque ≥ 10 × coût.
  Trades pris : 95 à 359 par an, plausible pour 6 marchés avec la règle « 2e trade si perdant ».
- Budget : 17 variantes sur 20. Les 3 restantes n'ont pas été utilisées (engagement écrit avant les calculs).
