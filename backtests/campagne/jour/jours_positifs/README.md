# Jours positifs ou espérance ? — campagne 2 « 1 trade par jour » (18/10/2026)

Question : existe-t-il une stratégie simple, 1 trade par jour (2e seulement si le 1er perd, `lib.regle_anto`), qui donne
**beaucoup de jours positifs ET une espérance nette positive et robuste** (`lib.evaluate`) ?
Règles : docstring de `run.py`, écrite avant tout calcul. **16 variantes** sur un budget de 20 (V17-V20 étaient réservées au
contrôle de robustesse d'une variante validée : non utilisées). Données 2011-2026, coûts `lib.COST` (+ swap la nuit), 100 € par R.

Contrôles : look-ahead OK pour les 16 variantes (`run.py --lookahead` : mêmes candidats sur des données coupées au 01/01/2019) ;
non-régression : le 1er trade du jour de V01 est identique au Williams d'origine sur 2 881 jours ; 10 trades recalculés à la main
avec un code indépendant (`verif.py`) : tous identiques.

## Résultat : aucune variante validée

| Var. | Règle | Trades | Réussite | Jours + | E nette (R) | t | €/jour | €/an | DD € | Pire jour | Pire série | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V01 | Williams k=0,5 Nasdaq, sortie 16:00 (référence) | 3 479 | 45,5 % | 48,4 % | +0,040 | +2,00 | +3,38 | +882 | 12 268 | −264 | 18 j | rejetée (découverte ≤ 0, PF 1,09, frais ×2, t) |
| V02 | Williams, objectif 0,5 R | 3 274 | 64,8 % | 64,4 % | −0,005 | −0,47 | −0,40 | −105 | 11 084 | −247 | 6 j | rejetée |
| V03 | Williams, 50 % à 0,5 R, reste à 16:00 | 3 479 | 50,2 % | 53,1 % | +0,014 | +1,01 | +1,16 | +303 | 11 855 | −247 | 18 j | rejetée |
| V04 | Williams, 50 % à 0,5 R, reste à 16:00 avec stop à l'entrée | 3 281 | 64,4 % | 64,9 % | +0,026 | +2,03 | +2,08 | +543 | 7 748 | −247 | 6 j | rejetée (découverte −0,022, PF 1,096, frais ×2, t) |
| V05 | Repli −0,5 ATR en tendance haussière (NQ + SP) | 1 198 | 53,3 % | 53,2 % | −0,047 | −3,26 | −1,37 | −359 | 6 713 | −210 | 12 j | rejetée |
| V06 | Repli −0,25 ATR en tendance haussière (NQ + SP) | 2 034 | 66,1 % | 66,0 % | −0,039 | −4,28 | −1,94 | −507 | 8 861 | −107 | 7 j | rejetée |
| V07 | RSI2 H1 dans le sens de la tendance, sortie SMA5 H1 | 1 736 | 55,1 % | 55,5 % | −0,030 | −3,00 | −1,28 | −334 | 5 631 | −210 | 7 j | rejetée |
| V08 | RSI2 H1 dans le sens de la tendance, objectif 0,25 ATR | 1 724 | 60,3 % | 60,0 % | −0,035 | −4,03 | −1,45 | −378 | 6 514 | −209 | 7 j | rejetée |
| V09 | Gap 0,1-0,5 ATR joué vers la clôture de la veille, stop 1 ATR | 2 491 | 67,2 % | 67,3 % | −0,028 | −3,47 | −1,68 | −440 | 7 103 | −107 | 6 j | rejetée |
| V10 | Idem V09, seulement dans le sens de la tendance | 1 065 | 69,0 % | 69,1 % | −0,026 | −2,10 | −0,68 | −179 | 3 233 | −107 | 5 j | rejetée |
| V11 | RSI2 journalier → achat à l'ouverture J+1, sortie 16:00 | 305 | 51,8 % | 51,8 % | +0,000 | +0,01 | +0,00 | +1 | 1 056 | −106 | 6 j | rejetée |
| V12 | RSI2 journalier → une nuit (15:55 → 09:30) | 313 | 57,2 % | 57,2 % | +0,033 | +1,06 | +0,25 | +65 | 947 | −178 | 5 j | rejetée |
| V13 | **Contrôle sans signal** : achat à l'ouverture, +0,25 / −1 ATR | 3 764 | 67,9 % | 67,9 % | −0,026 | −3,87 | −2,40 | −625 | 10 260 | −108 | 5 j | rejetée |
| V14 | Nuit après une séance baissière en tendance haussière | 1 535 | 54,3 % | 54,3 % | −0,006 | −0,43 | −0,21 | −54 | 3 188 | −283 | 6 j | rejetée |
| V15 | Retour au TWAP (VWAP sans volume), stop 1 ATR | 1 246 | 56,3 % | 57,2 % | −0,033 | −2,63 | −1,01 | −264 | 4 868 | −210 | 9 j | rejetée |
| V16 | RSI2 journalier + sortie « 1re ouverture profitable » (swing ≤ 5 séances) | 245 | 80,4 % | 80,4 % | +0,130 | +2,18 | +0,77 | +202 | 1 557 | −557 | 3 j | rejetée (t < 3 seulement) |

€/jour = moyenne sur tous les jours ouvrés (0 € les jours sans trade). Pire série = jours tradés perdants consécutifs.

## Ce qu'on en retient
1. **Des jours positifs, on en a sans rien faire.** Le contrôle sans signal V13 donne 68 % de jours positifs et perd 625 €/an (t −3,9).
   Un objectif proche et un stop loin suffisent à produire ce taux. Sur les 8 variantes à ≥ 60 % de jours positifs, 6 ont une
   espérance négative : leur taux de réussite est 0,4 à 5,9 points **sous** le taux d'équilibre (`analyse.txt`).
2. **Il n'y a aucun lien entre le taux de jours positifs et l'espérance d'une variante à l'autre** (Spearman −0,07). Ce qui
   compte, c'est le signal. **Pour un même signal**, rapprocher l'objectif monte le taux de jours positifs et baisse l'espérance :
   - Williams : 48 % de jours positifs à E +0,040 (V01) → 64 % à E −0,005 avec un objectif de 0,5 R (V02) ;
   - RSI2 swing : 74,5 % de trades gagnants à E +0,506 R (référence validée) → 80,4 % à E +0,130 avec la sortie bail-out (V16),
     soit −74 % d'espérance pour +6 points de réussite, avec en plus des pertes allant jusqu'à −5,6 R net (oct. 2018), faute
     de stop.
3. **Le retour à la moyenne intraday sur les indices perd, même avant frais.** Repli, RSI2 H1, gap et TWAP ont une E brute de
   −0,005 à −0,022 R et un t de −2,1 à −4,3. C'est cohérent avec la campagne 1 (momentum intraday).
4. **Meilleur compromis : V04** (Williams, 50 % de la position à 0,5 R puis stop du reste ramené à l'entrée). Par rapport à
   V01 : 65 % de jours positifs au lieu de 48 %, pire série de 6 jours au lieu de 18, drawdown −37 %, espérance −35 %.
   Elle est **rejetée avec le coût du protocole** (1,5 pt) : 2011-2018 est négatif, car 1,5 pt représentait 4,7 % de
   l'amplitude journalière médiane du Nasdaq en 2011, contre 0,4 % en 2026.
   *Information hors verdict, mêmes trades* : avec 0,75 pt (≈ future NQ), E +0,056, t 4,38, tous les critères passent ; avec un
   coût proportionnel de 1,25 pb (l'hypothèse qui a validé le Williams de base), E +0,060, t 4,64, DD 2 587 €. Avec le coût
   du protocole, 2019-2026 seul donne E +0,078 et t 4,32. C'est donc un candidat **conditionnel** : il dépend de l'hypothèse
   de coût, et le contrôle de robustesse (exécution décalée d'une minute) reste à faire.
5. **Références hors budget** (trades existants des stratégies swing validées, avec la règle du jour) : le RSI2 a 74,5 % de
   trades gagnants, E +0,506 et t 6,3 ; les 3 baisses ont 73,6 %, E +0,213 et t 3,6. Ce sont les seules stratégies du dépôt qui
   combinent un taux de réussite élevé et une espérance validée. Mais elles ne tradent que 5 à 7 % des jours ouvrés.
6. **Objectif de 50-100 €/jour** : la meilleure variante intraday rapporte environ 2-3 € par jour ouvré, à 100 € de risque
   par trade.

## Anomalies
- Le trou 15:15-16:15 NY (mars et fin octobre) signalé par `retour_moyenne` n'existe plus dans le cache actuel. Les séances du
  17/03/2026 et du 29/10/2025 sont complètes ; il ne reste que la pause CFD normale de 16:14 à 18:00.
- Avec un coût fixe en points, le coût en R varie fortement dans le temps. La famille Williams perd en 2011-2013
  (V01 : −9 002 €), puis gagne chaque année de 2018 à 2026.
- Séances exclues : fériés US où le CFD cote jusqu'à 13:00 (209-210 minutes), demi-séances, trous de données (117 séances
  Nasdaq en 2023). Il n'y a pas de calendrier d'annonces avant 2020, donc les coûts ×2 des jours d'annonce ne sont pas
  appliqués (le test « frais ×2 » les couvre).
- Multi-marchés : en cas d'égalité, la règle du jour prend le Nasdaq. Le S&P garde donc peu de trades après la règle
  (V14 : 252 contre 1 283), alors que les candidats sont comparables (1 225 contre 1 283). Ce n'est pas un problème de données.

Fichiers : `run.py` (règles + calcul), `results.json` (lib.evaluate + `jour` + `taux_reussite` + `regles` par variante),
`trades.csv.gz` (trades pris), `verif.py` (recalculs à la main), `analyse.py` / `analyse.txt` (structure gain/perte, corrélation,
sensibilité au coût, références).
