# Fibonacci OTE (17/10/2026)

`python3 backtests/fibo_ote/backtest.py <MARCHÉ> <M5|M15>` puis `python3 backtests/fibo_ote/backtest.py` (synthèse). Règles en tête du script.
Entrée limite 61,8 %, stop au-delà du 78,6 % + spread, objectif extension −0,5 ou retour à l'extrême ; règle journalière :
stop après un trade gagnant, 2 trades max. Horaires « séance » ou « 24 h ». 5 marchés × 2 UT × 2 horaires × 2 objectifs = 40 variantes.

Résultat : **1 variante sur 40 passe le critère, sans significativité** (S&P 500 M15 séance, ext −0,5 : 76 trades en 7 ans,
+2 237 €, t = 0,9 — attendu par hasard sur 40 essais). Toutes les autres sont négatives après frais, souvent fortement.
Cause principale : le stop OTE (≈ 17 % de l'impulsion) est très serré, donc le spread pèse lourd en R, surtout en M5.
Horaires : pas d'amélioration systématique « séance » vs « 24 h ». Règle journalière : ne change pas le signe des résultats.
