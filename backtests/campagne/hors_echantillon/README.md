# Revalidation 2011-2019 des stratégies Nasdaq (17/10/2026, données corrigées)

**Correction majeure des données le 17/10/2026** : les horodatages HistData sont en heure murale de New York avec heure
d'été, pas en EST fixe. Tous les fichiers ont été convertis avec +5 h fixe → décalage de +1 h pendant l'heure d'été US
(≈ 8 mois sur 12). Tous les backtests intraday antérieurs ont donc testé, l'été, des fenêtres décalées d'une heure.
Fichiers réécrits en vrai UTC (`scripts/fix_timezone.py`), vérifié : pic d'ouverture à 09:30 NY, 08:00 Londres, 09:00 Tokyo,
été comme hiver, chaque année. L'indicateur TradingView et le robot MT5 utilisent l'heure réelle de la bourse : non concernés.

Code d'origine inchangé (`robustesse/three_strats.py`), historique étendu à 2011.

| Nasdaq | 2011-2019 brut | net coût fixe 1,5 pt | net coût ∝ prix (1,25 pb) | 2020-2026 net coût fixe |
|---|---|---|---|---|
| **Williams k=0,5** | +0,093 R | +0,004 R (+657 €) | **+0,063 R (+10 566 €, t 2,11)** | **+0,095 R (+10 618 €, t ≈ 2,7)** |
| Pré-market | +0,059 R | −0,032 R (−6 967 €) | +0,028 R (+6 145 €, t 0,99) | +0,081 R (+11 740 €) |
| ORB 30 min achats | +0,027 R | −0,067 R (−7 798 €) | −0,004 R (−524 €) | +0,086 R (+6 676 €) |

Le coût fixe de 1,5 pt est trop sévère en 2011 (Nasdaq ≈ 2 300) ; le coût proportionnel est le plus réaliste.

## Verdict
- **Williams k=0,5 : seul survivant robuste**, positif et significatif sur les deux périodes (16 ans).
- Pré-market : positif mais non significatif en 2011-2019 → à surveiller.
- ORB achats : nul en 2011-2019 et nettement moins bon qu'annoncé sur 2020-2026 une fois l'heure corrigée → déclassé.
