# Lot 3 — stratégies simples (16/10/2026)

Lancer : `python3 backtests/batch3/strategies.py SP500 NASDAQ100 XAUUSD` et `... DAX CAC40`. Règles, sizing et frais (dont swap) en tête du script.
Critère fixé avant : E nette > 0 en IS et OOS, PF ≥ 1,10, OOS > 0 avec frais doublés. 100 € par R.

Validées (6 sur 17) :
| Stratégie | Trades | E nette | PF | IS | OOS | Total | t-stat |
|---|---|---|---|---|---|---|---|
| RSI 2 S&P 500 | 48 | +0,663 R | 3,81 | +0,374 | +0,852 | +3 181 € | 3,77 |
| RSI 2 Nasdaq | 47 | +0,450 R | 2,57 | +0,202 | +0,591 | +2 117 € | 2,58 |
| Fin/début de mois Nasdaq | 75 | +0,245 R | 1,48 | +0,170 | +0,339 | +1 834 € | 1,34 |
| Fin/début de mois S&P 500 | 75 | +0,224 R | 1,45 | +0,178 | +0,282 | +1 680 € | 1,30 |
| Inside day or | 243 | +0,082 R | 1,25 | +0,054 | +0,119 | +1 989 € | 1,37 |
| ORB 30 min DAX achats seuls | 784 | +0,072 R | 1,11 | +0,047 | +0,096 | +5 650 € | 1,13 |

Rejetées : nuit (S&P, Nasdaq), cassure 20 j (or, Nasdaq), inside day S&P / Nasdaq, ORB CAC 40. Euro Stoxx 50 : données indisponibles.

Portefeuille sans doublons (ORB Nasdaq achats + RSI 2 S&P + fin de mois Nasdaq + inside day or + ORB DAX achats) :
1 967 trades, +28 445 € (2020-2026), OOS 2024+ +12 369 €, DD max 3 901 €, corrélations mensuelles faibles (< 0,25).
