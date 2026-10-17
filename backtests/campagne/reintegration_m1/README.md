# Réintégration M1 dans la tendance (idée d'Anto, 17/10/2026)

Règles complètes dans `run.py` (fixées avant calcul). Or, Nasdaq, S&P, EURUSD, 2011-2026, données corrigées.
Signal : tendance EMA 89/200 + canal EMA 34 (vert = achats, rouge = ventes) ; bougie M1 qui reclôture au-delà des
3 moyennes ; stop = extrême de la bougie ; TP 1:1 ; frais déduits. Gestion du jour : A (stop si Londres gagne),
B (toujours 2 trades), puis on continue tant que le jour ≤ 0 (4 trades max, pas d'entrée après 20:00 Paris) ;
C = 2 trades seulement ; D = tous les signaux.

## Résultat : perdant partout, avant même les frais
- **Brut (avant frais) : −0,04 à −0,06 R par trade** sur les 4 marchés et les 4 gestions : le signal n'a aucun avantage.
- **Le stop sous une bougie M1 est plus petit que le spread** : risque médian or 0,43 $ (spread 0,47 $), EURUSD 2 pips
  (spread 1,5), S&P 0,8 pt (spread 0,75). Frais médians : 0,5 à 1,1 R par trade.
- Même en ne gardant que les trades dont le stop vaut ≥ 10 fois les frais : brut ≈ 0, net −0,05 à −0,17 R.
- Gestion « continuer jusqu'à être positif » : plus de jours positifs (jusqu'à 40 % vs 13-17 %), mais des pertes
  totales plus lourdes (B et A perdent plus que C) — elle amplifie un signal perdant, elle ne le corrige pas.
