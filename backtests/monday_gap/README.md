# Gap du lundi — Nasdaq (17/10/2026)

`python3 backtests/monday_gap/backtest.py` ; règles en tête du script. Gaps ≥ 0,25 ATR, 2020 → 10/2026.
| Jour | Règle | Trades | Résultat | PF | 2020-23 / 2024+ |
|---|---|---|---|---|---|
| Lundi | Comblement | 161 | +809 € | 1,14 | −0,057 / +0,174 R |
| Lundi | Continuation (clôture / TP 1:2) | 161 | −57 / −221 € | ≤ 0,99 | + / − (inversé) |
| Mardi-vendredi | toutes | 641 | −256 à −2 203 € | ≤ 0,99 | — |
Aucune validée : le comblement du lundi est positif au total mais négatif sur 2020-2023 (t = 0,8). Pas d'effet « lundi » exploitable.
