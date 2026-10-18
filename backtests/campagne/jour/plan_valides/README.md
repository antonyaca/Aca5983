# Règle d'Anto appliquée aux stratégies validées (18/10/2026)

## Williams Nasdaq, 1 trade/jour + « 2e chance » (`williams_2e_chance.py`)
Trade 1 identique au Williams validé (contrôle : écart nul sur 2 881 jours communs). 2e trade seulement si le 1er est
stoppé : niveau opposé touché ensuite → trade inverse, même stop, sortie 16:00.

| Coût ∝ prix (1,25 pb) | Trades | E nette | t | €/an | DD | Jours avec trade | Jours positifs | €/jour ouvré | Pire série |
|---|---|---|---|---|---|---|---|---|---|
| Trade 1 seul | 2 881 | +0,074 R | 3,37 | +1 350 | 4 199 | 70 % | 47 % | +5,17 | 18 j |
| Trade 1 + 2e chance | 3 217 | +0,068 R | 3,28 | +1 389 | 3 840 | 70 % | 48 % | +5,32 | 18 j |

La 2e chance seule (336 trades) est quasi nulle (+0,018 R, t 0,3) : elle n'ajoute rien.
Avec le coût fixe 1,5 pt (sévère en 2011-2015), ni l'un ni l'autre ne passe (t 1,9 / 1,7).

## Les 4 validées ensemble (Williams + RSI2 + NFP or + 3 baisses)
72 % des jours avec au moins un trade, 49 % de jours positifs, +12,26 €/jour ouvré en moyenne (+3 200 €/an),
pire série de 15 jours perdants, 65 % de mois positifs.

## Risque nécessaire pour une MOYENNE de 50 ou 100 €/jour
| | 50 €/jour | 100 €/jour |
|---|---|---|
| Williams seul | 967 €/trade → drawdown ≈ 40 600 € | 1 934 €/trade → ≈ 81 200 € |
| 4 validées | 408 €/trade → drawdown ≈ 11 900 € | 816 €/trade → ≈ 23 700 € |
Même dans ce cas, environ un jour sur deux reste négatif.
