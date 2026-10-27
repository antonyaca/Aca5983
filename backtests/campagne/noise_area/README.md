# Noise area Nasdaq — re-test sur données corrigées (27/10/2026)

Règles du lot 4 inchangées (docstring de `run.py`), 4 variantes fixées avant calcul. Critère `lib.evaluate`, 1,5 pt par trade.

**Aucune variante validée.**

| Variante | Trades | E brute | E nette | t | Découverte 2011-18 | Total | DD max |
|---|---|---|---|---|---|---|---|
| V1 deux sens | 3 187 | +0,056 R | +0,013 R | 1,0 | −0,004 R | +4 130 € | 5 313 € |
| V2 achats seuls | 1 657 | +0,064 R | +0,021 R | 1,4 | −0,009 R | +3 438 € | 1 928 € |
| V3 deux sens + règle Anto | 2 896 | +0,055 R | +0,012 R | 0,9 | +0,000 R | +3 407 € | 4 645 € |
| V4 achats seuls + règle Anto | 1 500 | +0,062 R | +0,019 R | 1,2 | −0,003 R | +2 810 € | 1 483 € |

Edge brut réel mais absorbé aux deux tiers par les frais ; négatif avec frais ×2 ; n'apparaît qu'après 2019.
La conclusion du lot 4 (OOS faible) est confirmée après correction des horaires.
