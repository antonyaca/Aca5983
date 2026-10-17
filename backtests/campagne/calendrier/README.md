# Famille « calendrier, saisonnalité, horaires de séance » : résultats

Règles : docstring de `run.py`, écrit avant tout calcul. Les calculs ont été lancés une seule fois, sur les données corrigées (drapeau `data_cache/FIXED` du 17/10 à 17:31).
Le dossier contient aussi `results.json` (les 21 variantes, avec la clé `regles`), `trades.csv.gz` et `anomalies.txt`.
Budget : 21 variantes sur 25. Critère : `lib.evaluate`, avec la période de découverte 2011-2018 (D) et la période de validation 2019-2026 (V).

**Verdict : aucune variante ne passe le critère. Aucune ne dépasse t = 1,9.**

| Var. | Règle (résumé) | Trades | E nette (R) | PF | D | V | Frais ×2 | t | Résultat | DD |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 | Fin de mois (J-2 → J+3), SP500 | 176 | +0,052 | 1,08 | −0,066 | +0,173 | −0,080 | 0,38 | 922 € | 2 204 € |
| V2 | Fin de mois, NASDAQ100 | 187 | +0,123 | 1,22 | +0,063 | +0,186 | +0,023 | 1,01 | 2 292 € | 1 226 € |
| V3 | Fin de mois, FTSE100 | 184 | −0,037 | 0,94 | −0,151 | +0,080 | −0,155 | −0,30 | −672 € | 2 737 € |
| V4 | Fin de mois, NIKKEI225 | 184 | −0,218 | 0,77 | −0,270 | −0,166 | −0,348 | −1,34 | −4 007 € | 5 185 € |
| V5 | Fin de mois, portefeuille des 4 indices | 185 | −0,021 | 0,97 | −0,115 | +0,079 | −0,141 | −0,18 | −381 € | 1 966 € |
| V6 | Veille de jour férié, SP500 | 135 | +0,082 | 1,46 | −0,006 | +0,164 | +0,037 | 1,66 | 1 110 € | 507 € |
| V7 | Veille de jour férié, NASDAQ100 | 142 | +0,059 | 1,31 | −0,000 | +0,119 | +0,026 | 1,23 | 844 € | 627 € |
| V8 | Veille de jour férié, FTSE100 | 93 | +0,037 | 1,20 | −0,006 | +0,079 | −0,001 | 0,68 | 344 € | 379 € |
| V9 | Veille de jour férié, NIKKEI225 | 183 | −0,026 | 0,92 | −0,068 | +0,013 | −0,086 | −0,45 | −476 € | 1 273 € |
| V10 | Avant décision FOMC, de la clôture de la veille à 12:00, SP500 | 113 | +0,060 | 1,38 | +0,056 | +0,064 | −0,014 | 1,26 | 681 € | 242 € |
| V11 | Avant décision FOMC, NASDAQ100 | 121 | +0,083 | 1,57 | +0,018 | +0,155 | +0,027 | 1,82 | 1 001 € | 358 € |
| V12 | Semaine d'expiration des options, SP500 | 177 | −0,032 | 0,95 | +0,113 | −0,175 | −0,178 | −0,26 | −564 € | 3 087 € |
| V13 | Semaine d'expiration des options, NASDAQ100 | 167 | +0,002 | 1,00 | +0,016 | −0,010 | −0,103 | 0,02 | 33 € | 2 103 € |
| V14 | Halloween, de novembre à avril (portefeuille) | 90 | +0,266 | 1,26 | +0,344 | +0,177 | −0,207 | 0,90 | 2 392 € | 1 978 € |
| V15 | Nuit, FTSE100 | 3 891 | −0,032 | 0,82 | −0,023 | −0,042 | −0,075 | −4,41 | −12 604 € | 12 853 € |
| V16 | Nuit, NIKKEI225 | 3 706 | −0,027 | 0,90 | −0,048 | −0,006 | −0,091 | −2,36 | −9 949 € | 13 012 € |
| V17 | Or, achat 18:00 → 03:00 NY (session Asie) | 3 978 | +0,007 | 1,06 | −0,012 | +0,027 | −0,016 | 1,38 | 2 640 € | 3 634 € |
| V18 | Or, vente 08:20 → 13:30 NY (séance COMEX) | 3 908 | −0,020 | 0,89 | −0,023 | −0,017 | −0,043 | −2,61 | −7 751 € | 8 617 € |
| V19 | Or, vente 14:30 → 15:30 Londres (fix de l'après-midi) | 3 963 | −0,021 | 0,79 | −0,026 | −0,015 | −0,044 | −5,32 | −8 194 € | 8 952 € |
| V20 | Dernière heure du vendredi, SP500 | 728 | −0,021 | 0,77 | −0,038 | −0,004 | −0,050 | −2,44 | −1 513 € | 1 565 € |
| V21 | Vente du vendredi soir au lundi soir, SP500 | 645 | −0,094 | 0,74 | −0,060 | −0,127 | −0,131 | −2,82 | −6 065 € | 6 249 € |

## Ce qu'il faut retenir
- **Fin de mois sur 16 ans :** l'effet ne tient pas en dehors de 2019-2026. Il est négatif sur le SP500 en 2011-2018 et le t ne dépasse pas 1 sur le Nasdaq. Il ne fonctionne pas sur le FTSE ni sur le Nikkei, ni en portefeuille. Le résultat positif obtenu sur 2020-2026 tenait à la période testée.
- **Effets les plus prometteurs, sans être validés :** la veille de jour férié et l'avant-décision FOMC sur les indices US. Leur profit factor est élevé (1,3 à 1,6) et leur drawdown faible. Mais il y a trop peu de trades (7 à 9 par an), le t est de 1,2 à 1,8 et la découverte est nulle ou à peine positive. Le gain vient de 2019-2026.
- **Halloween :** 90 trades seulement, sous le minimum de 100. Le swap sur un mois entier rend le résultat négatif dès que les frais sont doublés.
- **Effets inverses franchement négatifs (t ≤ −2,4) :** la vente de l'or pendant la séance COMEX, la vente autour du fix de Londres, la dernière heure du vendredi et la vente du week-end perdent de l'argent. Ces chiffres ne montrent pas d'effet exploitable à l'inverse, car ces fenêtres suivent surtout la hausse de fond des marchés (l'or et le SP500 ont monté sur la période). Le rendement de nuit ne couvre pas les frais et le swap sur le FTSE et le Nikkei.

## Mises en garde
- **Calendrier :** les dates viennent des calendriers officiels prévisibles (`exchange_calendars` : XNYS, XLON, XTKS, installé dans le scratchpad, hors du dépôt), pas des données. Les fermetures imprévisibles sont exclues des signaux : l'ouragan Sandy en 2012 et la panne de la bourse de Tokyo du 01/10/2020.
- **Dates FOMC 2011-2019 :** relevées sur les pages officielles `federalreserve.gov/monetarypolicy/fomchistorical20XX.htm`. Seules les réunions programmées sont retenues, sans les conférences téléphoniques ni les réunions extraordinaires. Les dates 2020-2026 sont reprises de `events/backtest.py`.
- **Doublement des coûts les jours d'annonce :** il n'est appliqué qu'aux variantes FOMC. Les dates NFP et CPI d'avant 2020 ne sont pas disponibles de source vérifiée.
- **Données manquantes :** des séances sont absentes ou incomplètes, et les trades concernés sont ignorés (détail dans `anomalies.txt`).
  - SP500 2023 : 59 séances incomplètes, avec des trous de plusieurs heures en février-mars, par exemple une ouverture à 10:00 ou 12:00.
  - SP500 2014 et 2017 : environ 30 séances incomplètes chaque année.
  - Nikkei 2011 : 30 séances incomplètes.
  - Il y a aussi des jours de données sur des jours fériés de bourse (le CFD cote) : ils sont ignorés.
- **Clôture des séances réduites :** ces jours-là, la clôture retenue est le dernier prix du CFD avant 16:00 (ou avant 16:30 et 15:00 selon le marché), pas la clôture du marché au comptant.
