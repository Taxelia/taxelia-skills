# Skills Taxelia

Dépôt : https://github.com/Taxelia/taxelia-skills

Marketplace Claude Code (`taxelia-skills`) contenant le plugin `taxelia`. Chaque skill est un
sous-dossier de `plugins/taxelia/skills/<nom-du-skill>/` avec son `SKILL.md`.

| Skill | Commande | Rôle |
|---|---|---|
| `legifrance-ingest` | `/taxelia:legifrance-ingest <url>` | Ingère une page Légifrance et la transforme en graphes de décision Taxelia via l'API (extraction, classement des articles, conception validée, construction testée). |

## Installer

Dans Claude Code :

```
/plugin marketplace add Taxelia/taxelia-skills
/plugin install taxelia@taxelia-skills
```

En ligne de commande : `claude plugin marketplace add Taxelia/taxelia-skills` puis
`claude plugin install taxelia@taxelia-skills`. L'URL complète
`https://github.com/Taxelia/taxelia-skills.git` fonctionne aussi ; pour tester des modifications non
poussées, on peut ajouter le chemin local d'un clone à la place.

Ouvrir ensuite une nouvelle session : le skill se lance avec `/taxelia:legifrance-ingest <url>`.

Mettre à jour après un `git pull` (ou quand le dépôt distant a changé) :

```
/plugin marketplace update taxelia-skills
```

## Ajouter un skill

1. Créer `plugins/taxelia/skills/<nom>/SKILL.md` (frontmatter `name` = `<nom>`, `description` qui dit
   quand l'utiliser), avec ses `references/` et `scripts/` éventuels.
2. Chemins : relatifs au répertoire du skill (Claude le connaît au lancement), jamais de chemin absolu
   propre à une machine.
3. Incrémenter `version` dans `plugins/taxelia/.claude-plugin/plugin.json`, committer et pousser sur
   https://github.com/Taxelia/taxelia-skills, puis `/plugin marketplace update taxelia-skills` sur chaque
   machine.
