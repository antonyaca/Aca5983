# Jours de NFP (17/10/2026)

`python3 backtests/nfp/backtest.py` ; règles en tête du script. Dates officielles BLS (80 publications 2020-2026,
dont les dates décalées par le shutdown 2025). Frais doublés (spread d'annonce). Données manquantes : 3-4 jours NFP en 2023.

| Marché | Variante | Trades | Résultat | PF | 2020-23 / 2024+ | Verdict |
|---|---|---|---|---|---|---|
| **Nasdaq** | **range 08:00-08:30, TP 1:2** | 66 | **+2 171 €** | 1,53 | +0,33 / +0,33 R | ✔ le plus robuste (positif sans les 3 meilleurs trades) |
| Nasdaq | range 08:00-08:30, clôture | 66 | +2 646 € | 1,43 | +0,04 / +0,96 R | ✔ mais dépend des 3 meilleurs trades |
| Nasdaq | range 08:30-08:45 | 73 | −2 495 / +3 057 € | — | IS négatif | ✘ |
| Or | toutes | 69-71 | −3 423 à +269 € | ≤ 1,05 | — | ✘ |

Ajouté aux 3 stratégies Nasdaq : +36 132 € au lieu de +33 961 €, DD 3 484 € (au lieu de 3 594 €). Corrélation 0,26.
Limite : ≈ 10 trades par an, t = 1,6 : signal prometteur mais statistiquement faible.
