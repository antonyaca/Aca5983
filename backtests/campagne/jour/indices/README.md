# « 1 trade par jour » — indices autour de l'ouverture (18/10/2026)

Règles fixées avant calcul dans la docstring de `run.py`, 20 variantes sur 20 autorisées. Chaque variante figure dans `results.json`
(`lib.evaluate` des trades pris après `lib.regle_anto` + `jour` = `lib.stats_jour` + `regles` + diagnostics). Les trades pris sont dans
`trades.csv.gz`, tous les candidats dans `candidats.csv.gz`. Cadre : 100 € par R, coûts `lib.COST` en points (×2 les jours FOMC pour le
Nasdaq et le S&P), découverte 2011-2018 / validation 2019-2026.

**Aucune variante validée.**

| Var. | Règle | Trades | E nette (R) | t | Jours + % | €/jour | Pire série | Verdict |
|---|---|---|---|---|---|---|---|---|
| V01 | Bougie M15 d'ouverture 1:1, Nasdaq | 3 791 | −0,122 | −7,5 | 50 | −11,22 | 9 j | ✘ |
| V02 | Bougie M15 1:1, FTSE | 3 774 | −0,116 | −7,1 | 51 | −10,60 | 9 j | ✘ |
| V03 | Bougie M15 1:1, 4 indices (1er signal) | 5 976 | −0,200 | −15,0 | 52 | −29,00 | 10 j | ✘ |
| V04 | Bougie M15 1:2, Nasdaq | 3 791 | −0,099 | −4,5 | 37 | −9,16 | 15 j | ✘ |
| V05 | ORB 15 min 1:2, Nasdaq | 5 346 | −0,042 | −2,5 | 50 | −5,51 | 12 j | ✘ |
| V06 | ORB 60 min 1:1, Nasdaq | 3 576 | −0,016 | −1,2 | 51 | −1,40 | 10 j | ✘ |
| V07 | ORB 60 min 1:1, S&P | 3 814 | −0,044 | −3,3 | 50 | −4,07 | 9 j | ✘ |
| V08 | ORB 60 min 1:1, FTSE | 3 527 | −0,038 | −2,6 | 50 | −3,30 | 10 j | ✘ |
| V09 | ORB 60 min 1:1, Nikkei | 3 320 | −0,071 | −5,2 | 48 | −5,73 | 12 j | ✘ |
| V10 | ORB 60 min 1:1, 4 indices | 5 834 | −0,053 | −4,9 | 58 | −7,47 | 8 j | ✘ (piège) |
| V11 | ORB 60 min 1:2, Nasdaq | 3 576 | −0,015 | −1,1 | 49 | −1,33 | 10 j | ✘ |
| V12 | ORB 60 min 1:1 + SMA200, Nasdaq | 1 838 | −0,019 | −1,1 | 52 | −0,86 | 8 j | ✘ |
| V13 | Williams 0,5 objectif 1:1, Nasdaq ⚑ | 3 390 | +0,020 | +1,4 | 53 | +1,63 | 12 j | ✘ (D −0,042) |
| V14 | Williams 1:1, S&P | 3 393 | −0,035 | −2,4 | 51 | −2,85 | 10 j | ✘ |
| V15 | Williams 1:1, Nikkei | 3 193 | −0,076 | −5,1 | 50 | −5,88 | 10 j | ✘ |
| V16 | Williams 1:1, 4 indices | 5 646 | −0,079 | −7,1 | 56 | −10,90 | 8 j | ✘ (piège) |
| V17 | Williams 1:1 + SMA200, Nasdaq ⚑ | 1 656 | +0,021 | +1,1 | 53 | +0,83 | 9 j | ✘ (D −0,027) |
| V18 | 1er repli EMA20 M5 (sens des 30 premières min), Nasdaq | 3 512 | −0,026 | −2,0 | 50 | −2,20 | 10 j | ✘ |
| V19 | 1er repli EMA20 M5, S&P | 3 472 | −0,041 | −3,1 | 48 | −3,44 | 13 j | ✘ |
| V20 | Gap & go confirmé (gap ≥ 0,25 ATR + bougie M15), Nasdaq | 881 | +0,042 | +1,7 | 55 | +0,90 | 9 j | ✘ (t < 3) |

⚑ = variante d'une stratégie déjà validée (Williams k = 0,5 Nasdaq). La colonne « Jours + » compte les jours positifs parmi les jours tradés.
« Piège » : la règle du 2e trade fait monter le taux de jours positifs alors que l'espérance reste négative.

## Ce qu'on en retient
- L'edge **brut** est souvent légèrement positif (+0,01 à +0,11 R). Mais en 2011-2018, les frais fixes en points coûtent de 0,06 à
  0,32 R par trade et l'absorbent : la période de découverte est négative pour toutes les variantes sauf V20.
- La bougie M15 d'ouverture (V01-V04) a un edge brut nul, avec des frais de 0,15 R (Nasdaq) à 0,3 R (S&P, Nikkei) avant 2019.
- L'objectif fixe ne sauve ni l'ORB ni le repli sur l'EMA20. Le Williams 1:1 garde le meilleur brut (+0,06 R en découverte,
  +0,11 R en validation).
- L'objectif d'Anto, 50 à 100 €/jour, représente 0,5 à 1 R par jour. Le meilleur résultat testé est +1,63 €/jour (V13).

## Les 3 meilleures non validées
1. **V20 Gap & go confirmé Nasdaq** : seule variante positive sur les deux périodes (D +0,019 / V +0,062), et encore positive avec les frais ×2
   (+0,009). Mais t = 1,66, elle ne trade que 21 % des jours, rapporte +235 €/an pour un drawdown de 1 128 €, avec 11 années positives sur 16.
2. **V13 Williams 1:1 Nasdaq** ⚑ : +426 €/an, drawdown de 8 965 €, 11 années positives sur 16, validation +0,087 R.
3. **V17 Williams 1:1 + SMA200 Nasdaq** ⚑ : +217 €/an, drawdown de 3 805 €.

## Sensibilité au coût (hors protocole, information seulement)
Clé `sensibilite_cout_proportionnel` (ajoutée après lecture des résultats, calculée pour toutes les variantes Nasdaq). Avec un coût de
1,25 pb du prix, convention qui avait servi à valider le Williams :
- le contrôle Williams avec sortie en clôture passe (t 3,47) ;
- **V13 passerait tous les critères** (E +0,055, t 3,85, D +0,028, V +0,084) ;
- V17 (t 2,64) et V20 (t 2,32) restent non validées.

Avec les coûts fixes du protocole, le **Williams de référence lui-même échoue** (t 1,94, D −0,008). Son statut « validé » dépend donc de
l'hypothèse de coût sur 2011-2018. V13 n'est pas un nouvel edge : c'est le même signal, avec un objectif 1:1 et un 2e trade.

## Contrôles
- **Moteur** : le contrôle Williams avec sortie en clôture reproduit 99,3 % des trades de `three_strats` à l'identique, sur 2 857 jours
  communs. Les 20 écarts tombent tous le lendemain d'une clôture anticipée, que je traite ici à l'heure officielle (13:00).
- **Recalcul à la main** : 8 trades recalculés depuis les minutes brutes avec un code indépendant (V06 ×2, V13, V20, V01, V18, V02 FTSE,
  V09 Nikkei), tous identiques. Pour V18 (04/01/2024), le premier contrôle avait échoué à cause d'un bug du script de vérification, pas
  du backtest : les horodatages sont en `datetime64[s]` et non en nanosecondes. Une fois corrigé, le trade est retrouvé au centime.
- **Look-ahead** : ATR14, SMA200 et amplitude de la veille sont décalés d'une séance, et les entrées se font après la bougie ou le range.
  L'EMA20 de la bougie signal, recalculée sur des données coupées à 10:05, est égale à la valeur utilisée.
- **Règle du jour** : jamais plus de 2 trades, jamais de 2e trade après un gain, et le 2e entre toujours après la sortie du 1er.
- **Fréquences** : environ 245 trades/an (bougie M15), 230 (ORB 60), 218 (Williams), 58 (gap & go), 370 (versions 4 indices).
- Le CFD Nasdaq suit l'indice cash (écart ±0,06 %) : il n'y a pas de faux gap de roll.

## Anomalies de données
- Trou du 17/02 au 31/07/2023 : environ 110 séances perdues par marché.
- Vendredis d'échéance trimestrielle (Nasdaq, S&P) : aucune cotation pendant les 10 à 24 premières minutes. La séance est écartée, et il
  n'y a pas de trade Williams ni gap le lundi suivant.
- Nikkei : 244 jours de cotation CFD tombent hors du calendrier (fériés japonais), et 125 séances ont moins de 50 % des minutes
  (surtout 2011-2012).
- Tokyo ferme à 15:30 depuis le 05/11/2024 ; la fenêtre 09:00-15:00 est conservée, conformément à la consigne.
