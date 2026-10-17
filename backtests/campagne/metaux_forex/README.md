# Campagne métaux + forex : 19 variantes sur 25, aucune validée

Règles : docstring de `run.py`, écrite avant les calculs. Résultats complets : `results.json`. Trades : `trades/Vxx.csv.gz`.
Données : cache corrigé en vrai UTC (`data_cache/FIXED`) ; période 2011-2026 ; 100 € par R ; coûts `lib.COST`, swap et coûts ×2 les jours d'annonce macro.

| # | Variante | Trades | E nette (R) | PF | Découv. | Valid. | t | Résultat | DD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V01 | Gotobi USDJPY, achat 08:00 → 09:55 JST | 1110 | +0,001 | 1,01 | +0,003 | −0,002 | +0,09 | +59 € | 532 € |
| V02 | Gotobi USDJPY, vente 09:56 → 12:00 JST | 1128 | −0,004 | 0,94 | −0,001 | −0,008 | −0,53 | −494 € | 833 € |
| V03 | Témoin non-Gotobi, achat 08:00 → 09:55 | 2907 | −0,019 | 0,76 | −0,021 | −0,016 | −5,40 | −5 421 € | 5 653 € |
| V04 | Fix WM de fin de mois, retournement (4 FX) | 729 | −0,007 | 0,92 | −0,002 | −0,013 | −0,90 | −515 € | 629 € |
| V05 | Fix WM quotidien, retournement (4 FX) | 15085 | −0,022 | 0,76 | −0,015 | −0,029 | −11,9 | −33 048 € | 33 190 € |
| V06 | Cassure du range asiatique (4 FX) | 14419 | −0,013 | 0,97 | −0,001 | −0,024 | −1,19 | −18 300 € | 28 332 € |
| V07 | Cassure du range asiatique (or) | 3535 | +0,009 | 1,02 | +0,019 | −0,003 | +0,39 | +3 024 € | 7 478 € |
| V08 | Or, retournement au fix PM (15:00 Londres) | 3948 | −0,023 | 0,78 | −0,026 | −0,020 | −5,41 | −9 044 € | 10 029 € |
| V09 | Or, retournement au fix AM (10:30 Londres) | 3983 | −0,022 | 0,68 | −0,029 | −0,014 | −8,65 | −8 686 € | 9 030 € |
| V10 | Or, achat de la séance asiatique (19h → 03h NY) | 4007 | −0,010 | 0,91 | −0,022 | +0,002 | −2,18 | −4 078 € | 6 066 € |
| V11 | Argent, achat de la séance asiatique | 3999 | −0,080 | 0,49 | −0,104 | −0,054 | −16,8 | −31 807 € | 32 830 € |
| V12 | Or, vente de la séance COMEX (08:20 → 13:30) | 3908 | −0,021 | 0,88 | −0,024 | −0,018 | −2,81 | −8 347 € | 9 200 € |
| V13 | Or, momentum de l'ouverture COMEX | 3900 | −0,021 | 0,87 | −0,034 | −0,008 | −3,15 | −8 292 € | 9 380 € |
| V14 | Ratio or/argent, z20 ±2 | 135 | −0,606 | 0,47 | −0,405 | −0,856 | −2,37 | −8 175 € | 9 010 € |
| V15 | Grosse bougie H1, momentum (6 instruments) | 18661 | −0,031 | 0,78 | −0,030 | −0,031 | −11,8 | −57 270 € | 57 601 € |
| V16 | Grosse bougie H1, retournement (6 instruments) | 18661 | −0,037 | 0,74 | −0,039 | −0,035 | −14,2 | −68 976 € | 70 329 € |
| **V17** | **Inside day or, 16 ans** | **627** | **+0,093** | **1,29** | **+0,097** | **+0,088** | **+2,35** | **+5 826 €** | **1 560 €** |
| V18 | Inside day (4 FX) | 2145 | +0,006 | 1,02 | +0,009 | +0,003 | +0,36 | +1 369 € | 2 529 € |
| V19 | Inside day (argent) | 609 | −0,063 | 0,83 | −0,092 | −0,032 | −1,69 | −3 835 € | 5 763 € |

## Verdicts
- **Aucune variante ne passe le critère.**
- **V17 (inside day sur l'or)** est la seule piste sérieuse. Elle est positive en découverte comme en validation, avec un PF de 1,29, une espérance encore positive avec frais doublés (+0,052) et sans les 10 meilleurs trades (+0,030), et 12 années positives sur 16. Elle échoue **uniquement sur le t de Student (2,35 < 3)**. Sur 2020-2026, on retrouve le lot 3 (250 trades, +0,10 R). La même règle ne marche pas sur l'argent (V19) ni sur le forex (V18), ce qui affaiblit l'idée d'un effet général.
- Les effets de microstructure de la littérature (Gotobi et fix de Tokyo, fix WM, fix de l'or) n'apparaissent pas une fois les coûts déduits. Le Gotobi brut tourne autour de +0,02 R, absorbé par un coût de 0,024 R. Les retournements aux fix sont même négatifs **en brut**.
- Les gros ou nombreux trades intraday sur ATR (V05, V15, V16) perdent à peu près le coût : il n'y a aucun biais directionnel exploitable.

## Mises en garde
- Avant 2020, les jours de coût doublé ne comptent que le NFP, approximé par le 1er vendredi du mois (pas de calendrier CPI/FOMC). Les jours fériés japonais sont ignorés pour le Gotobi.
- V14 : 1 R = moyenne des ATR en % des deux jambes. C'est une convention : coûts et swap des deux jambes ≈ 0,34 R par trade.
- Anomalie de données signalée et corrigée à la source avant ces calculs : l'ancien cache avait un décalage d'une heure en heure d'été US. En 2023, environ 20 000 à 23 000 minutes par mois de février à juillet, contre environ 31 000 habituellement (données clairsemées).
