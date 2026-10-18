# Recherche documentaire : stratégies « 1 trade par jour » pas encore testées (18/10/2026)

Recherche sur le web, dans des articles académiques et dans des écrits de traders, **sans aucun backtest**. Livrable réduit
à la demande du coordinateur : 10 pistes, la régularité des traders, et le pseudo-code des 3 meilleures pistes.
Règle suivie : chaque chiffre a son lien. Quand un chiffre vient d'un calcul et non d'une source, il est marqué
« calcul indicatif ». Ce qui n'a pas pu être vérifié est marqué « non vérifié ».

## Constat de départ

Les stratégies quotidiennes simples les mieux documentées sont **déjà testées** dans le dépôt : ORB (5, 15 et 30 min),
Williams, noise area de Zarattini, momentum intrajournalier (Gao 2018, Baltussen 2021), gaps, RSI2, IBS, calendrier,
fixings, Gotobi, range asiatique, etc. (liste transmise par le coordinateur et `campagne/*/README.md`). Il reste trois
sortes de pistes :
1. des effets liés au **calendrier de la Fed et des annonces macro**. Les preuves sont solides, mais ces effets ne jouent
   que 8 à 50 jours par an ;
2. des **saisonnalités horaires** (forex, ouverture européenne). Elles sont bien documentées, mais leur gain est du même
   ordre que le coût d'un CFD, et une baisse récente est documentée ;
3. des **règles de traders** peu ou pas chiffrées publiquement.

Échelle des preuves utilisée pour le classement :
- **A** : étude publiée dans une revue à comité de lecture, sur un long échantillon, avec un prolongement hors période ou
  une réplication ;
- **B** : étude académique, mais sans test de rentabilité nette accessible à un particulier, ou avec un déclin documenté ;
- **C** : backtest publié par un praticien ;
- **D** : affirmation de trader sans statistique publique.

## 1. Les 10 pistes, classées par force des preuves

| # | Piste | Marchés | Fréquence | Preuve | Risque principal |
|---|---|---|---|---|---|
| 1 | Prime des jours d'annonce macro (achat) | NASDAQ100, SP500 | ≈ 30 jours/an | A | La part FOMC a disparu en 2016-2019 ; peu de trades |
| 2 | Cycle FOMC : semaines paires (achat) | NASDAQ100, SP500 | ≈ 4 swings de 5 j par cycle | A− | Aucune preuve publique après 2018 |
| 3 | Dollar faible les jours de FOMC | EURUSD, GBPUSD, AUDUSD | 8 jours/an | A−/B | t = 1,69 seulement après coûts, dans l'étude elle-même |
| 4 | Dérive nocturne à l'ouverture européenne | SP500, NASDAQ100 | Quotidienne (jours de repli) | A puis disparue | Nulle depuis 2021 selon la Fed de New York |
| 5 | Saisonnalité horaire EURUSD / GBPUSD | EURUSD, GBPUSD | Quotidienne (2 jambes) | B | Gain de quelques pips ≈ coût CFD |
| 6 | Or : règle NFP inchangée appliquée au CPI et au FOMC | XAUUSD | ≈ 20 jours/an | B + preuve interne | Aucune preuve publique de rentabilité ; dérapage |
| 7 | Rééquilibrage institutionnel 60/40 | SP500 (+ obligations) | Quotidienne / fin de mois | B | Exige une série obligataire absente des données |
| 8 | Dérive avant les annonces de 10:00 | SP500, NASDAQ100 | ≈ 4 annonces/mois | B | Liée à des fuites ; persistance après 2014 non vérifiée |
| 9 | Nombres ronds en forex | EURUSD, GBPUSD, AUDUSD, USDJPY | Quotidienne | B− | Aucun test de rentabilité publié |
| 10 | ORB « stretch » de Crabel | NASDAQ100, SP500 | Quotidienne | D | Très proche du Williams déjà validé |

### Piste 1 : prime des jours d'annonce macro (indices US), preuve A
- **Règles** : NASDAQ100 et SP500, en données journalières tirées du M1.
  - Jours retenus : publication de l'emploi (NFP, 08:30 NY), de l'inflation (CPI, 08:30 NY) et décision FOMC programmée (14:00 NY).
  - Achat au dernier prix de séance (15:59 NY) la veille de l'annonce, sortie à 15:59 NY le jour de l'annonce.
  - Pas de stop : 1 R = ATR14 journalier (convention du dépôt). Une nuit de swap ; coûts ×2 (jour d'annonce).
- **Différence avec les tests faits** : le dépôt a testé l'avant-FOMC (`calendrier` V10-V11 : t 1,26 et 1,82) et des
  cassures d'annonce, mais pas l'achat les jours de NFP et de CPI.
- **Preuves** :
  - [Savor & Wilson (2013), JFQA 48(2), 343-375](https://ideas.repec.org/a/cup/jfinqa/v48y2013i02p343-375_00.html) :
    sur 1958-2009, rendement excédentaire moyen de **11,4 pb** les jours d'annonce contre **1,1 pb** les autres jours ;
    « over 60% of the cumulative annual equity risk premium is earned on announcement days ».
  - [Ai, Bansal & Guo (2023), NBER WP 31923](https://www.nber.org/system/files/working_papers/w31923/w31923.pdf) :
    sur 1961-2023, **10,68 pb** par jour d'annonce contre **0,93 pb** ; ces jours rapportent 4,65 % par an sur une prime
    de 6,59 % ; de janvier 2020 à août 2023, **16,33 pb** par annonce.
- **Risques** :
  - La part FOMC a disparu en 2016-2019. D'après
    [Kurov, Wolfe & Gilbert](https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf),
    la dérive pré-FOMC passe d'environ 44,5 pb (réunions avec conférence de presse, 2011-2015) à environ **9,2 pb**
    (2016-2019). Ce niveau n'est plus différent des jours sans annonce (environ 5,4 pb).
  - Environ 30 trades par an : un t ≥ 3 sera difficile à atteindre seul.
  - Corrélation avec les stratégies d'achat d'indices déjà validées (RSI2, 3 baisses).

### Piste 2 : cycle FOMC, semaines paires (indices), preuve A−
- **Règles** : NASDAQ100 et SP500 (FTSE100 et NIKKEI225 en contrôle, car l'effet existe aussi sur le MSCI hors US).
  - Comptage : jour 0 = jour de la décision FOMC programmée (2e jour si la réunion dure 2 jours). On compte en jours ouvrés
    (week-ends retirés, jours fériés comptés).
  - Semaines paires : semaine 0 = jours −1 à +3, semaine 2 = +9 à +13, semaine 4 = +19 à +23, semaine 6 = +29 à +33.
  - Achat à 15:59 NY la veille du 1er jour de chaque semaine paire, vente à 15:59 NY le dernier jour de cette semaine.
  - 1 R = ATR14, pas de stop. Variante : semaines 2, 4 et 6 seulement, car la semaine 0 recouvre l'avant-FOMC déjà testé.
- **Preuves** :
  - [Cieslak, Morse & Vissing-Jorgensen (Journal of Finance, 2019), SSRN](https://papers.ssrn.com/abstract=2687614) :
    « the equity premium is earned entirely in weeks zero, two, four and six in FOMC cycle time ».
  - [Version PDF consultée](https://stern.nyu.edu/sites/default/files/assets/documents/cycle_paper_cieslak_morse_vissingjorgensen.pdf),
    échantillon 1994-2013 :
    - rendement excédentaire moyen sur 5 jours : semaine 0 = 0,57 %, semaine 2 = 0,30 %, semaine 4 = 0,42 %, semaine 6 = 0,61 % ;
    - semaines impaires : environ 0 %, −0,17 %, −0,17 % et −0,12 % ;
    - rester hors du marché les semaines impaires donne un Sharpe d'environ 0,8, contre environ 0,4 en achat-conservation ;
    - le motif est présent dans chacune des 3 sous-périodes.
  - [Morse & Vissing-Jorgensen (2020)](https://conference.nber.org/conf_papers/f142652/f142652.pdf) : rendements
    supérieurs de **11 pb par jour** en semaine paire sur février 2007-novembre 2018. C'est le seul prolongement trouvé.
- **Risques** :
  - Aucune preuve publique après 2018 n'a été trouvée.
  - Le gain de la semaine 0 vient surtout du jour 0 (avant-FOMC), un effet disparu après 2015 (piste 1).
  - Environ 5 nuits de swap par trade.

### Piste 3 : dollar faible les jours de FOMC (forex), preuve A−/B
- **Règles** :
  - Panier équipondéré EURUSD + GBPUSD + AUDUSD, compté comme 1 trade (3 jambes de 33,3 € de risque).
  - USDJPY est exclu : l'effet n'y est pas significatif dans l'étude.
  - Achat du panier (vente du dollar) à 16:00 NY la veille de la décision, vente à 16:00 NY le jour de la décision,
    comme dans la fenêtre 16:00-16:00 de l'étude.
  - 1 R = ATR14 de chaque paire ; coûts ×2.
  - Environ 125 trades sur 2011-2026.
- **Preuves** : [Mueller, Tahbaz-Salehi & Vedolin, Journal of Finance 72(3), 1213-1252 (2017)](https://researchonline.lse.ac.uk/id/eprint/77256),
  chiffres tirés de la [version de juin 2016](https://drupalgsb-test.paas.cc.columbia.edu/sites/default/files-efs/pubfiles/15021/Exchange%20Rates%20andMonetary%20Policy%20Uncertainty_June2016.pdf),
  échantillon 1994-2013 :
  - portefeuille vendeur de dollar : **10,77 pb** les jours FOMC (t 2,27), contre 0,47 pb les autres jours ;
  - par devise : EUR 10,14 pb, GBP 13,45 pb, AUD 17,28 pb, JPY −4,33 pb (non significatif) ;
  - **après les écarts achat-vente : 8,02 pb (t 1,69, Sharpe annualisé 0,38)**.
- **Risques** : même dans l'étude, la preuve après coûts est faible ; seulement 8 trades par an ; aucune donnée publique
  après 2013 n'a été trouvée.

### Piste 4 : dérive nocturne à l'ouverture européenne (indices US), preuve A puis disparition documentée
- **Règles** :
  - SP500 et NASDAQ100, version « achat après repli ». C'est la seule version rentable après coûts dans l'étude.
  - L'étude utilise le déséquilibre d'ordres signé de la clôture, qu'on n'a pas dans les données. Remplacement proposé, que
    les auteurs n'ont pas testé : rendement 15:30-16:00 NY de la veille < 0.
  - Achat à 01:30 NY, sortie à 03:30 NY (fenêtre « OD+ » de l'étude). Stop à 0,25 × ATR14 = 1 R.
- **Différence avec les tests faits** : le dépôt a testé la nuit entière (clôture → ouverture) et la nuit conditionnelle,
  pas cette fenêtre de 2 h.
- **Preuves** :
  - [Boyarchenko, Larsen & Whelan (RFS 2023), Staff Report 917 de la Fed de New York](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf),
    E-mini S&P sur 1998-2020, fenêtre 02:00-03:00 ET :
    - **1,48 pb par jour** (environ 3,7 % par an), t 7,1, positive 20 années sur 23 ;
    - Sharpe 1,1 avant coûts et **environ −0,5 après coûts** ;
    - fenêtre élargie 01:30-03:30 : Sharpe 1,3 avant coûts, 0,3 après ;
    - « achat après repli » : Sharpe 1,8 avant coûts, **1,1 après**.
  - [Fed de New York, Liberty Street Economics (juillet 2026)](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/) :
    la fenêtre de 2 h à 3 h « has averaged close to zero since 2021 » (2021-2025, 1 245 jours). L'écart-type du
    déséquilibre de clôture est passé de 6,5 % à 2,9 %.
- **Risques** :
  - Effet nul depuis 2021, ce qui est documenté.
  - Le coût fixe du dépôt (Nasdaq 1,5 pt) vaut environ 6,5 pb quand l'indice était à environ 2 300 en 2011 (calcul
    indicatif). C'est plus que le gain moyen de l'heure.
  - Le remplacement du déséquilibre d'ordres par un rendement n'est pas validé.
  - Le dépôt signale des décalages horaires résiduels en mars et en octobre.

### Piste 5 : saisonnalité horaire EURUSD / GBPUSD (« une devise baisse pendant ses propres heures »), preuve B
- **Règles** (reprises de la réplication QuantRocket, en heure de New York) :
  - Jambe 1 : vente EURUSD de 03:00 à 11:00 NY. Jambe 2 : achat de 11:00 à 16:00 NY, prise seulement si la jambe 1 perd
    (règle d'Anto).
  - Stop à 0,5 × ATR14 journalier = 1 R ; sinon sortie à l'heure prévue. GBPUSD avec la même règle, en contrôle.
- **Différence avec les tests faits** :
  - le « test aveugle » de l'heure (lot 6) choisissait les créneaux après coup ;
  - le fix WM testé (V05) était un retournement conditionnel ;
  - ici, l'hypothèse est fixée à l'avance.
- **Preuves** :
  - [Breedon & Ranaldo, JMCB 45(5), 953-965 (2013)](https://ideas.repec.org/a/mcb/jmoncb/v45y2013i5p953-965.html),
    [document de travail BNS 2011-04](https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04)
    (données EBS 1997-2007) :
    - EURUSD : vendre l'euro aux heures européennes donne un **Sharpe de 1,3**, l'acheter aux heures US un **Sharpe de
      0,9**, écarts achat-vente compris ;
    - pour les autres paires : « most of these simple time-of-day trading strategies are not profitable when trading
      costs are included ».
  - [QuantRocket (17/02/2019)](https://www.quantrocket.com/blog/business-day-fx-patterns/) : sur EURUSD, données horaires
    depuis 2005, **TCAC de 6,2 % et Sharpe de 0,70**. Hypothèses : spread moyen de 0,15 pb et commission de 0,2 pb. Le texte
    ne précise pas si ces chiffres sont nets ou bruts.
  - [Krohn, Mueller & Whelan (2022)](https://www.wu.ac.at/fileadmin/wu/d/ri/isk/VSFX_2022/Paper/Session_III_1a_Krohn__foreign_Exchange_Fixings_Returns_Around_The_Clock_0712.pdf) :
    - sur 1999-2019, le dollar monte avant les fixings et baisse après, d'environ 2 pb par fenêtre ;
    - le résultat devient **négatif après coûts** pour un client qui paie l'écart ;
    - le retournement de la fenêtre européenne n'est **pas significatif sur 2014-2019**.
  - [Jiang (SSRN 2613592, révisé en 2019)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2613592) : les devises
    européennes montent en moyenne pendant les heures US.
  - [Longmore (FXEmpire, mis à jour le 08/06/2026)](https://www.fxempire.com/education/article/fx-seasonality-what-still-works-and-what-doesnt-in-2026-1545003) :
    gain moyen de « a handful of pips » par aller-retour, très sensible aux coûts.
- **Risques** : le coût du dépôt sur EURUSD (1,5 pip, environ 1,4 pb, calcul indicatif) est près de 9 fois le spread de
  la réplication. L'avantage est probablement absorbé, et un affaiblissement est documenté après 2014.

### Piste 6 : or, règle NFP inchangée appliquée au CPI et au FOMC, preuve B + preuve interne
- **Règles** : celles de `nfp/backtest.py`, sans aucun changement.
  - Range des 30 minutes avant l'annonce : 08:00-08:30 NY pour le CPI, 13:30-14:00 NY pour le FOMC.
  - On prend le 1er franchissement entre l'annonce et l'annonce + 2 h 30 (au plus tard 15:30), dans les deux sens.
  - Stop au bord opposé ; sortie au TP 1:2 ou à 16:00 ; coûts ×2.
- **Différence avec les tests faits** : `events/backtest.py` n'a testé le CPI et le FOMC que sur le Nasdaq et le S&P, pas
  sur l'or.
- **Preuves** :
  - [Elder, Miao & Ramchander, JBF 36(1), 51-65 (2012)](https://ideas.repec.org:443/a/eee/jbfina/v36y2012i1p51-65.html) :
    sur 2002-2008, la réaction des métaux aux surprises macro est « swift and significant ». Les publications de 08:30
    ont le plus d'effet (NFP, commandes de biens durables).
  - Preuve interne : NFP or validé, 160 trades, t 4,6, et t 2,65 hors échantillon sur 2011-2019 (`campagne/README.md`).
- **Risques** :
  - Aucune preuve publique de la rentabilité de la cassure : les études montrent seulement que l'or réagit.
  - Dérapage : d'après le dépôt, plus de 2 $ de dérapage par trade annulent le gain du NFP or.
  - Chaque nouveau type d'annonce compte comme une variante (tests multiples).

### Piste 7 : rééquilibrage institutionnel 60/40, preuve B (donnée externe nécessaire)
- **Règles** :
  - Suivre la dérive d'un portefeuille 60 % actions (SP500) / 40 % obligations (contrat US 10 ans, à ajouter aux données).
  - Si les actions sont en surpoids au-delà d'un seuil, vendre le SP500 le lendemain.
  - Même logique pendant la dernière semaine du mois.
- **Preuves** : [Harvey, Mazzoleni & Melone, NBER WP 33554 (mars 2025, révisé en janvier 2026)](https://www.nber.org/papers/w33554) :
  « leading to a decrease in equity returns of 17 basis points over the next day ». Échantillon : E-mini S&P et T-note
  10 ans, de mi-septembre 1997 à mi-mars 2023
  ([résumé CXO](https://cxoadvisory.com/calendar-effects/exploiting-predictable-institutional-portfolio-rebalancing)).
- **Risques** :
  - Article non encore publié dans une revue.
  - La construction exacte du signal à seuil n'est pas publique dans les extraits lus (non vérifié).
  - Piste incompatible avec les seules données M1 actuelles.

### Piste 8 : dérive avant les annonces de 10:00 (indices), preuve B
- **Règles** :
  - Jours concernés : ISM manufacturier, ISM services, ventes de logements existants, promesses de ventes (heure de 10:00 NY
    à confirmer sur les calendriers officiels).
  - m = prix à 09:58 − prix à 09:30. Si |m| ≥ 0,1 × ATR14, entrée dans le sens de m à 09:59.
  - Stop à 0,25 × ATR14, sortie à 10:15.
- **Preuves** : [Kurov, Sancetta, Strasser & Wolfe, JFQA (brouillon du 10/11/2017)](https://www.skidmore.edu/economics/documents/KSSW2017-PriceDriftBeforeUSMacroeconomicNews.pdf),
  E-mini S&P de 2008 à 2014 :
  - le prix part dans le bon sens environ 30 minutes avant la publication, soit environ 49 % du mouvement entre −30 min
    et +5 min ;
  - 4 annonces sur 20 sont concernées : ISM non manufacturier, promesses de ventes, ISM manufacturier, ventes de logements
    existants ;
  - l'effet est négligeable sur 2003-2007.
- **Risques** : effet attribué à des fuites d'information, persistance après 2014 non vérifiée ; la fenêtre coïncide avec
  l'ouverture (bruit).

### Piste 9 : nombres ronds en forex, preuve B−
- **Règles** : deux hypothèses d'Osler, testées séparément, entre 03:00 et 12:00 NY. Une « figure » est un niveau rond :
  x,xx00 en général, xxx,00 pour USDJPY.
  - **(a) Accélération** : 1re clôture M1 à au moins 3 pips au-delà d'une figure, alors que le prix de 03:00 était à au
    moins 15 pips de l'autre côté. Entrée dans le sens du franchissement, stop 20 pips de l'autre côté de la figure,
    objectif 2 R, sortie à 16:00 NY.
  - **(b) Retournement** : au 1er contact avec une figure, entrée dans le sens inverse, stop 20 pips au-delà, objectif 2 R.
- **Preuves** :
  - [Osler, Journal of Finance, p. 1791-1819 (2003)](https://academicnewsletter.sufe.edu.cn/info/361290)
    ([version Fed de New York](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.html)) :
    - les take-profit se concentrent sur les nombres ronds, les stop-loss juste au-delà ;
    - d'où deux effets : « trends tend to be reversed at predictable support and resistance levels » et « trends gain
      momentum once predictable support and resistance levels are crossed ».
  - Or : [Aggarwal & Lucey, RFE 16(2) (2007)](https://ideas.repec.org/a/eee/revfin/v16y2007i2p217-230.html) et
    [Lucey & O'Connor, FRL 17 (2016)](https://ray.yorksj.ac.uk/id/eprint/1438/1/The%20Gap%20Psychological%20Barriers%20in%20Gold%20and%20Silver%20Prices.pdf).
    Ces derniers trouvent des barrières aux dizaines pour l'or et aucune pour l'argent, sur 1975-2015.
- **Risques** :
  - Aucune étude ne teste la rentabilité nette.
  - Les paramètres (3, 15 et 20 pips) sont arbitraires.
  - Coût d'environ 0,065 R par trade (1,5 pip pour environ 23 pips de risque, calcul indicatif).

### Piste 10 : ORB « stretch » de Toby Crabel (Nasdaq, S&P), preuve D
- **Règles** :
  - S = moyenne, sur les 10 séances précédentes, de min(H − O, O − L), séance 09:30-16:00 NY.
  - À 09:30, achat stop à O + S et vente stop à O − S.
  - Le 1er ordre déclenché ouvre la position ; l'ordre opposé sert de stop (risque 2S) et de retournement. Le 2e trade
    n'existe donc que si le 1er perd, ce qui colle à la règle d'Anto. Sortie à 16:00.
- **Preuves** : [Crabel, « Playing the Opening Range Breakout », Technical Analysis of Stocks & Commodities v6:9, p. 337-339 (1988)](https://store.traders.com/-v06-c09-playing-pdf.html).
  La description publique ne contient aucune statistique.
- **Risques** : piste très proche du Williams k = 0,5 déjà validé, donc corrélation forte probable ; les ORB ont échoué
  hors Nasdaq dans le dépôt.

### Écartées après lecture
- **Momentum intrajournalier sur l'or et le forex** ([Baltussen et al.](https://academicweb.nd.edu/~zda/intramom.pdf)) :
  pour les devises, coefficient de 0,33 (t 1,45, non significatif) sur 2000-2020 ; R² hors échantillon de 0,07 % pour les
  matières premières.
- **Fix de Tokyo** (Krohn et al.) : déjà couvert par le Gotobi et son témoin (`metaux_forex` V01-V03).
- **Retournement du mardi** : seuls existent des backtests de praticiens
  ([SPY : 212 trades, +0,3 % par trade, TCAC 1,8 %, règles payantes](https://quantifiedstrategies.substack.com/p/turnaround-tuesday-strategy-backtest)),
  et l'idée recouvre le RSI2 et les 3 baisses déjà validés.
- **Règle des 80 % (Market Profile)** : le seul chiffrage trouvé vient d'un forum
  ([ES, plus de 1 000 jours : 20 réussites sur 23 dans une version souple, 6 sur 12 côté vendeur](https://nexusfi.com/a/concepts/80-percent-rule)).
- **Annonces des banques centrales hors Fed sur les indices** :
  [Brusa, Savor & Wilson (RoF 2020)](https://ideas.repec.org/a/oup/revfin/v24y2020i2p263-304..html) ne trouvent
  « no comparable result for other central banks ».

## 2. Ce que disent les preuves sur la régularité

- **ESMA, communiqué du 27/03/2018** ([lien](https://www.esma.europa.eu/node/84933)) : « 74-89% of retail accounts
  typically lose money », avec des pertes moyennes par client de **1 600 € à 29 000 €**. Depuis, chaque broker doit
  afficher son propre pourcentage, recalculé **tous les 3 mois sur les 12 mois précédents**
  ([annexe II de la décision](https://www.esma.europa.eu/sites/default/files/library/esma35-43-1135_notice_of_pi_decisions_on_cfds_and_binary_options.pdf)).
- **Mentions relevées le 18/10/2026** :
  - [XTB France](https://www.xtb.com/fr) : 77 % ;
  - [Plus500 France](https://www.plus500.com/fr-FR/) : 80 % ;
  - [Saxo France](https://www.home.saxo/fr-fr) : 66 %.
- **FCA, 06/12/2016** ([lien](https://fca.org.uk/news/press-releases/fca-proposes-stricter-rules-contract-difference-products)) :
  « 82% of clients lost money » sur un échantillon représentatif de comptes CFD.
- **AMF, Lettre de l'Observatoire de l'épargne n° 10, octobre 2014** ([PDF](https://www.amf-france.org/sites/institutionnel/files/contenu_simple/lettre_ou_cahier/lettre_observatoire/La%20lettre%20de%20l%27Observatoire%20de%20l%27epargne%20de%20l%27AMF%20-%20ndeg%2010%20-%20Octobre%202014.pdf)),
  14 799 particuliers en forex et CFD, 2009-2012 :
  - **plus de 89 % de perdants** sur 4 ans, environ 84 % par an ;
  - perte moyenne d'environ 10 900 €, perte médiane de 1 843 € ;
  - 13 224 clients ont perdu environ 175 M€, tandis que 1 575 ont gagné 13,8 M€ ;
  - à 1 000 ordres ou plus, la perte moyenne atteint 31 349 €.
- **Barber, Lee, Liu & Odean, JFM 18 (2014)** ([lien](https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html)) :
  à Taïwan sur 1992-2006, « Less than 1% of the day trader population is able to predictably and reliably earn positive
  abnormal returns net of fees ».
- **Barber, Lee, Liu, Odean & Zhang, document de travail d'octobre 2017** ([PDF](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/day%20trading%20and%20learning%20110217.pdf)) :
  - plus de 75 % des day traders arrêtent en moins de 2 ans ;
  - la part de day traders rentables reste d'environ 5 % ;
  - la performance agrégée nette est négative chacune des 15 années.
- **Chague, De-Losso & Giovannetti (2019)** ([lien](https://ideas.repec.org/p/fgv/eesptd/525.html)), contrats à terme sur
  indice au Brésil, 2013-2015, personnes ayant fait au moins 300 jours de day trading :
  - **97 % ont perdu de l'argent** ;
  - 0,4 % ont gagné plus qu'un guichetier de banque (54 $ par jour) ;
  - le meilleur a gagné 310 $ par jour, avec un écart-type de 2 560 $.
- **Heimer & Simsek, NBER WP 24176** ([lien](https://nber.org/papers/w24176)) : le plafond de levier imposé en 2010 au
  forex des particuliers aux États-Unis a réduit de 40 % les pertes des traders très endettés.
- **Une stratégie « positive tous les jours » existe-t-elle ?** La seule preuve publique trouvée est celle d'un teneur de
  marché à haute fréquence : Virtu Financial, « only one losing trading day » sur 1 238 jours entre 2009 et 2013
  ([S-1 du 10/03/2014](https://www.sec.gov/Archives/edgar/data/0001592386/000104746914002070/a2218589zs-1.htm)). Virtu
  gagne sur l'écart de prix, répété sur des millions d'ordres : ce n'est pas un trader directionnel. **Aucune étude
  trouvée ne montre une stratégie directionnelle simple positive chaque jour.**
- **Calcul indicatif (pas une source)** : avec des jours indépendants et de loi normale, la part de jours positifs dépend
  du Sharpe annuel. Sharpe 1 → 52,5 % ; Sharpe 2 → 55,0 % ; Sharpe 3 → 57,5 % ; Sharpe 5 → 62,4 %. Même un excellent
  système a donc environ 40 % de jours perdants.
- **La règle « 2e trade si le 1er perd »** augmente la part de jours positifs, mais pas l'espérance : celle-ci reste la
  somme des espérances des trades pris. Le dépôt l'a constaté (`reintegration_m1` : plus de jours positifs, mais des
  pertes totales plus lourdes avec un signal perdant).

## 3. Pseudo-code des 3 meilleures pistes

Choix : les pistes 1, 2 et 6. Elles combinent des preuves fortes, un test faisable avec les données M1 et les calendriers
déjà présents dans le dépôt, et un coût supportable, car on exécute en clôture ou sur des stops larges. Les pistes 3, 4 et
5 sont exclues, car leur gain après coûts est faible ou disparu d'après leurs propres sources.

```python
# Commun — protocole jour/PROTOCOLE.md (≤ 20 variantes, règles figées avant calcul, 1 R = 100 €)
import sys; sys.path.insert(0, "/home/claude/aca5983/backtests/campagne")
from lib import load, sessions_ny, COST, SWAP, evaluate, line, regle_anto, stats_jour, line_jour
NFP  = BLS_2011_2019 (campagne/nfp_2011/run.py) + NFP (nfp/backtest.py)              # 2011-2026, déjà vérifiées
FOMC = FOMC (campagne/calendrier/run.py)                                                # 2011-2026, réunions programmées
CPI  = CPI_2011_2019 + CPI (events/backtest.py)   # 2011-2019 à relever : https://www.bls.gov/bls/news-release/cpi.htm
                                                  # (la date est dans l'URL : cpi_01192012 = 19/01/2012)
def seances(inst):            # séances 09:30-16:00 NY complètes ; C = dernier prix < 16:00
    S = sessions_ny(load(inst, "America/New_York"))
    return table jour -> (O, H, L, C=close[-1]) triée
def atr14(T):                 # connu la veille : TR des séances précédentes uniquement
    TR = max(H-L, |H-C_prec|, |L-C_prec|) ; return TR.rolling(14).mean().shift(1)
def nuits(d1, d2): return (d2 - d1).days        # nuits calendaires (swap base 360)
```

### Spécification A : prime des jours d'annonce (piste 1)
```python
for inst in ["NASDAQ100", "SP500"]:                       # V1 Nasdaq, V2 S&P, V3 Nasdaq NFP+CPI seulement
    T = seances(inst); A = atr14(T)
    for d in sorted(set(NFP) | set(CPI) | set(FOMC)):
        if d not in T: log("séance absente", d); continue    # trou 02-07/2023, S&P 2012-14/2017
        p = séance précédente de d dans T
        R = A[d]                                          # ATR connu à la clôture de p
        P_in, P_out = T.C[p], T.C[d]
        gross_r = (P_out - P_in) / R
        cost_r  = 2*COST[inst]/R + nuits(p, d)*SWAP[inst][0]/360*P_in/R      # ×2 : jour d'annonce
        rows += dict(day=d, t_in=ts(p,"15:59"), t_out=ts(d,"15:59"), gross_r=gross_r, cost_r=cost_r,
                     instrument=inst, evt=type(d))
t = regle_anto(DataFrame(rows))      # 1 trade/jour ; jamais de 2e (même t_in), priorité NASDAQ100 si les deux
print(line(evaluate(t, "annonces")), line_jour(stats_jour(t)))
# contrôle (non compté) : mêmes trades les jours SANS annonce → doit être nettement inférieur
```

### Spécification B : cycle FOMC, semaines paires (piste 2)
```python
B = pd.bdate_range("2010-12-01", "2026-10-09")            # jours ouvrés lun-ven (fériés comptés, comme l'article)
def semaine(b):                                           # numéro de semaine dans le cycle FOMC
    f_next = 1re date FOMC >= b ; n = nb de jours ouvrés de b à f_next
    if n == 1: return 0                                   # jour -1 = début de la semaine 0 suivante
    if 2 <= n <= 6: return -1
    f_last = dernière date FOMC <= b ; k = jours ouvrés de f_last à b (k = 0 le jour FOMC)
    return (k + 1) // 5                                   # 0..3→0, 4..8→1, 9..13→2, ..., 29..33→6
PAIRES = {0, 2, 4, 6}                                     # V3 : {2, 4, 6} (sans l'avant-FOMC déjà testé)
for inst in ["NASDAQ100", "SP500"]:                       # V1, V2 ; FTSE100/NIKKEI225 en contrôle seulement
    T = seances(inst); A = atr14(T)
    for bloc in suites de jours consécutifs de B avec semaine(b) in PAIRES:      # ≤ 5 jours
        b1, b2 = bloc[0], bloc[-1]
        e = dernière séance de T < b1 ; s = dernière séance de T <= b2           # sortie à la clôture
        if e is None or s <= e: continue
        R = A[next_session(e)]                            # ATR connu à la clôture de e
        gross_r = (T.C[s] - T.C[e]) / R
        cost_r  = COST[inst]/R + nuits(e, s)*SWAP[inst][0]/360*T.C[e]/R          # exécution en clôture
        rows += dict(day=s, t_in=ts(e,"15:59"), t_out=ts(s,"15:59"), gross_r=gross_r, cost_r=cost_r,
                     instrument=inst)
        # écarter un bloc qui chevauche un trou de données > 7 jours (règle de retour_moyenne)
t = regle_anto(DataFrame(rows)); évaluer comme en A
# contrôle (non compté) : semaines impaires → l'article prédit ≤ 0
```

### Spécification C : or, règle NFP inchangée sur le CPI et le FOMC (piste 6)
```python
EV = {"CPI": (CPI, 510), "FOMC": (FOMC, 840)}             # minute NY de l'annonce (08:30 / 14:00)
df = load("XAUUSD", "America/New_York")
for evt, (dates, t0) in EV.items():                      # V1 CPI, V2 FOMC, V3 CPI+FOMC+NFP (portefeuille)
    for d in dates:
        g = minutes du jour d ; rg = g[(hm >= t0-30) & (hm < t0)]
        if len(rg) < 24: log("range incomplet", d); continue
        hi, lo = rg.high.max(), rg.low.min()
        for m in g[(hm >= t0) & (hm < min(t0+150, 930))]:                        # 1er franchissement
            up, dn = m.high > hi, m.low < lo
            if up and dn: break                           # deux bords dans la même minute : pas de trade
            if up or dn:
                dir = +1 if up else -1
                entree = max(m.open, hi) if up else min(m.open, lo)              # gap → ouverture
                stop = lo if up else hi ; R = abs(entree - stop) ; tp = entree + 2*R*dir
                sortie = 1er de : stop (prioritaire dans la minute ; gap au-delà → ouverture),
                         tp, ou dernier prix < 16:00   (minute d'entrée incluse pour le stop)
                rows += dict(day=d, t_in=ts(d,m), t_out=ts(sortie), instrument="XAUUSD", evt=evt,
                             gross_r=(sortie_px - entree)*dir/R, cost_r=2*COST["XAUUSD"]/R)
                break
t = regle_anto(DataFrame(rows))      # CPI 08:30 puis FOMC 14:00 le même jour : le 2e seulement si le 1er perd
évaluer ; contrôle de sensibilité au dérapage : +1 $ puis +2 $ par trade (le NFP or devient nul à +2 $)
```

Contrôles communs : vérifier 2 trades à la main sur le M1 brut ; signaler les jours d'annonce sans données (trou
02-07/2023) ; enregistrer toutes les variantes, y compris les échecs, dans un `results.json`.
