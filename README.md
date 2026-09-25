# Skills Taxelia

Dépôt : https://github.com/Taxelia/taxelia-skills

Marketplace Claude Code (`taxelia-skills`) contenant le plugin `taxelia`. Chaque skill est un
sous-dossier de `plugins/taxelia/skills/<nom-du-skill>/` avec son `SKILL.md`.

| Skill | Commande | Rôle |
|---|---|---|
| `legifrance-ingest` | `/taxelia:legifrance-ingest <url>` | Ingère une page Légifrance et la transforme en graphes de décision Taxelia via l'API publique `https://taxelia.bizyness.fr` (extraction, classement des articles, conception validée, construction testée). |
| `search` | `/taxelia:search <question>` | Répond à une question en interrogeant `/search` sur le graphe principal d'un workspace : faits explicites seulement, questions posées une à une pour les inputs requis par le moteur, JSON de chaque requête et réponse affiché, aucune source hors API. Demande une clé API au premier usage (stockée dans `~/.config/taxelia/apikey`). |

## Installer

Dans Claude Code :

```
/plugin marketplace add Taxelia/taxelia-skills
/plugin install taxelia@taxelia-skills
```

En ligne de commande : `claude plugin marketplace add Taxelia/taxelia-skills` puis
`claude plugin install taxelia@taxelia-skills`. L'URL complète
`https://github.com/Taxelia/taxelia-skills.git` fonctionne aussi.

Ouvrir ensuite une nouvelle session : les skills se lancent avec `/taxelia:legifrance-ingest <url>` et
`/taxelia:search <question>`.

Récupérer la dernière version des skills :

```
/plugin marketplace update taxelia-skills
```
