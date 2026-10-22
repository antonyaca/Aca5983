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
