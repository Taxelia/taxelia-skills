---
name: legifrance-ingest
description: Ingère une page Légifrance (ordonnance, loi, code, articles fiscaux) et la transforme en graphes de décision Taxelia via l'API REST — extraction du texte et des tableaux, classement de chaque article, conception validée (architecture, catalogue, marqueurs, valeurs par défaut), construction par lots testés, passe finale. À utiliser quand l'utilisateur donne une URL legifrance.gouv.fr et veut en tirer des règles/graphes Taxelia, ou dit « ingère ce texte », « transforme cette page en arbres », « /taxelia:legifrance-ingest <url> ».
---

# Ingestion d'un texte Légifrance en graphes Taxelia

Tu transformes un texte fiscal publié sur Légifrance en graphes de décision exécutables par le moteur
Taxelia, dans un workspace, via l'API REST. La démarche est **complète, avec deux points d'arrêt de
validation** par l'utilisateur. Elle reprend la méthode qui a produit le workspace `cibs-2027`
(CIBS Livre II, 1 042 articles, 40 graphes) et **tous les pièges rencontrés** : lis
`references/pitfalls.md` avant de commencer, et relis-le avant chaque phase de construction.

`<skill>` désigne le répertoire de base de ce skill (indiqué quand il est lancé) : tous les chemins
`references/…` et `scripts/…` ci-dessous sont relatifs à lui ; appelle les scripts par leur chemin
absolu (`python3 <skill>/scripts/imp.py …`).

Références (à lire quand la phase le demande, pas toutes d'un coup) :
- `references/engine-and-api.md` — sémantique exacte du moteur, endpoints, format d'import, `/search`.
- `references/modeling.md` — comment découper, concevoir le catalogue, les marqueurs, les valeurs par défaut, les tests.
- `references/pitfalls.md` — les pièges, numérotés (P1…). À citer dans tes consignes aux sous-agents.
- `references/brief-reader.md` — consigne des agents de lecture (phase 2).
- `references/brief-builder.md` — consigne des agents de construction (phase 5).
- `scripts/` — outils (voir `scripts/README.md`).

Langue : tu parles français à l'utilisateur. Les clés du catalogue sont en anglais snake_case ; libellés,
noms de nœuds et textes de sortie en français correct (accents).

## Phase 0 — Cadrage (toujours, avant toute action)

1. **Première question, obligatoire** : utiliser un **workspace existant** ou en **créer un nouveau** ?
   Utilise `AskUserQuestion`. Si existant : lister les workspaces (`GET /workspaces`) et faire choisir.
   Si nouveau : proposer un id (slug `^[a-z0-9][a-z0-9-]{1,62}$`, ex. `cibs-2027`), un nom, une description.
2. **API** : l'API publique de Taxelia, `https://taxelia.bizyness.fr` (`/search` sans clé, routes
   `/workspaces/**` avec une clé). Vérifie qu'elle répond (`GET /health`). Les écritures y modifient des
   données partagées : annonce ce que tu vas créer ou modifier et obtiens l'accord de l'utilisateur avant
   la première écriture, et avant toute modification d'un workspace existant (P40).
3. **Clé API en écriture** : demande-la à l'utilisateur (ne va jamais la chercher en base : refusé, P39).
   Stocke-la dans `<work>/.apikey` (chmod 600) ; ne l'affiche jamais, ne la committe jamais.
4. **Répertoire de travail** : `<work>` = `<racine du projet ouvert>/ingest-work/<workspace>/` par défaut
   (propose-le, l'utilisateur peut en choisir un autre ; ne le mets pas dans un dépôt git : il contient la clé).
   Écris `<work>/ingest.json` (lu par tous les scripts) :
   `{"api": "https://taxelia.bizyness.fr", "workspace": "<id>", "primary_id": "<id>_principal", "primary_name": "<nom /search>"}`.
5. **Workspace existant** : exporte d'abord l'état (`<skill>/scripts/ws.py export`) et sauvegarde-le dans
   `<work>/backup-<date>.json`. Lis ses graphes et son catalogue : la conception devra s'y intégrer
   (réutiliser les clés, ne pas casser le graphe primaire, ne rien supprimer sans accord). Rappel P38 :
   un workspace dupliqué ne peut pas être « promu » en retour ; si l'utilisateur veut un bac à sable,
   le dire avant de dupliquer.
6. Demande aussi, si ce n'est pas clair : le périmètre (tout le texte ou certains chapitres) et la
   date d'effet à utiliser dans les scénarios.

## Phase 1 — Extraction du texte (Légifrance est derrière Cloudflare)

`curl`/`WebFetch` échouent (page de challenge Cloudflare, P1). Utilise le **navigateur intégré** :
1. `navigate` vers l'URL, puis vérifie `document.title`. S'il reste « Un instant… » plus de ~20 s,
   demande à l'utilisateur d'afficher le panneau du navigateur et, si une vérification anti-robot
   s'affiche, de la faire lui-même (jamais toi) ; reprends quand le titre est celui du texte.
2. Exécute `<skill>/scripts/extract_legifrance.js` avec l'outil `javascript_tool` : il construit dans la page
   `window.__lf` = texte intégral où **chaque tableau est réinjecté en markdown à sa place** (Légifrance
   masque les tableaux derrière « Afficher le tableau », P2), et renvoie la taille et le nombre de tableaux.
3. Récupère le texte par tranches (`window.__lf.slice(i, i+40000)` à chaque appel) et écris chaque
   tranche dans `<work>/source.txt` (un `fetch` depuis la page vers une autre adresse est bloqué par sa CSP, P3).
4. Contrôle : `python3 <skill>/scripts/split_lots.py <work>/source.txt --stats` liste les articles, les en-têtes
   de chapitres et les numéros manquants (souvent des articles abrogés/inexistants, P4 — ne pas les
   signaler comme perdus sans vérifier).

## Phase 2 — Lecture et classement de TOUS les articles (en parallèle)

1. `python3 <skill>/scripts/split_lots.py <work>/source.txt --lots <work>/lots --max-chars 60000` découpe par
   chapitres en lots équilibrés.
2. Lance un sous-agent par lot (en parallèle, dans un seul message, modèle intermédiaire suffisant),
   avec `references/brief-reader.md` complété : chemin du lot, fichier de sortie `<work>/out/NN.md`,
   **vocabulaire de clés commun** (pour que les lots convergent, P24) et blocs attendus.
3. Chaque article reçoit une catégorie : `REGLE`, `DEFINITION`, `HORS_MODELE` (calcul, procédure,
   délai… le moteur n'a ni variables ni arithmétique, P7) ou `RENVOI`.
4. `python3 <skill>/scripts/coverage.py <work>` vérifie que chaque article du texte est classé une fois.
5. Pour chaque article `DEFINITION` : décider s'il sera **déduit par un graphe de qualification** (faits
   bruts → marqueur) ou **décrit** en entier dans le catalogue. Aucune qualification juridique définie par
   le texte ne doit rester une question posée à l'appelant (P44–P46).

## Phase 3 — Consolidation (une passe, puis POINT D'ARRÊT 1)

Un sous-agent (modèle le plus capable) produit `<work>/consolidation.md` en suivant
`references/modeling.md` : chiffres, **un seul graphe primaire**, découpage des sous-graphes **d'abord
par réutilisation**, chaîne d'étapes et fin de chaîne commune, **vocabulaire des marqueurs**, catalogue
unifié (clés, types, valeurs, libellés, `legalBasis`, **décisif ou valeur par défaut**), conventions de
sortie (`tax_rate` explicite à 0 pour les exonérations, P30), ordre de construction et scénarios, points
à trancher (≤ 8, chacun avec une recommandation).

Avant l'arrêt, fais une **revue des qualifications** : pour chaque input du catalogue proposé, fait brut,
qualification définie (à déduire), qualification non déductible (à décrire) ou appréciation ; aucune
description de brouillon (P49) ; aucune notion inventée (P47).

**Arrêt 1** : présente à l'utilisateur la synthèse (nombre de graphes, blocs réutilisables, marqueurs,
points à trancher avec recommandations) et envoie le fichier (`SendUserFile`). N'avance qu'après
validation. Intègre ses décisions dans le document.

## Phase 4 — Workspace et catalogue

1. Nouveau workspace : `<skill>/scripts/ws.py create --id … --name … --description … --strict` (mode strict
   **activé** pour tout nouveau modèle, P15). Existant : ne change pas son mode sans accord (un
   workspace en production écrit en mode souple changerait de réponses, P16).
2. Construis `<work>/catalog.json` depuis la consolidation (règles de libellés P33–P35, valeurs par
   défaut P18–P20) et importe-le seul : `python3 <skill>/scripts/imp.py <work>/catalog.json` (dry-run puis réel).
   L'import écrase chaque entrée **complètement** (P32) : toujours envoyer l'entrée entière.

## Phase 5 — Construction par lots (du bas vers le haut)

- Ordre : d'abord les graphes qui ne renvoient vers rien (fin de chaîne), le primaire en dernier (une
  référence doit viser un graphe existant ou présent dans le même fichier, P27).
- Un sous-agent par lot (≤ ~6 graphes), **séquentiels** (les imports et les tests partagent l'API),
  avec `references/brief-builder.md`. Chaque agent écrit un générateur Python avec `<skill>/scripts/dsl.py`,
  fait dry-run puis import (`<skill>/scripts/imp.py`), écrit les scénarios (`<work>/tests/<id>.json`) et joue
  `<skill>/scripts/run_scenarios.py` jusqu'au vert, puis la suite complète (non-régression).
- Pendant la construction, les graphes secondaires portent un nom temporaire `t__<id>` pour être
  testables directement ; `<skill>/scripts/set_names.py on|off` les pose ou les retire (P28).
- Tiens `<work>/controller-notes.md` : défauts signalés dans des graphes déjà construits, à corriger
  toi-même (petites corrections) ou en passe finale ; doutes juridiques.
- Vérifie après chaque lot : `<skill>/scripts/check_couples.py` (0 couple doublé, P11) et, si l'API a ralenti,
  le temps de `POST /workspaces/{ws}/refresh`.

## Phase 6 — Passe finale (puis POINT D'ARRÊT 2)

1. Corrige les défauts de `controller-notes.md` (avec scénarios de non-régression).
2. Suite de bout en bout `<work>/tests/e2e.json` sur le **seul nom primaire**, avec des **faits bruts
   uniquement** (aucun marqueur forcé) : un scénario par grande famille de cas + des requêtes
   incomplètes vérifiant `required` / `not_required` (P21) + `outputs` demandés et `result.complete` (P31).
3. `<skill>/scripts/set_names.py off` (un seul graphe nommé), rejoue l'e2e, `check_couples.py` = 0.
4. `<work>/doutes-juridiques.md` : chaque doute/approximation, regroupé par thème, avec l'état actuel
   des graphes et les options. Mets en tête les incohérences entre lots.

**Arrêt 2** : présente le bilan (graphes, scénarios passés, clés ajoutées, doutes) et envoie les fichiers.
Démontre une requête réelle (corps et réponse `/search`) sur un cas typique.

## Règles transverses

- Les valeurs attendues des scénarios viennent **de la loi**, jamais de la sortie du graphe (P36).
- Ne compare pas avec un autre workspace sauf demande (le modèle est indépendant).
- Toute modification de code d'un dépôt (moteur, éditeur…) sort du périmètre du skill : si un défaut du
  moteur bloque, décris-le à l'utilisateur et demande avant de coder (branche, TDD, pas de push).
- Ne pousse rien, ne déploie rien. Chaque écriture sur l'API se fait avec l'accord de l'utilisateur (P40).
