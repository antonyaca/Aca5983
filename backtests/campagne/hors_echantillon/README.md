# Revalidation 2011-2019 des stratégies Nasdaq (17/10/2026)

Code d'origine inchangé (`robustesse/three_strats.py`), seul l'historique est étendu. Contrôle 2020-2026 retrouvé à l'identique
(ORB +15 441 €, pré-market +11 205 €, Williams +6 096 €). Alignement horaire des données vérifié pour chaque année
(pic de volatilité à 09:30 NY).

| Nasdaq | 2011-2019 brut | net (1,5 pt fixe) | net (coût ∝ prix, 1,25 pb) | 2020-2026 net |
|---|---|---|---|---|
| ORB 30 min achats | +0,053 R | −0,152 R (−17 500 €) | −0,018 R (−2 022 €) | +0,182 R (+15 441 €) |
| Pré-market | +0,059 R | −0,033 R (−7 268 €) | +0,028 R (+6 108 €, t 0,99) | +0,073 R (+11 205 €) |
| Williams k=0,5 | +0,054 R | −0,036 R (−6 088 €) | +0,024 R (+4 060 €, t 0,83) | +0,051 R (+6 096 €) |

Le coût fixe de 1,5 pt est trop sévère en 2011 (Nasdaq ≈ 2 300) ; la colonne « coût proportionnel » est la plus réaliste.

## Verdict
- **Aucune des trois ne passe le test hors échantillon.** L'avantage brut existe sur 16 ans (≈ +0,05 R) mais il est faible ;
  la période 2020-2026 (forte volatilité, tendance) l'a nettement gonflé.
- ORB achats : nul en 2011-2019 → la plus fragile. Pré-market et Williams : légèrement positifs mais non significatifs.
- S&P 500 : négatif sur 2011-2019 pour les trois.
- Conséquence : ne pas augmenter le risque sur ces stratégies ; les garder en démo / petite taille avec suivi de dégradation.
