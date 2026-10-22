# Nasdaq — 3 pistes d'amélioration (22/10/2026), règles dans `run.py`

1. **Filtre de volatilité (ATR5 > ATR50) sur le Williams** : garde 46 % des jours ; espérance par trade inchangée
   (clôture +0,074 → +0,069 R ; régulier +0,053 → +0,051 R), drawdown plus faible mais gain annuel divisé par 2-2,5,
   plus significatif (t 2,3-2,6). **Rejeté** : il n'améliore pas l'avantage, il réduit seulement l'activité.
2. **Versions vente** (RSI2 > 90 et 3 hausses, sous la SMA200) : 28 et 36 trades en 16 ans → trop peu pour conclure.
   **Rejeté** (rien d'exploitable, le Nasdaq a rarement été sous sa SMA200).
3. **Voisinage du RSI2 achat** (coût ∝ prix) :
| Réglage | Trades | E nette | t | €/an (100 €/R) | Jours positifs |
|---|---|---|---|---|---|
| RSI2 < 5 | 66 | +0,596 R | 3,99 | +250 | 80 % |
| **RSI2 < 10 (validé)** | 126 | +0,456 R | 4,48 | +365 | 71 % |
| RSI2 < 20 | 219 | +0,365 R | 4,54 | +506 | 73 % |
| RSI3 < 10 | 46 | +0,622 R | 3,29 | +182 | 80 % |
   **Confirmé** : tous les réglages voisins gagnent, sur les deux périodes → l'avantage n'est pas un hasard de réglage.
   Seuil plus large = plus de trades et plus d'euros, avantage par trade un peu plus faible.

## Réduire le drawdown (`drawdown.py`) — classement par gain annuel / drawdown max (coût ∝ prix, 100 € par R)
| Stratégie | Trades/jour | €/an | DD | Gain/DD |
|---|---|---|---|---|
| Williams régulier achats si > SMA200 + RSI2<20 + 3 baisses | 0,39 | 1 339 | 1 147 | 1,17 |
| Williams régulier achats seulement | 0,37 | 667 | 882 | 0,76 |
| RSI2 < 20 | 0,05 | 506 | 713 | 0,71 |
| Williams régulier (base) | 0,75 | 1 042 | 2 807 | 0,37 |
Toutes validées (lib.evaluate). Achats seulement : variante prévue avant calcul, cohérente avec la dérive haussière du
Nasdaq. Limite : à objectif de gain égal, le drawdown du meilleur mélange (≈ 10 mois de gains) est le même que celui du
mélange précédent (Williams régulier + RSI2<20 + 3 baisses, gain/DD 1,19) ; il demande seulement moins de trades.

## Micro-scalping « objectif +2, stop −1 » en boucle (`micro_scalp.py`, 22/10/2026)
Nasdaq 2011-2026, toutes les heures de 0 h à 23 h (Paris), stop 5/10/20 pts, sens momentum ou retour, coût 1,5 pt (et 1,0).
- Espérance nette négative dans 142 des 144 cases (coût 1,5 pt) : stop 5 pts ≈ −0,30 R, 10 pts ≈ −0,14 R, 20 pts ≈ −0,07 R.
  Avant frais ≈ 0 partout (+2/−1 = 1 chance sur 3, comme le hasard).
- Meilleure case 2011-2018 (stop 20, retour, 13 h) → −0,063 R en 2019-2026 (t −4,8). Seule case positive (21 h) :
  379 trades, années alternées → bruit.
- Journée simulée avec 1 R = 1 € et arrêt à ±100 € : −100 € atteint dans 100 % des cas, après ~670 trades (médiane).
Conclusion : non viable ; chaque trade paie un spread pour un avantage nul.

## Micro-scalping +2/−1 filtré RSI / Stochastique M1 (`scalp_rsi_stoch.py`, 22/10/2026)
Frais bas : EURUSD raw spread + commission 0,8 pip ; Nasdaq micro-future MNQ 0,75 pt. 54 combinaisons (filtre × stop × session).
- Nasdaq : négatif partout (−0,02 à −0,10 R) ; avant frais ≈ 0.
- EURUSD Asie / Londres / New York : négatif partout (−0,04 à −0,23 R).
- Seule exception : **EURUSD « soir » 22 h-minuit Paris**, RSI : +0,14 R après 0,8 pip, t 7,1. Concentré à 23:00-23:30
  (bascule quotidienne du forex, brut +0,54 R) : **artefact d'illiquidité**. Les données HistData sont en prix bid seul
  et ne montrent pas l'écartement du spread à cette heure (souvent plusieurs pips). Net à 1,5 pip : −0,03 R ; à 2 pips :
  −0,13 R. Non exploitable.
