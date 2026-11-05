# Pullback structurel M15 Nasdaq — la méthode du replay (05/11/2026)

Méthode appliquée en replay TradingView avec Anto : structure M15 (sommets/creux), cassure, pullback sur le niveau
cassé, entrée sur clôture M15 de confirmation, SL derrière le pullback, TP en multiple de R. Règles complètes fixées
avant calcul dans `run.py`. NASDAQ100 2011-2026, 100 € de risque fixe, coût 1,5 pt, aucune position la nuit.
21 variantes : 6 séances × RR 1,5 / 2 / 2,5, + filtre stochastique, + filtre EMA 200, + entrée en limite aveugle.

## Résultat : aucune variante validée
| Variante (règle d'Anto) | Trades | Brut / trade | Net / trade (1,5 pt fixe) | Net (coût ∝ prix) | t (∝ prix) |
|---|---|---|---|---|---|
| Journée 08-20 h, RR 2 | 3 091 | −0,01 R | −0,13 R | −0,06 R | −2,3 |
| Londres 09-12 h, RR 2 | 718 | −0,11 R | −0,23 R | −0,16 R | −3,2 |
| **US 15:30-18 h, RR 2,5** | 788 | **+0,10 R** | −0,01 R | +0,07 R | 1,3 |
| Après-midi 14-20 h, RR 2,5 | 1 726 | +0,06 R | −0,05 R | +0,03 R | 0,7 |
| Asie 01-07 h, RR 2 | 1 008 | −0,05 R | −0,19 R | −0,13 R | −3,0 |
| Limite aveugle (journée, RR 2) | 3 820 | −0,00 R | −0,14 R | −0,07 R | −2,9 |

- Le signal n'a un avantage brut qu'à l'ouverture US (15:30-18:00 Paris) ; le matin et la nuit, il perd avant frais.
- Même la meilleure (US RR 2,5) reste non significative : t 1,3 (seuil 3), ≈ +380 €/an avec la règle d'Anto, pire
  mois −844 €, 39 % de jours positifs. Loin de Williams k 0,5 (≈ 1 350 €/an) et du portefeuille validé (≈ 3 200 €/an).
- Confirmation vs limite aveugle : la clôture de confirmation ne crée pas d'edge, elle filtre un peu (−0,13 vs −0,14 R).
- Filtres stochastique et EMA 200 : pas d'amélioration nette.
- La série du replay (+620 € en ~6 trades) est compatible avec le hasard sur un signal à espérance ≈ 0.

Fichiers : `results.json` (21 variantes + règle d'Anto), `trades.csv.gz`, `candidats.csv.gz`, `cout_proportionnel.txt`.
