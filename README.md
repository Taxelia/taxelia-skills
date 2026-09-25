# Skills Taxelia

Dépôt : https://github.com/Taxelia/taxelia-skills

Marketplace Claude Code (`taxelia-skills`) contenant le plugin `taxelia`. Chaque skill est un
sous-dossier de `plugins/taxelia/skills/<nom-du-skill>/` avec son `SKILL.md`.

| Skill | Commande | Rôle |
|---|---|---|
| `legifrance-ingest` | `/taxelia:legifrance-ingest <url>` | Ingère une page Légifrance et la transforme en graphes de décision Taxelia via l'API publique `https://taxelia.bizyness.fr` (extraction, classement des articles, conception validée, construction testée). |

## Installer

Dans Claude Code :

```
/plugin marketplace add Taxelia/taxelia-skills
/plugin install taxelia@taxelia-skills
```

En ligne de commande : `claude plugin marketplace add Taxelia/taxelia-skills` puis
`claude plugin install taxelia@taxelia-skills`. L'URL complète
`https://github.com/Taxelia/taxelia-skills.git` fonctionne aussi.

Ouvrir ensuite une nouvelle session : le skill se lance avec `/taxelia:legifrance-ingest <url>`.

Récupérer la dernière version des skills :

```
/plugin marketplace update taxelia-skills
```
