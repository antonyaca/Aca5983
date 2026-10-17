# Aca5983 — Labo de backtest

Historiques de marché stockés dans le repo pour backtester sans MT5.

## Données (`data/`)

| Nom | Code HistData | Contenu |
|---|---|---|
| XAUUSD | xauusd | Or / dollar |
| EURUSD | eurusd | Euro / dollar |
| SP500 | spxusd | Indice S&P 500 (CFD) |
| NASDAQ100 | nsxusd | Indice Nasdaq 100 (CFD) |

- Unité de temps : M1, prix **bid**, heure UTC (convertie depuis l'heure de New York fixe de la source).
- Un fichier par année : `data/<NOM>/<NOM>_M1_<ANNEE>.csv.gz` (colonnes : time, open, high, low, close, volume).
- Depuis 2020. Inventaire à jour dans `data/manifest.json`.
- Source : HistData.com (gratuite). Les prix peuvent différer légèrement de ceux d'un autre broker ; le spread est ajouté dans les backtests.

## Mise à jour

Automatique chaque dimanche soir (onglet **Actions** > *Historiques de marché*).
Lancement manuel possible avec le bouton **Run workflow** (choix des instruments et de l'année de départ).

## Alerte qualité

- **DAX** : les fichiers 2021, 2022 et 2023 contiennent des cours au niveau de l'Euro Stoxx 50 (3 200-4 400) au lieu du DAX (≈ 13 000-17 000), jusqu'au 01/12/2023. Tout résultat DAX sur cette période est invalide.
