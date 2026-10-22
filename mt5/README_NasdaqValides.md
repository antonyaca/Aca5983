# Robot MT5 — NasdaqValides (22/10/2026)

`NasdaqValides.mq5` : les 3 stratégies Nasdaq validées sur 2011-2026 (`backtests/campagne/nasdaq_suite/`).
1. **Williams régulier, achat seulement**, si la clôture d'hier > SMA200 : achat stop à ouverture 09:30 NY + amplitude/2
   de la séance précédente, stop = ouverture ; à +0,5 R → 50 % encaissés et stop au prix d'entrée ; fermeture 15:59 NY.
2. **RSI2** : à 15:56 NY, RSI(2) < 20 et prix > SMA200 → achat ; vente à 15:56 NY dès que le prix > SMA5.
3. **3 baisses** : à 15:56 NY, 3 clôtures en baisse → achat ; vente au 1er jour en hausse ou après 5 séances.
Taille automatique pour un risque fixe (`RiskPerTrade`). Numéros magiques 598401 / 598402 / 598403.
Options : `DailyMaxLoss` / `DailyMaxGain` (arrêt du Williams pour la journée), `MaxSpreadPoints` (pas d'entrée si spread trop large).

## Installation
MT5 → Fichier → Ouvrir le dossier des données → `MQL5/Experts` → copier le fichier → MetaEditor → Compiler (F7).

## Tester avec les vrais spreads (testeur de stratégie)
1. Expert : NasdaqValides ; symbole : le Nasdaq 100 de ton broker (US100, NAS100, USTEC…) ; période **M1**.
2. Modélisation : **« Chaque tick basé sur des ticks réels »** → spreads réels historiques du broker (+ swaps et commissions du compte).
3. Dates : par exemple 01/01/2024 → aujourd'hui (les ticks réels n'existent souvent que sur quelques années).
4. **Obligatoire dans le testeur : `ServerMinusNYHours`** (dans le testeur, l'heure GMT n'est pas connue).
   Valeur = heure du serveur − heure de New York. Pour la plupart des brokers (serveur GMT+2/GMT+3), **7**.
   Vérification : l'ouverture de New York (09:30 NY) doit tomber à **16:30** heure du serveur sur le graphique.
5. Historique D1 d'au moins 300 jours nécessaire (SMA200, RSI).

## En compte démo
Glisser le robot sur un graphique M1 du Nasdaq, cocher « Autoriser le trading algorithmique », laisser
`ServerMinusNYHours = 0` (automatique). Le journal affiche l'heure de New York calculée au démarrage : la vérifier.

## Écarts connus avec le backtest
- Les clôtures journalières utilisées (RSI, SMA, 3 baisses) sont celles du D1 du broker (clôture vers 17:00 NY), le jour
  en cours étant pris au prix de 15:56 NY ; le backtest utilisait la séance 09:30-15:55. Légères différences de signaux.
- Robot non compilé ici (pas de MetaEditor dans l'environnement) : signaler toute erreur de compilation.
