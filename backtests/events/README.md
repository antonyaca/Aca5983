# Annonces CPI et FOMC — règle NFP inchangée (17/10/2026)

`python3 backtests/events/backtest.py`. Dates officielles BLS (CPI 80) et Fed (FOMC 53 réunions programmées). Frais ×2.
Contrôle : NFP Nasdaq identique au test précédent (+2 171 € / +2 646 €).
- **S&P 500 CPI, TP 1:2 : seul résultat « strict »** — 72 trades, +4 318 €, PF 1,87, IS +0,36 / OOS +0,94 R, t = 2,07, positif sans les 3 meilleurs trades.
  Mais incohérent : la même règle sur le CPI Nasdaq perd en 2020-2023, et le NFP S&P perd. Probable en partie dû au hasard (≈ 20 tests).
- Nasdaq CPI / FOMC : négatifs en 2020-2023, très positifs depuis 2024 → non validés.
- S&P FOMC clôture : +4 516 € mais dépend de 3 trades.
- Lecture d'ensemble : les cassures d'annonce sont positives avant frais dans 11 cas sur 12, surtout depuis 2024 ; à surveiller, pas encore exploitable seul.
