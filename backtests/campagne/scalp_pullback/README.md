# « Scalping PullBack Tool R1.1 » (JustUncleL) — 17/10/2026

Signal recodé fidèlement depuis le Pine (Heikin Ashi, PAC EMA 34, EMA 89/200, repli ≤ 3 bougies, alerte BUY/SELL).
Exécution ajoutée avant test : entrée à l'ouverture réelle suivante, stop = bord opposé du PAC, sorties 1R / 2R / retour
sous la ligne centrale du PAC. M5 et M15, 10 marchés, 2011-2026, données corrigées, coûts habituels. Règles : `run.py`.

## Résultat : aucun edge
| | Trades | Brut / trade | Coût / trade | Net |
|---|---|---|---|---|
| M15 (3 sorties) | ≈ 28 000 chacune | −0,017 à +0,016 R | 0,20 R | −0,19 à −0,22 R |
| M5 (3 sorties) | ≈ 65 000-75 000 | −0,010 à +0,018 R | 0,34 R | −0,33 à −0,35 R |

- Avant frais, le signal vaut un pile ou face (≈ 0 R) sur tous les marchés ; seul le Nikkei est légèrement positif
  brut (+0,06 / +0,09 R), mais son coût (0,19-0,36 R) est plus élevé.
- 60 combinaisons marché × réglage : **toutes négatives après frais**, y compris sur la meilleure (Nasdaq M15 sortie PAC :
  −0,076 R, 6 années positives sur 16).
- Cause : stop serré (bord du PAC) → spread = 20 à 35 % du risque à chaque trade.
