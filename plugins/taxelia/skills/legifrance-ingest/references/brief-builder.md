# Consigne des agents de construction (phase 5) — à copier dans `<work>/brief-builder.md` et compléter

Remplace les `{…}`. Chaque agent de construction reçoit ce fichier + la liste de SES graphes (ids de la
consolidation) + le nom de son rapport. Les agents sont lancés **l'un après l'autre**.

---

# Consigne : construire des graphes dans le workspace `{ws}` (API {api})

Tu construis quelques graphes conçus dans `{work}/consolidation.md`. Uniquement via l'API de
`{work}/ingest.json` ; ne touche à aucun dépôt, à aucun autre workspace. Pas de sous-agent. Noms de
nœuds/arêtes, titres, descriptions et textes de sortie en français correct ; clés en snake_case.
La clé API est dans `{work}/.apikey` : ne l'affiche jamais, ne la recopie nulle part.

## Sources (dans cet ordre)
- Conception (fait foi) : `{work}/consolidation.md` — architecture, **marqueurs**, liste des graphes
  (id, articles, appelants, suite), catalogue, scénarios de ton lot.
- Règles par article : `{work}/out/*.md` (fiches) et le texte `{work}/lots/*.txt`.
- Sémantique moteur et API : `{skill}/references/engine-and-api.md`. Conventions : `{skill}/references/modeling.md`.
- Pièges : `{skill}/references/pitfalls.md` — en particulier P8–P13, P17–P21, P27–P30, P36.
- Rapports des lots précédents : `{work}/reports/*.md` (conventions de marqueurs déjà utilisées).

## Règles
- Id = celui de la consolidation ; `name` = `t__<id>` (temporaire, pour tester) sauf le primaire :
  `{primary_name}`. `title` et `description` (but + articles).
- Chaque décision émet `legal_basis` (cumulatif, ex. « {code} L. 213-151 »).
- Une seule arête par couple (source, cible), repli compris : `match: any` ou `g.cont(...)`.
- Ordre des arêtes = priorité ; cas particulier avant cas général ; France (`in [FR,MC]`) avant `europe`.
- Mode strict : ne jamais tester à un nœud une clé sans objet pour un cas qui l'atteint (garde par
  marqueur ou par fait connu) ; ne jamais donner de valeur par défaut à un fait décisif pour faire taire
  une question.
- `tax_rate` explicite (0 pour exonération / hors champ) selon `modeling.md` §5.
- Un seul graphe principal : `{primary_id}` (nom `{primary_name}`). Tu ne crées pas d'autre graphe nommé.
- Graphes existants (mode mise à jour) : pars de l'export le plus récent, garde les ids, ne supprime rien
  sans accord ; réimporte seulement ce que tu modifies ; `diff_export.py` avant/après dans ton rapport.
- **Avant de créer une clé** : `python3 {skill}/scripts/catalog_search.py "<notion>" "<fait>" "<article>"` ;
  si une clé couvre le besoin, réutilise-la ; **en cas de doute, arrête-toi** et décris les candidats dans
  ton rapport sans créer la clé (le contrôleur demandera confirmation à l'utilisateur).
- Catalogue : déjà importé. Clé ou valeur manquante (après vérification) → ajouter l'entrée COMPLÈTE à
  `{work}/catalog-additions.json`, l'importer seule (`scripts/imp.py`), le signaler.
- Défaut repéré dans un graphe déjà construit : ne le réécris pas ; décris la correction exacte dans ton rapport.

## Procédure
1. Générateur `{work}/gen/<lot>.py` avec `{skill}/scripts/dsl.py` (import via `sys.path`) →
   `{work}/graphs/<id>.json` (ou un fichier pour des graphes qui se référencent entre eux).
2. `python3 {skill}/scripts/imp.py {work}/graphs/<fichier>.json` (dry-run puis import).
3. Scénarios `{work}/tests/<id>.json` (tree `t__<id>`) : ceux de la consolidation + 1–3 par branche.
   Les marqueurs amont peuvent être forcés en input pour isoler le graphe. Attendus = LA LOI.
4. `python3 {skill}/scripts/run_scenarios.py {work}/tests/<id>.json` jusqu'au vert (réimporter après
   chaque correction), puis toute la suite `{work}/tests/*.json` (non-régression) et
   `python3 {skill}/scripts/check_couples.py`.
5. Rapport `{work}/reports/<lot>.md` : graphes (nœuds/arêtes), scénarios (réussis/total), ajouts au
   catalogue, écarts à la conception et pourquoi, doutes juridiques, défauts vus ailleurs.

Réponse finale (≤ 10 lignes) : graphes importés, scénarios, ajouts, écarts, doutes.
