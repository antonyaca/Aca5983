# Momentum intraday et ORB — S&P 500 et Nasdaq 100 (M1)

Lancer : `python3 backtests/intraday/backtest.py [SP500 NASDAQ100]` → `results/<INSTRUMENT>/`.
Capital 10 000 €, risque fixe 100 € par trade (1 R = 100 €). Heure de New York (heure d'été gérée), séances 09:30-16:00 complètes uniquement.

## Règles
- **Momentum** (Gao, Han, Li & Zhou, 2018) : sens = signe du mouvement clôture de la veille (16:00) → 10:00. Entrée 15:30, sortie 16:00. Stop de protection 0,25 / 0,5 / 1 ATR journalier (14 jours précédents).
- **ORB** : range des 15 ou 30 premières minutes. Entrée au premier franchissement (jusqu'à 15:00), stop au bord opposé, sortie RR 1, RR 2 ou 16:00. Deux bords franchis dans la même minute → pas de trade ; stop touché dans la minute d'entrée → perte.
- Coûts aller-retour : SP500 0,75 pt, NASDAQ100 1,5 pt, convertis en R selon le stop.

## Résultat (16/10/2026, données au 09/10/2026)
- Momentum : aucun avantage, ni sur SP500 ni sur Nasdaq.
- ORB SP500 : rien de stable ; la sortie à 16:00 est positive en IS mais négative en OOS.
- **ORB Nasdaq, sortie à 16:00** : seul résultat positif après frais en IS et en OOS.
  - 30 min : +0,131 R/trade, +20 431 € sur 2020-2026, OOS +0,056 R (+3 810 €), drawdown max 3 384 €, 1 565 trades.
  - 15 min : +0,106 R/trade, OOS quasi nul (+0,004 R).
  - Robustesse ORB 30 : positif chaque année (2025 ≈ 0), reste positif avec des frais doublés (+0,098 R) ou triplés (+0,066 R).
  - Mise en garde : 18 réglages testés, l'avantage baisse nettement depuis 2024.

## Filtres sur l'ORB 30 min Nasdaq (`filters.py`, 16/10/2026)
Protocole fixé avant lecture : 12 filtres candidats, seuils calculés sur 2020-2023 ; retenu si +0,03 R en IS Nasdaq, ≥ 40 % des trades gardés, et amélioration de l'IS S&P 500 (contrôle). Jugement final sur 2024-2026 sans ajustement.
- Seul filtre retenu : **achats seulement**.
- ORB 30 min Nasdaq, achats seulement, sortie 16:00 : 817 trades, +0,193 R/trade, +15 791 €, PF 1,31, drawdown max 2 290 €, pire série 16.
  IS +0,266 R, OOS +0,108 R (+4 095 €) ; positif chaque année y compris 2022 ; OOS encore +0,08 R avec frais doublés.
- Écarté à juste titre : « range étroit » (+0,47 R en IS, −0,004 R en OOS), exemple typique de sur-optimisation.
- Sur le S&P 500, le même filtre reste négatif en OOS : l'avantage semble propre au Nasdaq.
