# Moteur et API Taxelia — ce qu'il faut savoir pour ingérer des règles

Source de vérité : `back/taxelia-api-core/docs/{domain,architecture}.md` et
`back/taxelia-api-application/docs/api.md`. Relis-les si un comportement te surprend : le code a pu
évoluer depuis l'écriture de ce skill.

## API (auth : en-tête `X-Api-Key: <clé en écriture>` sur toutes les routes `/workspaces/**`)

| Appel | Usage |
|---|---|
| `GET /health` | l'API répond (sans clé) |
| `GET /workspaces` | liste `{id, name, description, createdAt, graphCount, catalogCount, strictInputs}` |
| `POST /workspaces` `{id, name, description?, strictInputs?}` | créer (409 si l'id existe) |
| `PATCH /workspaces/{ws}` `{name?, description?, strictInputs?}` | renommer / basculer le mode strict |
| `POST /workspaces/{ws}/duplicate` `{id, name, description?, strictInputs?}` | copie (catalogue + brouillons + état publié) |
| `GET /workspaces/{ws}/inputs` / `outputs` | catalogue |
| `GET /workspaces/{ws}/graphs` | liste des graphes (id, name, title, versions) |
| `GET /workspaces/{ws}/graphs/export` | catalogue complet + graphes, au format d'import |
| `POST /workspaces/{ws}/graphs/import?dryRun=true` | validation seule → `{"valid":true}` ou `422 {errors:[…]}` |
| `POST /workspaces/{ws}/graphs/import` | applique : upsert catalogue, snapshot complet de chaque graphe du fichier, publication, recompilation du workspace |
| `POST /workspaces/{ws}/refresh` | recompile le workspace |
| `POST /search` (sans clé) | évaluation (ci-dessous) |
| `POST /breadcrumb` (sans clé) | chemin parcouru |

## Format d'import (résumé)

```jsonc
{
  "catalog": {
    "inputs":  [ {"key": "customer_country", "label": "Pays du client", "description": "…", "legalBasis": "CIBS L. 211-76",
                  "fieldType": "location", "defaultValue": null} ,
                 {"key": "voucher_type", "label": "Type de bon", "fieldType": "select", "defaultValue": "aucun",
                  "options": [{"value": "aucun", "name": "Aucun"}, {"value": "bum", "name": "Bon à usages multiples"}]} ],
    "outputs": [ {"key": "tax_rate", "label": "Taux de TVA", "description": "…"} ]
  },
  "graphs": [ {
    "id": "taux_niveau",               // identité (slug lisible accepté) ; créé s'il n'existe pas
    "name": "t__taux_niveau",          // clé /search ; ABSENT pour un sous-graphe en production
    "title": "Conversion du niveau de taux", "description": "But + articles couverts",
    "start": "tn_start",
    "nodes": [ {"key": "tn_start", "type": "question", "name": "Niveau de taux ?", "outputs": [ … ]},
               {"key": "tn_ref",   "type": "reference", "ref": "exigibilite"},
               {"key": "tn_res",   "type": "result", "name": "…", "outputs": [ {"key": "tax_rate", "value": "20"} ]} ],
    "edges": [ {"from": "tn_start", "to": "tn_res", "name": "Normal", "match": "all",
                "conditions": [ {"key": "rate_level", "operator": "eq", "value": "normal"} ]},
               {"from": "tn_start", "to": "tn_ref", "name": "Sinon", "fallback": true, "conditions": []} ]
  } ]
}
```

- `fieldType` : `text` (aussi pour les nombres), `select` (options obligatoires), `date`, `location`
  (code pays ISO), `boolean` (valeurs `"true"`/`"false"` en minuscules).
- `defaultValue` : inputs seulement ; doit être une option pour un `select`, `true`/`false` pour un booléen.
- Output : `key` (déclarée), `type` `text` (défaut) ou `localized` (`translations: [{language, text}]`),
  `value` (texte, `$autre_cle` possible), `cumulative` (défaut `false`).
- Condition : `key` déclarée en input **ou en output** (marqueur), `operator` ∈ `eq ne in nin gt lt gte lte`,
  `value` texte (`"[a,b]"` pour `in`/`nin`, `$autre_cle`, macro pays `europe`/`dom`/`tom`).
- Validation d'import (codes utiles) : `UNDECLARED_INPUT_KEY`, `UNDECLARED_OUTPUT_KEY`,
  `DANGLING_REFERENCE`, `REFERENCE_CYCLE`, `DUPLICATE_EDGE_COUPLE`, `MULTIPLE_START_NODES`,
  `RESULT_NODE_HAS_OUTGOING_EDGE`, `REFERENCE_NODE_HAS_OUTGOING_EDGE`, `INVALID_OPERATOR_VALUE`,
  `DUPLICATE_GRAPH_NAME`, `INVALID_DEFAULT_VALUE`, `GRAPH_ID_IN_OTHER_WORKSPACE`.
- Le fichier ne porte pas de workspace : c'est la route qui décide.

## `/search`

Requête :
```json
{ "workspace": "cibs-2027", "tree": "cibs_2027", "language": "fr", "outputs": ["tax_rate"],
  "conditions": [ {"key": "operation_nature", "value": "goods"}, {"key": "customer_country", "value": "DE"} ] }
```
Réponse : `outputs[] {key, type, values | translations}`, `inputs {provided, required, defaulted}`,
`result {complete, missingOutputs}`.
- `required` : ce qu'il faut encore fournir. En workspace strict, seulement ce qui manque vraiment.
- `defaulted` : valeurs par défaut du catalogue appliquées sur le chemin (hypothèses faites).
- `outputs` demandés : ne modifient PAS le parcours ; `complete = required vide ET tous les outputs demandés produits`.

## Sémantique du moteur (à respecter en concevant)

1. **Un seul chemin**, du départ à une feuille. À chaque nœud, les arêtes sont essayées **dans l'ordre
   du fichier** (création dans l'éditeur) ; la première qui correspond gagne ; sinon l'arête `fallback` ;
   sinon arrêt. Arête `match: all` (toutes les conditions) ou `any` (au moins une).
2. **Une seule arête par couple (source, cible)**, repli compris (409/422 `DUPLICATE_EDGE_COUPLE`).
3. **Référence = saut sans retour** (tail call) vers le début du graphe cible ; pas d'arête sortante.
   Un sous-graphe réutilisé a donc UNE seule suite pour tous ses appelants.
4. **Pas de variables, pas d'arithmétique** : on ne calcule ni base, ni prorata, ni somme de seuils ;
   les seuils se comparent à un nombre fourni (`lte 10000`).
5. **Outputs du chemin lisibles** (« path inputs ») : conditions et `$clé` voient les inputs de
   l'appelant + les outputs texte **non cumulatifs** déjà émis (y compris par le nœud courant pour ses
   propres arêtes, et à travers les références). L'input de l'appelant gagne sur un output de même clé.
   Un output plus tardif remplace le précédent. Cumulatifs et localisés : **non lisibles**. La valeur
   lue est brute (`tax_rate = FR` se lit `FR`, l'adaptateur n'intervient qu'en sortie).
6. **Outputs d'un nœud résolus dans l'ordre** : un `$clé` peut lire un output **précédent** du même
   nœud ; une référence vers un output suivant (ou soi-même) reste non résolue et **retient tout le nœud**
   (aucun de ses outputs n'est émis, la clé part dans `required`).
7. **Cumulatifs dédoublonnés** : une valeur déjà présente n'est pas ajoutée (texte comparé après résolution ;
   localisé par langue), à sa première position.
8. **Macros pays** : `europe` = membre UE selon la table `country` — **FR et MC sont `europe`** ;
   GP/MQ/RE/GF/YT ne le sont pas (`dom` couvre GP/MQ/RE/YT). Les Canaries ont leur code (`IC`).
9. **Adaptateur `tax_rate`** : une valeur numérique sort telle quelle ; un code pays est converti en
   taux normal de ce pays à `sale_date`.
10. **Mode strict (par workspace, `strictInputs`)** : un input absent se résout, seulement quand une
    condition ou un `$` en a besoin, par : valeur de l'appelant → output déjà sur le chemin → `defaultValue`
    du catalogue (rapportée dans `defaulted`) → si la clé est un **output** du catalogue (marqueur) : absente
    = condition fausse, jamais demandée → sinon **inconnue**. Une arête inconnue rencontrée avant une arête
    qui correspond **arrête le parcours sur ce nœud** (ni les arêtes suivantes ni le repli ne sont essayés)
    et la clé est demandée. Une arête `all` avec une condition connue fausse, ou `any` avec une vraie, est
    décidée malgré l'inconnue. Un nœud qui n'a qu'un repli ne bloque jamais.
    **Mode souple** (défaut, `tva-france`) : input absent = condition fausse, le repli est pris en silence.
11. Compilation : nœuds partagés (un nœud atteint par plusieurs chemins, un graphe référencé partout =
    coût unique) ; recompilation d'un workspace ~2 s ; chaque import republie et recompile.

## Démarrage local

Si le projet ouvert a un `.claude/launch.json` : `taxelia-api` (port 8088, Mongo local `taxelia`, profil
`local`) et `taxelia-graph-editor` (port 8089). Sinon, demander l'URL de l'API à l'utilisateur. Démarrer/arrêter avec les outils de preview
(`preview_start`/`preview_stop`), pas avec Bash. L'éditeur s'ouvre sur un workspace par
`http://localhost:8089/?ws=<id>`.
