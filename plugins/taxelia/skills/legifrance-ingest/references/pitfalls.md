# Pièges rencontrés (construction de `cibs-2027`, septembre 2026)

Chaque piège : ce qui s'est passé → quoi faire. Cite les numéros dans les consignes aux sous-agents.

## Extraction

- **P1 — Cloudflare.** `curl` et `WebFetch` reçoivent une page « Just a moment… ». → Navigateur intégré
  (`navigate`, puis `javascript_tool` / `get_page_text`). Si la page reste sur « Un instant… /
  Vérification de sécurité en cours » : le panneau du navigateur est probablement masqué (la page ne
  s'affiche pas, la vérification ne se termine pas). Demande à l'utilisateur d'**afficher le panneau** ;
  si une case « Je ne suis pas un robot » apparaît, **c'est à lui de la cocher** (ne jamais résoudre une
  vérification anti-robot). Attends ensuite que `document.title` ne soit plus « Un instant… ».
- **P2 — Tableaux masqués.** Légifrance affiche « Afficher le tableau » à la place des tableaux : une
  extraction texte perd les taux (L. 213-151 et suivants), les plafonds de franchise, etc. 28 tableaux
  manquaient au CIBS. → `scripts/extract_legifrance.js` réinjecte chaque `<table>` en markdown à sa place.
  Dans ces tableaux, une ligne sans colonne « conditions » **hérite** de celle du dessus (cellule fusionnée).
- **P3 — CSP.** Un `fetch` depuis la page vers une autre adresse est bloqué. → Sortir le texte par tranches
  de 40 000 caractères via le retour de `javascript_tool`.
- **P4 — Numéros absents.** Des numéros d'articles n'existent pas (abrogés, jamais créés : L. 213-30,
  L. 213-209…). Ne pas les déclarer « perdus » : compare avec les en-têtes « Articles X à Y ».
- **P5 — Texte modificatif.** Une ordonnance « portant ajustements » contient des articles qui modifient
  d'autres textes (non modélisables) et, en annexe, le code consolidé (la vraie source). Repérer l'annexe
  et les articles de l'ordonnance qui changent des règles (ex. territoires, entrée en vigueur).

## Moteur

- **P6 — Un seul chemin, saut sans retour.** Une référence ne revient jamais : un sous-graphe partagé a
  une seule suite. Pas de « sous-routine ».
- **P7 — Ni variables ni arithmétique.** Pas de calcul de base, prorata, cumul, délai → `HORS_MODELE`
  (+ `info`), ou comparaison d'un nombre fourni à une constante.
- **P8 — Ordre des arêtes = priorité.** Autrefois perdu (HashSet), corrigé : l'ordre du fichier est
  respecté. Mettre le cas particulier avant le cas général.
- **P9 — Macro `europe` inclut FR et MC.** Tester la France (`in [FR,MC]`) AVANT `europe`.
- **P10 — `$clé` d'un même nœud.** Un output ne peut lire qu'un output **précédent** du même nœud ;
  sinon tout le nœud est retenu (rien n'est émis). Ordonner les outputs.
- **P11 — Une arête par couple (source, cible), repli compris.** 131 couples doublés ont dû être
  réécrits ; l'API les refuse désormais (`DUPLICATE_EDGE_COUPLE`). OU simple → `match: any` ;
  sinon nœud de suite. Contrôle : `scripts/check_couples.py`.
- **P12 — Outputs lisibles, avec limites.** Cumulatifs et localisés illisibles ; valeur lue brute.
  Un libellé localisé ne peut pas être testé : doubler par un marqueur texte (ex. `exemption_basis`).
- **P13 — L'appelant gagne.** Un input de l'appelant écrase le marqueur de même clé et **masque ses
  raffinements** ultérieurs (ex. forcer `operation_qualification` cache `livraison_en_chaine`). En
  production, ne rendre forçable que ce qui est prévu ; en test, ne pas forcer le marqueur que le graphe
  testé raffine.
- **P14 — Explosion à la compilation (corrigée).** Chaque chemin était recopié (870 000 nœuds, 17 Go).
  Le moteur partage désormais les nœuds. Si un import redevient très lent ou renvoie 500, mesurer
  `POST /refresh` et le signaler.
- **P15 — Mode souple = suppositions silencieuses.** En mode souple, un input absent rend la condition
  fausse et le repli est pris : une vente de bougie vers l'Allemagne répondait 19 % sans demander le CA de
  ventes à distance. → Tout nouveau modèle en `strictInputs = true`.
- **P16 — Ne pas basculer un workspace en production.** Ses graphes supposent le mode souple ; le
  basculer change des réponses. Demander.
- **P17 — Mode strict = arrêt sur inconnu.** Une arête inconnue avant une arête qui correspond arrête
  le parcours ; les arêtes suivantes et le repli ne sont pas essayés.
- **P18 — Trop de questions sans valeurs par défaut.** Sans défauts, une vente simple posait ~25
  questions d'exclusion. → Défauts pour les situations rares, jamais pour un fait décisif.
- **P19 — Ne jamais cacher un fait décisif derrière un défaut** pour faire taire une question : corriger
  le graphe (garde, ordre).
- **P20 — Questions hors sujet.** 26 graphes demandaient `service_category` pour des biens,
  `goods_category`/`transport` pour des services, l'OSS en B2B… → gardes par `operation_qualification`,
  ou arête du cas courant en premier. Une condition `ne` sur un input absent le fait demander.
- **P21 — `required` et `defaulted`.** En mode strict `required` ne liste que ce qui manque ;
  `defaulted` liste les hypothèses. Tester les deux (`required` / `not_required`).

## Conception

- **P22 — Découper par réutilisation, un seul primaire.** Décision de l'utilisateur. Les sous-graphes
  restent sans nom en production.
- **P23 — Une seule fin de chaîne.** Avec les marqueurs, une fin commune qui lit `exemption_kind` remplace
  cinq fins parallèles (47 → 40 graphes).
- **P24 — Lecture parallèle = synonymes.** 9 lecteurs ont produit 364 clés pour 193 réelles. → Donner un
  vocabulaire commun dans la consigne de lecture, puis fusionner en consolidation (table des renommages).
- **P25 — DOM et « territoire tiers ».** Incohérence entre lots (export vers la Réunion, assurance d'un
  client martiniquais). → Trancher une fois, par un marqueur calculé une fois (localisation) et lu partout.
- **P26 — Codes pays spéciaux.** Monaco = France (L. 112-4-2) ; GF/YT non-territoires de taxation ;
  Canaries `IC` ; Mont Athos, Campione… sans code propre → input dédié. Corse = code `FR` : la distinguer
  par le code postal (20000–20999) du critère de lieu retenu (`place_basis`).

## Import et données

- **P27 — Références.** La cible doit exister (publiée) ou être dans le même fichier : construire du bas
  vers le haut.
- **P28 — Noms temporaires.** Pour tester un sous-graphe il lui faut un nom (`t__<id>`) ; en production
  un seul graphe nommé. `scripts/set_names.py on|off`. Réimporter un graphe seul lui remet son `t__` :
  refaire `off` ensuite.
- **P29 — Gros imports.** Un import de 40 graphes en une transaction a dépassé la durée de vie de
  transaction Mongo (500). → `scripts/imp.py` importe par paquets.
- **P30 — `tax_rate` explicite.** Absence de taux ≠ 0 % pour l'appelant : poser `0` pour toute
  exonération / hors champ (voir `modeling.md` §5).
- **P31 — Outputs demandés.** `outputs: ["tax_rate"]` ne raccourcit pas le parcours (une valeur peut être
  remplacée plus loin) ; `complete` exige `required` vide.
- **P32 — L'import de catalogue écrase.** Une entrée omise n'est pas supprimée, mais une entrée présente
  est remplacée entièrement : un champ omis (`label`, `legalBasis`, `defaultValue`, options) est effacé.
  Toujours partir de l'export et renvoyer l'entrée complète.
- **P33 — Clés sans libellé.** 13 clés du vocabulaire de départ étaient importées sans libellé.
  → Chaque clé a un libellé.
- **P34 — Libellés en double / sans accents.** « Code postal » ×4, « Marqueur » ×12, 171 libellés sans
  accents. → Libellés distincts, accentués, sans point final.
- **P35 — Notes techniques dans les libellés** (« Émis par G36 », « Valeurs : … ») → dans la description.
- **P36 — Attendus = la loi.** Plusieurs lots ont trouvé des défauts parce que les attendus venaient du
  texte, pas de la sortie. Ne jamais aligner un attendu sur la sortie du graphe.
- **P37 — Nœuds de référence sans nom.** L'API les accepte ; l'éditeur les affiche par leur cible
  (« → titre »). Ne pas leur inventer de nom.
- **P38 — Pas de promotion de bac à sable.** Un workspace dupliqué ne peut pas être réimporté dans
  l'original (ids de graphes d'un autre workspace refusés). Travailler dans le workspace cible, avec une
  sauvegarde d'export.

## Environnement

- **P39 — Clé API.** Ne pas la lire en base (refusé par la politique de permissions) : la demander.
  Ne jamais l'afficher ni l'écrire dans un dépôt ; `<work>/.apikey` en chmod 600.
- **P40 — API partagée.** `https://taxelia.bizyness.fr` sert des données partagées : annoncer et faire
  valider chaque écriture (création de workspace, import de catalogue, import de graphes, bascule du
  mode strict) ; ne jamais toucher à un workspace autre que celui convenu ; exporter avant de modifier un
  workspace existant.
- **P41 — Comportement inattendu du moteur.** Si une règle ne peut pas s'exprimer, ou si le moteur se
  comporte autrement que `engine-and-api.md`, ne contourne pas en silence : décris le cas à
  l'utilisateur (une évolution du moteur est hors du périmètre du skill).
- **P42 — Sous-agents.** Lecture : en parallèle. Construction : **séquentielle** (API partagée). Donner
  à chacun les chemins de fichiers, pas le contenu ; exiger un rapport écrit et une réponse courte.
