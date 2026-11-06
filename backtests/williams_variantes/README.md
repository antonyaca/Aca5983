# Williams Nasdaq — campagne de variantes (06/11/2026)

Données M1 2011 → 30/10/2026, coût 1,5 pt, 100 €/R. `wvar.py <repo> NASDAQ100 [json variantes]`, `w_exits.py` (sorties).
Bug corrigé en cours : un niveau déjà dépassé au moment où l'entrée devient possible était rempli au niveau (prix
impossible) → fausses pépites « ancre clôture veille » (t 10) et « entrée après 16h ». Remplissage au marché désormais.

## Meilleure combinaison : k = 0,4 + entrée avant 17h30 Paris + trailing stop 1R (clôture 22h sinon)
| | Trades | E nette | t | €/an | DD | 2011-18 | 2019-26 | Années + |
|---|---|---|---|---|---|---|---|---|
| Référence (k 0,5, toute la séance, clôture) | 2 898 | +0,042 | 1,9 | 775 | 8 691 | −0,009 | +0,098 | 13/16 |
| **Combo** | 2 614 | **+0,113** | **5,3** | **1 874** | **2 460** | +0,083 | +0,145 | 15/16 |

Voisins (k 0,35-0,5 ; limite 16h30-19h30 ; trailing 0,75-1,5R) : tous positifs sur les 2 périodes, t 3,1-5,3.
Frais ×2 : +0,039 R (2011-18 négatif, 2019-26 +0,120) — sensible aux frais quand le Nasdaq était bas.
S&P 500 : ne se transpose pas (net ≈ 0). Effet propre au Nasdaq.

## Autres pistes (une dimension à la fois)
Positives sur les 2 périodes : k 0,4 ; achats seuls ; sens SMA200 ; entrée avant 17h30 ; gros gap (> 0,3 ATR14, t 3,1) ;
trailing 1R. Rejetées : ATR comme volatilité, ancre clôture veille, sorties anticipées (17h-21h), filtre jour de semaine
(échantillons trop petits), NR4, stop opposé / 0,5 ATR.
