# Skills Taxelia

Marketplace Claude Code (`taxelia-skills`) contenant le plugin `taxelia`. Chaque skill est un
sous-dossier de `plugins/taxelia/skills/<nom-du-skill>/` avec son `SKILL.md`.

| Skill | Commande | Rôle |
|---|---|---|
| `legifrance-ingest` | `/taxelia:legifrance-ingest <url>` | Ingère une page Légifrance et la transforme en graphes de décision Taxelia via l'API (extraction, classement des articles, conception validée, construction testée). |

## Installer

Dans Claude Code (ou en ligne de commande avec `claude plugin …`) :

```
/plugin marketplace add <chemin local ou URL git de ce dépôt>
/plugin install taxelia@taxelia-skills
```

Mettre à jour après un `git pull` (ou quand le dépôt distant a changé) :

```
/plugin marketplace update taxelia-skills
```

## Ajouter un skill

1. Créer `plugins/taxelia/skills/<nom>/SKILL.md` (frontmatter `name` = `<nom>`, `description` qui dit
   quand l'utiliser), avec ses `references/` et `scripts/` éventuels.
2. Chemins : relatifs au répertoire du skill (Claude le connaît au lancement), jamais de chemin absolu
   propre à une machine.
3. Incrémenter `version` dans `plugins/taxelia/.claude-plugin/plugin.json`, committer, puis
   `/plugin marketplace update taxelia-skills` sur chaque machine.
