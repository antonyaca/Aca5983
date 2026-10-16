# Aca5983 — Labo de backtest

Historiques de marché stockés dans le repo pour backtester sans MT5.

## Données (`data/`)

| Nom | Instrument Dukascopy | Contenu |
|---|---|---|
| XAUUSD | xauusd | Or / dollar |
| EURUSD | eurusd | Euro / dollar |
| SP500 | usa500idxusd | Indice S&P 500 (CFD) |
| NASDAQ100 | usatechidxusd | Indice Nasdaq 100 (CFD) |

- Unité de temps : M1, prix **bid**, avec volumes, heure UTC.
- Un fichier par année : `data/<NOM>/<NOM>_M1_<ANNEE>.csv.gz` (colonnes : timestamp en ms, open, high, low, close, volume).
- Depuis 2020. Inventaire à jour dans `data/manifest.json`.
- Source : Dukascopy (gratuite). Les prix peuvent différer légèrement de ceux d'un autre broker ; le spread est ajouté dans les backtests.

## Mise à jour

Automatique chaque dimanche soir (onglet **Actions** > *Historiques de marché*).
Lancement manuel possible avec le bouton **Run workflow** (choix des instruments et de l'année de départ).
