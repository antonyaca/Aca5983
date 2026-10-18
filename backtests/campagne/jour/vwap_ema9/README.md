# VWAP + EMA 9 (captures d'Anto, 18/10/2026)

Règles : `run.py` (fixées avant calcul). Nasdaq et S&P, M5, croisement EMA 9 / VWAP (approché par le prix moyen de la
séance, faute de volume), entrées 15:35-18:00 Paris, stop dur 0,25 ATR (≈ « −25-30 % » de l'option), sortie dès qu'une
bougie clôture de l'autre côté de l'EMA 9 (A) ou objectif 1:1 en plus (B), règle d'Anto (1 trade + 2e si perte).

## Résultat : aucun avantage
| | Trades | Brut / trade | Net (coût fixe) | Net (coût ∝ prix) | Jours positifs |
|---|---|---|---|---|---|
| Nasdaq, sortie A | 4 512 | +0,035 R | −0,053 R | −0,004 R | 40-44 % |
| S&P, sortie A | 4 495 | +0,031 R | −0,092 R | −0,056 R | 38-40 % |
| 2 indices, sortie B | 5 258 | +0,032 R | −0,071 R | −0,028 R | 45-49 % |
Avant frais le croisement gagne à peine (+0,03 R) ; les frais l'annulent. Aucune des 12 combinaisons n'est validée.
Correctif : `lib.regle_anto` réindexe désormais ses entrées (un concat multi-marchés avec index dupliqués
gonflait le nombre de trades ; détecté ici, résultats « 2 indices » recalculés).

## Optimisation TP/SL (`optimisation.py`) — 120 réglages, choisis sur 2011-2018, jugés sur 2019-2026
- Meilleur réglage Nasdaq en découverte (stop 0,15 ATR, sans objectif, sans sortie EMA 9 = tenir jusqu'à 16:00) :
  +0,103 R en 2011-2018 → **+0,029 R en 2019-2026 (t 0,6), 35 % de jours positifs**.
- Meilleur S&P en découverte (stop 0,25 ATR, objectif 3 R) : +0,055 R → −0,001 R en validation.
- 44 réglages sur 120 positifs en validation ; aucun significatif (meilleur t 1,98, choisi après coup).
- Ce qui ressort : la sortie « clôture au-delà de l'EMA 9 » de la vidéo est la pire ; les réglages les moins mauvais
  tiennent jusqu'au soir, ont peu de jours positifs (35-48 %) et vivent de rares grosses journées de tendance.
