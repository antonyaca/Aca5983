# Écart Nasdaq / S&P 500 intraday — retour à la moyenne (17/10/2026)

`python3 backtests/spread_nq_sp/backtest.py` ; règles en tête du script. β médian 1,24. Frais des deux jambes ≈ 0,05 R.
| Seuil | Trades | Avant frais | Après frais | PF | 2020-23 / 2024+ |
|---|---|---|---|---|---|
| z = 2 | 329 | +0,034 R | −635 € | 0,91 | −0,067 / +0,037 R |
| z = 3 | 83 | +0,064 R | +74 € | 1,04 | −0,018 / +0,040 R |
Aucune validée. L'écart revient rarement à zéro dans la journée (85 % des trades finissent à la clôture) : les écarts
intraday Nasdaq / S&P ont tendance à persister, pas à se refermer.
