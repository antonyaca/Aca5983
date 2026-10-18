# Campagne 2 « 1 trade par jour » (18/10/2026) — synthèse

Demande : stratégie simple, 1 trade/jour (2e seulement si le 1er perd), le plus de jours positifs possible, 50-100 €/jour.
Protocole : `PROTOCOLE.md`. 4 agents de test + 1 agent de recherche + vérifications de Claude. Données 2011-2026 corrigées.

| Famille | Variantes | Validées (coûts du protocole) | Meilleur résultat |
|---|---|---|---|
| Indices à l'ouverture (`indices/`) | 20 | 0 | Gap & go Nasdaq +0,042 R, t 1,66 |
| Forex et or (`forex_or/`) | 17 + 1 post-hoc | 0 | Cassure hebdo (post-hoc) +0,055 R, t 2,41 |
| Moyennes mobiles / indicateurs (`moyennes_mobiles/`) | 20 | 0 | Supertrend Nasdaq +0,021 R, t 1,0 ; le filtre MA ne bat pas un achat sans filtre |
| Jours positifs (`jours_positifs/`) | 16 | 0 | V04 Williams « 50 % à 0,5 R + stop à l'entrée » |
| Recherche (`recherche/`) | — | — | pistes : jours d'annonce, cycle de la Fed, or CPI/FOMC |

## Ce qui tient (coût proportionnel au prix, convention qui valide le Williams ; vérifié par Claude)
- **Williams Nasdaq, 50 % à +0,5 R puis stop à l'entrée, reste à 16:00** (`plan_valides/verif_v04.py`) :
  3 094 trades, +0,053 R, t 4,0, +1 042 €/an, DD 2 807 €, **65 % de jours positifs**, pire série 6 jours.
  Non validé avec 1,5 pt fixe (t 1,5) : ce coût pèse 0,1 R en 2011 mais ≈ 0,01 R au niveau actuel du Nasdaq.
- Williams Nasdaq TP 1:1 : +0,050 R, t 3,2, 54 % de jours positifs, +908 €/an.
- Or, règle NFP étendue aux CPI (2011-2026) et FOMC (2013-2026) (`plan_valides/or_cpi_fomc.py`) :
  CPI + FOMC 245 trades, +0,261 R, t 2,53, frais ×2 négatifs → **non validé** ; NFP reste le seul validé.

## Conclusion
Aucune stratégie simple ne donne 50-100 €/jour avec 100 € de risque : les meilleures font 2 à 5 € par jour ouvré.
Jours positifs : la règle du 2e trade les augmente sans augmenter le gain ; même un Sharpe de 2-3 ne donne que
55-57 % de jours positifs (calcul : P(jour > 0) = Φ(Sharpe / √252)).
