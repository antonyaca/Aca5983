# Robustesse du trio Nasdaq (17/10/2026)

`python3 backtests/robustesse/run.py`. Trio = ORB 30 min achats + Williams k=0,5 deux sens + pré-marché deux sens. 100 € par R, coûts inclus.

- Williams, sensibilité de k (deux sens) : positif en IS et OOS de k = 0,3 à 0,8 (PF 1,11 à 1,21). Pas de dépendance à k = 0,5.
- Trio par année : 2020 +1 701 €, 2021 +8 605, 2022 +9 067, 2023 +736, 2024 +2 837, 2025 +5 757, 2026 (oct.) +5 258.
- Semaines : 52 % positives, 18 % à +500 € ou plus, moyenne +96 €, pire −1 120 €.
- Monte Carlo 1 an (tirage de semaines) : gain médian +4 855 €, 11 % d'années perdantes, DD médian 2 420 €, 95e centile 4 959 €.
