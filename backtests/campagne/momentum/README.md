# Famille cassure / momentum / suivi de tendance — campagne oct. 2026

Règles fixées avant calcul dans le docstring de `run.py`. Les données ont été relancées après la correction des horodatages
(fichier `data_cache/FIXED` du 17/10 17:31) : ce sont les seuls résultats calculés. 22 variantes sur les 25 autorisées.
Résultats complets dans `results.json`, trades dans `trades.csv.gz`.
Période 2011-2026 : découverte (D) 2011-2018, validation (V) 2019-2026. 1 R = 100 €.

**Aucune variante validée.**

| Code | Variante | Trades | E brute | E nette | PF net | D | V | t | Résultat | DD |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | GHLZ (1re demi-heure → dernière) S&P 500 | 3100 | +0,003 | −0,020 | 0,72 | −0,024 | −0,017 | −6,1 | −6 155 € | 6 173 € |
| A2 | GHLZ Nasdaq | 3608 | −0,001 | −0,023 | 0,69 | −0,029 | −0,016 | −8,0 | −8 227 € | 8 543 € |
| A3 | GHLZ FTSE | 3747 | +0,002 | −0,018 | 0,73 | −0,017 | −0,019 | −7,2 | −6 724 € | 6 800 € |
| A4 | GHLZ Nikkei | 3477 | +0,003 | −0,038 | 0,47 | −0,048 | −0,029 | −15,5 | −13 133 € | 13 255 € |
| A5 | Baltussen et al. (veille → 15:30) S&P | 3112 | +0,008 | −0,016 | 0,77 | −0,018 | −0,014 | −4,8 | −4 828 € | 4 870 € |
| A6 | Baltussen et al. Nasdaq | 3614 | +0,001 | −0,021 | 0,71 | −0,030 | −0,010 | −7,3 | −7 473 € | 7 566 € |
| A7 | GHLZ S&P, volatilité haute | 1290 | +0,009 | −0,007 | 0,90 | −0,006 | −0,007 | −1,3 | −839 € | 1 192 € |
| B1 | Williams k=0,5 FTSE | 2898 | −0,026 | −0,080 | 0,83 | −0,061 | −0,099 | −3,8 | −23 154 € | 23 936 € |
| B2 | Williams Nikkei | 2922 | +0,118 | −0,027 | 0,94 | −0,058 | +0,001 | −1,2 | −7 969 € | 11 525 € |
| B3 | Williams or (COMEX) | 2878 | +0,047 | −0,046 | 0,91 | −0,063 | −0,026 | −1,8 | −13 141 € | 13 141 € |
| B4 | Williams GBPUSD (Londres) | 2975 | +0,048 | −0,013 | 0,97 | +0,016 | −0,046 | −0,6 | −4 005 € | 9 859 € |
| B5 | Williams FTSE + SMA200 | 1374 | −0,060 | −0,114 | 0,77 | −0,074 | −0,151 | −3,7 | −15 671 € | 16 586 € |
| C1 | ORB 30 min achats FTSE | 1936 | −0,006 | −0,070 | 0,88 | −0,095 | −0,044 | −2,4 | −13 531 € | 15 947 € |
| C2 | ORB 30 min achats Nikkei | 1854 | +0,133 | −0,018 | 0,96 | −0,068 | +0,027 | −0,6 | −3 294 € | 9 585 € |
| D1 | Opening drive S&P | 287 | −0,037 | −0,087 | 0,83 | −0,071 | −0,094 | −1,3 | −2 483 € | 3 127 € |
| D2 | Opening drive FTSE | 701 | +0,012 | −0,034 | 0,93 | −0,069 | +0,004 | −0,8 | −2 409 € | 4 467 € |
| E1 | Range asiatique → Londres GBPUSD | 3715 | +0,079 | +0,002 | 1,00 | −0,010 | +0,015 | +0,1 | +805 € | 8 594 € |
| E2 | Range asiatique → Londres EURUSD | 3740 | +0,040 | −0,029 | 0,95 | −0,003 | −0,057 | −1,2 | −10 885 € | 15 648 € |
| E3 | Range asiatique → Londres or | 3401 | +0,095 | +0,020 | 1,04 | +0,029 | +0,010 | +0,9 | +6 889 € | 5 271 € |
| F1 | TSMOM 12 mois mensuel, 10 marchés | 1840 | +0,266 | −0,058 | 0,96 | −0,129 | +0,012 | −0,7 | −10 598 € | 28 600 € |
| F2 | TSMOM 12 mois forex + métaux | 1128 | +0,124 | −0,165 | 0,88 | −0,242 | −0,087 | −1,6 | −18 661 € | 28 237 € |
| G1 | Expansion de volatilité, 5 jours, 4 indices + or | 475 | −0,059 | −0,091 | 0,76 | −0,144 | −0,035 | −2,4 | −4 313 € | 4 544 € |

## Lecture
- **Momentum intraday (A)** : l'edge brut est nul (≈ +0,00 R, PF brut 0,98 à 1,17). Les t très négatifs ne traduisent pas
  une inversion : ils viennent du coût fixe (≈ 0,02 R) prélevé sur des gains minuscules et peu dispersés. L'effet publié
  (SPY 1993-2013) n'apparaît pas sur les CFD 2011-2026.
- **Williams, ORB et opening drive hors Nasdaq (B, C, D)** : il existe parfois un edge brut (Nikkei, or, GBPUSD), mais le spread
  le fait disparaître, et il est négatif en découverte. Le filtre SMA200 dégrade le résultat sur le FTSE.
- **Range asiatique (E)** : l'or (E3) est la seule variante positive en découverte et en validation, mais avec t = 0,9 et
  PF 1,04, elle redevient négative si l'on double les frais.
- **TSMOM (F)** : l'edge brut est réel (+0,27 R par mois et par marché), mais le swap long des indices (≈ 0,3 R par mois)
  l'absorbe entièrement. C'est le même constat que pour l'Ichimoku en portefeuille.

## Les 3 meilleures non validées
E3 (or, range asiatique, +6 889 €, t 0,9), E1 (GBPUSD, range asiatique, +805 €, t 0,1), et F1 (TSMOM, brut fort mais net négatif).

## Mises en garde et anomalies de données
- **Trou de données février-juillet 2023** sur tous les marchés (≈ 30 % de minutes en moins) : environ la moitié des séances
  2023 est écartée.
- **S&P 500 : séances incomplètes en 2012-2014 et 2017** (102 à 164 séances retenues par an, contre ≈ 245 ensuite).
- **Nikkei** : avant 2019, les cotations CFD sont clairsemées. Le seuil de séance a été abaissé à 50 % (décidé avant le calcul).
- Le doublement des coûts les jours d'annonce macro n'est pas appliqué, faute de calendrier antérieur à 2020 dans le dépôt.
- Contrôles effectués : deux trades vérifiés à la main sur les données M1 brutes (GHLZ S&P du 15/03/2024, Williams FTSE du
  04/04/2025). Les R extrêmes correspondent à des journées réelles (Brexit 24/06/2016, 23/03/2020). Il n'y a pas de look-ahead :
  ATR, SMA et médianes sont décalés d'une séance, et l'entrée se fait toujours après le signal.
