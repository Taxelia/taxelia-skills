# Consigne des agents de lecture (phase 2) — à copier dans `<work>/brief-reader.md` et compléter

Remplace les `{…}` avant de lancer les agents. Chaque agent reçoit : ce fichier, SON lot, SON fichier de
sortie. Il ne modifie rien d'autre, n'appelle aucune API, ne lance pas de sous-agent.

---

# Consigne : lire et classer les articles d'un lot de {texte, ex. « CIBS Livre II »} pour un modèle de graphes de décision

Tu lis UN lot de {texte} (source Légifrance : {url}, en vigueur au {date}) et tu classes CHAQUE article.
Tu écris seulement ton fichier de sortie. Français pour le contenu, clés en anglais snake_case.

## Ce que deviendront les articles (décide la classification)

Moteur de graphes Taxelia :
- L'appelant envoie des **inputs** plats (faits d'UNE opération). Le moteur suit UN chemin du graphe
  primaire jusqu'à une feuille.
- Nœuds : QUESTION (arêtes sortantes, peut porter des sorties), RESULT (feuille), REFERENCE (saut **sans
  retour** vers un autre graphe : un sous-graphe réutilisé a UNE suite pour tous ses appelants).
- Conditions sur les inputs (et sur les **marqueurs**, sorties texte déjà posées sur le chemin) :
  `eq ne in nin gt lt gte lte`, `all`/`any`, un repli ; valeurs `$autre_cle`, listes `[a,b]`, macros pays
  `europe`/`dom`/`tom` (attention : `europe` inclut FR et MC).
- **Pas de variables, pas d'arithmétique** : pas de base, prorata, cumul, délai calculé. Sorties :
  textes constants, `$input`, `tax_rate` (nombre ou code pays), sorties cumulatives (`legal_basis`,
  `info`, `invoice_mention`).
- Architecture décidée : UN graphe primaire ; sous-graphes découpés d'abord pour la réutilisation.

## Catégories (une par article)

- `REGLE` — décide quelque chose sur une opération à partir de faits qu'un appelant peut fournir.
- `DEFINITION` — définit une notion → description / `legalBasis` d'une clé du catalogue.
- `HORS_MODELE` — calcul, procédure, délai, déclaration, paiement, contrôle, affectation ; raison en
  quelques mots ; préciser si une sortie `info` utile peut en découler.
- `RENVOI` — ne fait que renvoyer ou annoncer un plan.
Les tableaux (réinjectés en markdown) sont des règles ; une ligne sans colonne « conditions » hérite de
la ligne du dessus.

## Sortie (markdown, structure exacte)

### 1. Tableau de couverture
Une ligne par article du lot, dans l'ordre, aucun oublié :
`| Article | Catégorie | Bloc proposé | Résumé (condition → effet, ≤ 25 mots) | Inputs | Outputs |`

### 2. Fiches de règles par bloc
Pour chaque bloc : but, articles, **appelants** (situations qui y mènent — c'est ce qui décide de la
réutilisation), **suite** (feuilles ou bloc suivant), puis les règles :
`- [L. 211-67] SI installation_by_supplier eq true ALORS lieu = lieu d'installation (taxable_country = $installation_country)`
Garder les nuances (exceptions, « par dérogation », options). Signaler toute règle qui exige une
information qu'un appelant ne peut pas raisonnablement fournir.

### 3. Catalogue proposé
`| Clé | INPUT/OUTPUT | Type (BOOLEAN/TEXT/NUMBER/DATE/COUNTRY/SELECT) | Valeurs | Description | legalBasis | Décisif ou défaut proposé |`
Préférer les faits bruts. **Réutiliser le vocabulaire commun ci-dessous** ; n'ajouter qu'en cas de besoin.

### 4. Renvois externes et remarques
Articles hors du lot dont dépend une règle, ambiguïtés, incertitudes.

## Vocabulaire commun (à réutiliser)

{liste des clés d'inputs et d'outputs de départ, avec type — UNIQUEMENT des faits bruts (jamais une
qualification juridique que le texte définit : pas de « nature de l'opération », « assujetti », « à titre
onéreux »… — P44). Ex. pour la TVA : `sale_date` DATE, `supply_kind` SELECT (ce qui est fourni : vente d'un
bien meuble, énergie, immeuble, location, travail sur le bien du client, service ou contenu numérique…),
`supplier_legal_form` SELECT, `supplier_country` / `customer_country` COUNTRY, `transport` BOOLEAN,
`departure_country` / `arrival_country` COUNTRY, `goods_category` / `service_category` SELECT ; sorties
`taxable`, `taxable_country`, `tax_rate`, `invoice_mention`, `legal_basis`, `info`… ; et, pour un workspace
existant, les clés de son catalogue}
Pour chaque article `DEFINITION`, indiquer si la notion doit être **déduite par le graphe** à partir de
faits bruts (et lesquels) ou seulement **décrite** dans le catalogue (P45).

## Blocs attendus (réutiliser les noms quand ils conviennent)

{liste de noms de blocs attendus — ex. « Champ – territoire », « Qualification de l'opération »,
« Lieu – livraisons de biens », « Franchise en base », « Taux », « Exigibilité »…}

## Réponse finale (courte)
Nombre d'articles par catégorie, blocs proposés avec leurs appelants, 3 principales incertitudes.
