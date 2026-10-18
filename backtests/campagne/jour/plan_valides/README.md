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

## « Le point d'entrée doit être le stop » (`stop_comme_entree.py`, 18/10/2026)
Deux lectures testées sur le Williams (Nasdaq, S&P en contrôle), coût ∝ prix :
| Lecture | Nasdaq | S&P |
|---|---|---|
| I1 : entrée limite à l'ouverture (ancien stop) après la cassure, stop niveau opposé, TP 1:1 | −0,063 R (884 trades, t −2,2) | −0,177 R |
| I1 : idem, sortie 16:00 | −0,027 R | −0,149 R |
| I2 : Williams puis retournement au stop (2e trade) | trade de retournement ≈ +0,01 R : n'apporte rien | idem |
Constat annexe : **Williams Nasdaq avec TP 1:1** (au lieu de la clôture) : 2 881 trades, +0,050 R, t 3,20, DD 2 869 €,
**54 % de jours positifs**, +908 €/an — plus régulier mais moins rentable que la sortie en clôture (+1 350 €/an, 47 %).

## Vérification indépendante de V04 (agent « jours positifs ») — `verif_v04.py`
Williams Nasdaq, 50 % sortis à +0,5 R, reste avec stop ramené à l'entrée, sortie 16:00 ; 2e trade si le 1er perd.
Recodé séparément : 3 100 trades communs avec l'agent, 7 seulement diffèrent de plus de 0,001 R.
| Coût | Trades | E nette | t | €/an | DD | Jours positifs (jours tradés) | Pire série | Mois positifs |
|---|---|---|---|---|---|---|---|---|
| ∝ prix 1,25 pb, règle d'Anto | 3 094 | +0,053 R | 4,01 ✔ | +1 042 | 2 807 | 65 % | 6 j | 63 % |
| fixe 1,5 pt, règle d'Anto | 3 094 | +0,020 R | 1,53 ✘ | +399 | 7 509 | 64 % | 6 j | 56 % |
