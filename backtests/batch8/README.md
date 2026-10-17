# Lot 8 — stratégies 2 à 5 (17/10/2026)

`python3 backtests/batch8/strategies.py` ; règles en tête du script. Critère strict (t ≥ 2) : aucune.
- Cassure du plus haut / bas de la veille : ≈ 0 (Nasdaq +1 340 €, PF 1,02 ; S&P −3 938 €).
- Power hour : Nasdaq +2 228 € (PF 1,15) mais ≈ 0 depuis 2024 ; S&P ≈ 0.
- Nuit conditionnelle : Nasdaq +3 224 € (PF 1,21) mais ≈ 0 en 2020-2023, positif seulement depuis 2024 ; S&P ≈ 0.
- Williams après NR7 : dégrade le Williams sur le Nasdaq (2024+ négatif) ; meilleur sur le S&P mais fragile → incohérent, rejeté.
Note : le Williams « tous les jours » donne ici +7 013 € (1 170 trades) contre +6 200 € (1 189) dans le lot 4 — petites
différences de filtrage des séances et d'historique ATR ; la conclusion ne change pas.
