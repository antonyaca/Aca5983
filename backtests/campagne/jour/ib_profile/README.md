# Initial Balance + profil (VAH / VAL / POC) — « Break & Retest » et « Fade » (captures d'Anto, 18/10/2026)

Règles : `run.py` (fixées avant calcul). IB 09:30-10:00 NY (15:30-16:00 Paris), profil en temps passé par prix (pas de
volume dans les données), zone de valeur 70 %. S&P 500 (captures) et Nasdaq, 2011-2026, règle d'Anto.

| Setup | Marché | Trades | Brut / trade | Net (coût ∝ prix) | Jours positifs |
|---|---|---|---|---|---|
| S1 Break & retest (stop POC), 1:1 / 1:2 | S&P | 2 589 | −0,04 / −0,02 R | −0,53 / −0,51 R | 45 / 33 % |
| | Nasdaq | 2 848 | −0,02 / −0,04 R | −0,22 / −0,24 R | 47 / 32 % |
| S2 Fade (retour dans la zone), objectif POC / 1:1 | S&P | 2 984-3 161 | −0,01 / +0,03 R | −0,15 / −0,10 R | 60 / 51 % |
| | Nasdaq | 3 170-3 499 | 0,00 / +0,02 R | −0,07 / −0,04 R | 70 / 51 % |

Aucune des 16 combinaisons n'est positive. Le Fade vers le POC donne 60-70 % de jours positifs mais perd :
gains petits, pertes pleines (piège du taux de réussite). Le Break & retest avec stop au POC a des stops trop courts
(frais 0,12-0,36 R) et un avantage brut négatif.
