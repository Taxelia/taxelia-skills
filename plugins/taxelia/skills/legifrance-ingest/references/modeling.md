# Concevoir le modèle (phase 3) et le construire (phase 5)

## 1. Classer avant de modéliser

Chaque article → `REGLE` (décide quelque chose sur UNE opération à partir de faits fournis),
`DEFINITION` (définit une notion → description/`legalBasis` d'une clé ou d'une valeur), `HORS_MODELE`
(calcul, procédure, délai, déclaration, paiement, contrôle, affectation ; peut produire une sortie `info`
sur un chemin), `RENVOI`. Tableau de couverture exhaustif ; les tableaux du texte (taux, seuils) sont des
règles. Sur le CIBS : 531 règles / 222 définitions / 219 hors modèle / 72 renvois.

## 2. Architecture

- **Un seul graphe primaire** (seul graphe nommé en production : c'est la clé `tree` de `/search`).
  Il porte le champ d'application (hors champ, non assujetti…) et l'aiguillage ; il ne fait pas le travail.
- **Sous-graphes découpés d'abord pour la réutilisation** : un bloc appelé depuis plusieurs branches
  (ex. franchise en base) est un graphe. Puis par sous-section du texte, ≤ ~40 nœuds par graphe.
- **Chaîne d'étapes avec une fin commune** (TVA : champ → qualification → lieu → localisation →
  exonérations → redevable → taux → exigibilité → déduction → facturation). Grâce aux outputs lisibles,
  UNE seule fin de chaîne suffit : chaque étape lit les marqueurs posés avant elle (ex. `exemption_kind`)
  au lieu d'avoir des fins parallèles.
- **Arrêts anticipés** (hors champ, non imposable…) : RESULT directement.
- Pour chaque graphe : id, titre, articles, type (terminal / continue vers X), appelants, taille ;
  puis une matrice de réutilisation.
- Ordre des exceptions : ce que le texte dit « par dérogation » passe **avant** la règle générale
  (arêtes dans l'ordre de priorité ; première qui correspond gagne).

## 3. Marqueurs (outputs lisibles)

Un marqueur est un output texte non cumulatif, déclaré en **output** au catalogue, posé par l'étape qui
décide et **lu en condition** par les étapes suivantes. Définis le vocabulaire une fois (clé, valeurs,
qui l'émet, qui le lit) avant de construire. Ceux de `cibs-2027` (réutilisables pour la TVA) :
`operation_qualification`, `taxable_country`, `place_basis`, `taxable_territory`, `margin_scheme`,
`exemption_kind` (aucune / fonctionnelle / fonctionnelle_limitee / derogatoire / franchise),
`exemption_basis` (code article), `taxation_option_exercised`, `regime`, `liable_person`, `rate_level`,
`invoice_waiver`.
Règles : un marqueur n'est émis que par UNE étape sur un chemin donné (pas de collision) ; initialise-le
explicitement quand une étape en dépend (ex. `exemption_kind = aucune` à l'entrée) ; un marqueur non
encore posé est « faux » (jamais demandé) ; en production seul un marqueur explicitement prévu peut être
forcé par l'appelant (dans `cibs-2027` : `taxable_territory`) — les autres sont réservés (P13).
Une valeur numérique à relire doit voyager en texte (ex. `rate_level` → `taux_niveau` → `tax_rate`).

## 4. Catalogue

- Clés = **faits bruts** que l'appelant connaît (pays du client, transport, catégorie de bien…), pas des
  conclusions juridiques. Fusionne les synonymes proposés par les lots (liste des renommages).
- Pour les `select` : toutes les valeurs, avec l'article de chacune dans la description d'option si utile.
- Seuils : un `NUMBER` (`fieldType text`) quand la loi fixe le chiffre et que l'appelant détient la
  donnée (CA N-1 et N séparés) ; un booléen pré-calculé quand le seuil est fixé par arrêté ou dépend de
  cumuls pluriannuels / de tiers.
- Appréciations subjectives (distorsion de concurrence, « savait ou ne pouvait ignorer ») : booléens
  déclaratifs ; sans affirmation positive → droit commun, avec une `info`.
- **Décisif ou valeur par défaut** (mode strict) : `defaultValue` pour les situations rares dont la
  réponse normale est évidente et sans risque à supposer (bon, opération illicite, vente à bord, chaîne,
  option non exercée, `aucun`…) ; **aucune valeur par défaut** pour ce qui change le résultat d'une
  opération courante (nature/catégorie, pays, qualité du client, transport, seuils et CA, établissement…).
  Dans le doute : décisif. Vérifie par simulation qu'une opération ordinaire ne pose que 2 à 8 questions.
- Libellés : français avec accents, courts (≤ 60 car.), sans point final, **tous distincts** (préciser
  année précédente / en cours, « du client / du fournisseur »…), marqueurs nommés d'après ce qu'ils
  retiennent ; description ≠ libellé ; `legalBasis` = articles.

## 5. Conventions de sortie

- `legal_basis` (cumulatif) sur chaque décision : « CIBS L. 213-151 » (préfixe du code concerné).
- `info` (cumulatif) : hypothèses, notes, ce qui est hors modèle mais utile.
- `invoice_mention` (cumulatif) émis par l'étape qui décide (le moteur ne sait pas en fin de chemin
  « pourquoi il est là »).
- `tax_rate` : **toujours explicite** quand la question du taux est tranchée : `0` pour toute exonération
  et tout hors champ ; `0` + `info` pour une autoliquidation par le client à l'étranger ou un territoire
  tiers ; `$pays` (taux normal de ce pays) quand le fournisseur doit la taxe d'un autre État ; taux
  français quand le client autoliquide en France. Absence de `tax_rate` = « non tranché » (cas où la TVA est
  facturée par un fournisseur étranger, par ex.) → `complete: false` si l'appelant demande `tax_rate`.

## 6. Construction

- Générateur Python par lot avec `scripts/dsl.py` (`G`, `q`, `r`, `ref`, `e`, `fb`, `cont`, `t`, `lb`,
  `info`, `inv`, `L`, `dump`) : `dump` vérifie la structure et l'unicité des couples avant d'écrire.
- Pour un OU : une arête `match: any` si ce sont des conditions simples ; sinon un **nœud de suite**
  (`g.cont`) qui porte les arêtes suivantes dans le même ordre de priorité. Jamais deux arêtes sur un couple.
- Mode strict : un nœud atteint par des cas différents ne doit pas tester une clé sans objet pour l'un
  d'eux (un service ne doit pas rencontrer `goods_category`) → garde par marqueur
  (`operation_qualification`) ou par un fait déjà connu, ou mettre en premier l'arête du cas courant.
  Une négation (`ne`) sur un input absent le fait demander.
- Chaque nœud de décision : `legal_basis` exact ; un nœud de sortie par article quand l'article doit être
  cité précisément (les graphes grossissent de 20–40 % par rapport aux estimations, c'est normal).

## 7. Tests

- Par graphe (`<work>/tests/<id>.json`, tree `t__<id>`) : les scénarios de la consolidation + 1–3 par
  branche ; les marqueurs amont peuvent y être **forcés** en input pour tester un graphe isolément (mais un
  marqueur forcé masque ses précisions ultérieures, P13 — ne pas forcer celui que le graphe raffine).
- De bout en bout (`<work>/tests/e2e.json`, tree = nom primaire) : faits bruts uniquement, un scénario
  par famille, requêtes incomplètes (`required`, `not_required`), `outputs` + `result`.
- Format : voir l'en-tête de `scripts/run_scenarios.py` (`expect`, `contains`, `absent`, `required`,
  `not_required`, `outputs` + `result`).
- Attendus = la loi. Si un scénario échoue, corrige le graphe ; ne touche l'attendu que s'il lisait mal
  la loi (et dis-le).
