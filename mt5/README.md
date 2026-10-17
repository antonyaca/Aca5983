# Robot MT5 — Nasdaq 3 stratégies

`Nasdaq3Strategies.mq5` : pré-marché + Williams (k = 0,5) + ORB 30 min achats, mêmes règles que `tradingview/nasdaq_3_strategies.pine`
et que les backtests 2020-2026. Heure de New York calculée automatiquement (heure d'été US gérée). Un trade max par stratégie et par jour,
pas de take profit, clôture forcée à 15:59 NY. Numéros magiques 598301 / 598302 / 598303.

Installation : MT5 → Fichier → Ouvrir le dossier des données → MQL5/Experts → copier le fichier → MetaEditor → Compiler (F7)
→ glisser le robot sur un graphique M1 du Nasdaq → cocher « Autoriser le trading algorithmique ».
À valider d'abord en compte démo. Testeur de stratégie : renseigner `ServerMinusNYHours` (écart fixe serveur − New York, souvent 7).
