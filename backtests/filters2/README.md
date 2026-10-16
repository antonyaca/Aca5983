# Filtres pré-enregistrés sur A / B / C (16/10/2026)

Lancer : `python3 backtests/filters2/run.py` (protocole en tête du script). 100 € par trade, capital 10 000 €.

| Stratégie | Filtre retenu (règle IS + contrôle) | IS | OOS 2024+ | Décision |
|---|---|---|---|---|
| A · ORB 30 min Nasdaq, achats seuls | gap d'ouverture haussier | +0,448 R | +0,072 R (base : +0,108 R) | **Garder A sans filtre** : le filtre dégrade l'OOS |
| B · Range asiatique or | contre-tendance + vol. basse + ventes | +0,188 R | −0,217 R | **Rejeté** : sur-optimisation |
| C · Gap fade Nasdaq ≥ 0,5 ATR | contre la tendance SMA 50 | +0,086 R | +0,035 R | Valide mais marginal (192 trades) |

Retenu : **A sans filtre** (817 trades, +15 791 €, PF 1,31, DD 2 290 €).
A + C : +16 904 €, DD 2 285 €, OOS +4 455 € : apport faible de C (+1 113 €), corrélation journalière −0,2.
