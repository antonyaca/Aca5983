# Flèches JustUncleL + stop au dernier plus haut / plus bas (captures d'Anto, 18/10/2026)

Signal = alerte BUY/SELL du script (Heikin Ashi par défaut). Stop = dernière fractale confirmée (triangle). Sorties
1R / 2R / fin du signal. Entrées 09:00-20:00 Paris. Or, Nasdaq, S&P, EURUSD, 2011-2026, M1 + M5, M15, H1. Règles : `run.py`.

## Résultat : aucun avantage, à aucune unité de temps
| Unité | Trades (sortie 2R) | Brut / trade | Frais médians | Net |
|---|---|---|---|---|
| M1 | 110 847 | −0,013 R | 0,33 R | −0,54 R |
| M5 | 24 697 | +0,025 R | 0,14 R | −0,18 R |
| M15 | 12 007 | +0,011 R | 0,08 R | −0,11 R |
| H1 | 3 549 | −0,003 R | 0,04 R | −0,06 R |

- Avant frais, la flèche vaut un pile ou face à toutes les unités de temps : le problème n'est pas que le spread.
- Découpages statistiques (fixés avant lecture, découverte 2011-2018 / validation 2019-2026) : sens achat/vente,
  heure d'entrée, taille du stop rapportée aux frais → aucun sous-ensemble positif net sur les deux périodes.
  Meilleur cas : stops > 20 fois les frais (≈ 0 R net) — pas d'edge.
