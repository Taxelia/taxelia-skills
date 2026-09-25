---
name: search
description: Interroge un graphe de décision Taxelia via l'API /search et répond uniquement à partir des retours de l'API (jamais d'une source extérieure ni de connaissances propres), en affichant le JSON de chaque requête et de chaque réponse ; pose une à une les questions que le moteur renvoie (inputs requis) jusqu'à une réponse complète. À utiliser quand l'utilisateur veut « chercher dans le graphe », « interroger Taxelia », connaître un taux, une mention de facture, un redevable… pour une opération, ou dit « /taxelia:search ».
---

# Recherche dans un graphe Taxelia (/search)

Tu réponds à une question en interrogeant le moteur Taxelia. **Tout ce que tu affirmes vient des réponses de
l'API.** `<skill>` = le répertoire de base de ce skill (indiqué au lancement) ; l'outil est
`python3 <skill>/scripts/tsearch.py` (voir son en-tête).

## Règles absolues

1. **Seule source : l'API.** N'utilise ni tes connaissances fiscales, ni le web, ni un autre fichier. Pas de
   commentaire juridique, pas d'article cité qui ne figure pas dans la réponse (`legal_basis`, `info`,
   descriptions du catalogue lues via l'API). Si l'API ne répond pas à la question, dis-le : « le graphe ne
   produit pas cette information » — ne complète pas.
2. **Aucune hypothèse.** Un input n'est envoyé que si l'utilisateur l'a énoncé explicitement, ou l'a donné en
   réponse à une question. Tout le reste passe par les questions que le moteur renvoie (`inputs.required`).
   Les seules hypothèses admises sont celles que le moteur applique lui-même (`inputs.defaulted`) : montre-les.
3. **Valeurs du catalogue uniquement.** Un fait de l'utilisateur est traduit en une valeur qui existe dans
   le catalogue (option d'un select, code pays ISO pour un champ `location`, `true`/`false`, nombre, date
   `AAAA-MM-JJ`). Si la correspondance n'est pas évidente, demande à l'utilisateur de choisir parmi les options.
4. **Toujours afficher le JSON** de chaque requête et de chaque réponse, en entier (bloc ```json), avant ton
   interprétation.
5. **Jamais de marqueur forcé** : n'envoie pas en input une clé de sortie du catalogue (outputs), sauf si
   l'utilisateur le demande expressément.

## Déroulé

1. **Préparation**
   - API : `https://taxelia.bizyness.fr` par défaut (`--api <url>` seulement si l'utilisateur en donne une autre).
   - Clé : lire le catalogue et la liste des workspaces demande une clé (lecture suffit). Si
     `~/.config/taxelia/apikey` n'existe pas, demande-la à l'utilisateur, écris-la dans ce fichier (chmod 600),
     ne l'affiche jamais.
   - Workspace : si l'utilisateur ne l'a pas nommé, `tsearch.py workspaces` puis demande lequel
     (`AskUserQuestion`). Le graphe interrogé est son **graphe principal** (le seul graphe nommé). Si le
     workspace a plusieurs graphes nommés (`tsearch.py main <ws>` les liste), demande lequel interroger et
     passe `--tree <nom>`.
2. **Ce qu'on cherche** : identifie la ou les sorties qui répondent à la question parmi `tsearch.py outputs <ws>`
   (ex. taux → `tax_rate`, mention de facture → `invoice_mention`) et passe-les en `--outputs` : la réponse
   dira `result.complete` et `missingOutputs`.
3. **Ce que j'ai compris** : affiche un tableau « fait énoncé → input → valeur » pour les seuls faits
   explicites de la question. Pour trouver la bonne clé et la bonne valeur : `tsearch.py find <ws> "<mots>"`
   et `tsearch.py keys <ws> <clé>` (descriptions et options). N'ajoute rien d'autre.
4. **Boucle**
   - `tsearch.py run <ws> '<inputs json>' --outputs <sorties>` → affiche requête et réponse JSON.
   - Si `inputs.required` n'est pas vide : `run` affiche après la réponse l'entrée catalogue de ces clés
     (section `CATALOG OF REQUIRED INPUTS`, lue elle aussi via l'API) ; pose les
     questions à l'utilisateur, **une clé à la fois**, avec le libellé, la description et les valeurs
     possibles tels que l'API les donne (`AskUserQuestion` quand il y a 2 à 4 valeurs ; sinon liste les
     valeurs dans ton message et demande). Si l'utilisateur ne sait pas, arrête et présente la réponse
     partielle (`complete: false`).
   - Ajoute la réponse aux inputs et relance. Continue jusqu'à `inputs.required` vide.
5. **Réponse finale**
   - La réponse à la question, reprise **telle que l'API la donne** (ex. `tax_rate`, `invoice_mention`), puis
     les autres sorties utiles, `legal_basis` et `info` cités tels quels.
   - `result` (`complete`, `missingOutputs`) et la liste `inputs.defaulted` (hypothèses faites par le moteur).
   - Le JSON final de la requête et de la réponse.
   - Si `complete` est faux alors que `required` est vide, dis que le graphe ne produit pas la sortie demandée
     pour ce cas (sans l'inventer).
