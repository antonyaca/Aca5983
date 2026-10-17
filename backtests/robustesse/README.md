# Robustesse : les 3 stratégies Nasdaq sur d'autres marchés (17/10/2026)

`python3 backtests/robustesse/three_strats.py <MARCHÉS>` — mêmes règles, seul l'horaire de séance change (voir le script).
Contrôle : le code générique retrouve les résultats Nasdaq (Williams identique ; ORB +15 441 € vs +15 791 € ; pré-marché
+11 205 € vs +11 970 € — écarts dus aux filtres de séances incomplètes).

| Marché | Pré-marché | Williams | ORB achats |
|---|---|---|---|
| Nasdaq (référence) | ✔ +11 205 € | ✔ +6 200 € | ✔ +15 441 € |
| S&P 500 | +3 298 € (PF 1,04) | −390 € | +2 219 € (OOS < 0) |
| Nikkei 225 | ✔ +3 520 € (PF 1,12, t = 1,1, nul sans top 5) | +4 856 € (frais ×2 OOS < 0) | −89 € |
| FTSE 100 | −14 608 € | −11 133 € | −7 208 € |
| Argent | −24 103 € | −28 452 € | −27 061 € |
| WTI (données 2024-2025 manquantes) | −5 602 € | −5 293 € | −7 216 € |

Conclusion : l'edge ne se transporte pas. Il est propre au Nasdaq (un peu au S&P 500 et au Nikkei, marchés corrélés à la tech US).
