# Scripts du skill legifrance-ingest

Tous les scripts Python lisent `ingest.json` du répertoire de travail (`--work <dir>`, variable
`INGEST_WORK`, ou répertoire courant / parents) et la clé dans `<work>/.apikey` (jamais affichée).

```json
{"api": "http://localhost:8088", "workspace": "cibs-2027", "primary_id": "cibs_2027_principal", "primary_name": "cibs_2027"}
```

| Script | Rôle |
|---|---|
| `extract_legifrance.js` | à exécuter dans la page Légifrance (`javascript_tool`) : texte intégral avec tableaux en markdown dans `window.__lf` |
| `split_lots.py` | `--stats` (articles, en-têtes, trous de numérotation) ; `--lots <dir>` découpe par chapitres |
| `coverage.py <work>` | vérifie que chaque article est classé une fois par les lecteurs (`<work>/out/*.md`) |
| `ws.py` | `list`, `create`, `strict on|off`, `export`, `graphs`, `refresh` |
| `imp.py <fichiers>` | import dry-run puis réel, catalogue d'abord, graphes par paquets |
| `dsl.py` | DSL des générateurs (`G`, `q`, `r`, `ref`, `e`, `fb`, `cont`, `t`, `lb`, `info`, `inv`, `L`, `dump`, `set_code`) |
| `set_names.py on|off` | pose/retire les noms temporaires `t__<id>` des sous-graphes (depuis l'export) |
| `check_couples.py` | 0 attendu : couples (source, cible) portant plusieurs arêtes |
| `run_scenarios.py <tests>` | rejoue les scénarios (`expect`, `contains`, `absent`, `required`, `not_required`, `defaulted`, `outputs`, `result`) |
| `ask.py '<json>'` | une requête `/search` lisible (démonstration, sonde des questions posées) |

Exemple de générateur (dans `<work>/gen/lot1.py`) :

```python
import sys; sys.path.insert(0, "<skill>/scripts")   # <skill> = répertoire de base du skill
from dsl import G, t, lb, info, L, dump, set_code
set_code("CIBS")
g = G("franchise_en_base", "Franchise en base", "Franchise en base (L. 233-3 à 21).", "fr_start")
g.q("fr_start", "Chiffre d'affaires sous le plafond ?")
g.r("fr_ok", "Franchise applicable", t("exemption_kind", "franchise"), t("tax_rate", "0"), lb("L. 233-9"))
g.ref("fr_next", "exonerations_internationales")
g.e("fr_start", "fr_ok", ("franchise_turnover_prev_year", "lte", "85000"), ("franchise_turnover_current_year", "lte", "93500"),
    name="Sous les plafonds")
g.fb("fr_start", "fr_next", name="Au-dessus")
dump("/…/graphs/franchise_en_base.json", g)
```
