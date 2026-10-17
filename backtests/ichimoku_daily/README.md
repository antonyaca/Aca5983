# Ichimoku journalier en portefeuille — 10 marchés, 2010-2026 (17/10/2026)

`python3 backtests/ichimoku_daily/backtest.py` ; règles en tête du script (fixées avant). Données 2010-2019 ajoutées et
contrôlées (indices à partir de mi-novembre 2010). IS 2010-2017, OOS 2018-2026. 100 € par trade.

| Setup | Trades | Avant frais | Après frais | PF | IS / OOS | Total |
|---|---|---|---|---|---|---|
| Cassure du nuage | 594 | −0,039 R | −0,117 R | 0,71 | −0,172 / −0,071 | −6 923 € |
| Croisement TK | 762 | **+0,141 R** | −0,014 R | 0,98 | −0,130 / +0,094 | −1 064 € |

Sensibilité au swap (hypothèse 6 %/an achat indices-métaux, 2,5 % devises) — croisement TK :
sans swap +8 479 € (PF 1,20, IS ≈ 0, t = 1,35) ; swap divisé par 2 : +3 708 € (PF 1,08). Cassure du nuage négative même sans swap.
Par marché (croisement TK) : or +3 069 €, argent +1 869 €, AUDUSD +1 251 € ; FTSE −4 071 €, Nikkei −2 046 €, USDJPY −1 770 €.
Conclusion : léger avantage brut du croisement TK (surtout métaux, 2020-2022), mangé par le coût de portage des CFD ;
aucune version validée, et 2010-2017 est nul ou négatif même sans swap.
