#!/usr/bin/env python3
"""Check that every article of the extracted text is classified exactly once by the reading agents.

  coverage.py <work>     reads <work>/source.txt and <work>/out/*.md (coverage tables:
                         | Article | Catégorie | Bloc | Résumé | Inputs | Outputs |), writes <work>/coverage.json
Prints counts per category and per block, articles missing or classified twice. The category cell may carry a
parenthesis after the category (e.g. "HORS_MODELE (calcul)").
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from split_lots import articles  # noqa: E402

CAT = re.compile(r"[\*`\s]*(R[ÈE]GLE|D[ÉE]FINITION|HORS_MOD[ÈE]LE|RENVOI)", re.I)
ARTICLE_CELL = re.compile(r"^(L\.?\s?|R\.?\s?|D\.?\s?)?(\d+(?:-\d+)*)")


def norm_cat(c):
    return c.upper().replace("È", "E").replace("É", "E")


def main(work):
    text = open(os.path.join(work, "source.txt")).read()
    expected = [a for _, a in articles(text)]
    rows = {}
    for path in sorted(glob.glob(os.path.join(work, "out", "*.md"))):
        for line in open(path):
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            m = ARTICLE_CELL.match(cells[0].replace(" ", " ").strip("*` "))
            c = CAT.match(cells[1])
            if not (m and c):
                continue
            art = (m.group(1) or "").replace(" ", "").replace(".", "") + m.group(2)
            rows.setdefault(art, []).append({"lot": os.path.basename(path), "cat": norm_cat(c.group(1)),
                                             "bloc": cells[2], "resume": cells[3], "inputs": cells[4], "outputs": cells[5]})
    json.dump(rows, open(os.path.join(work, "coverage.json"), "w"), ensure_ascii=False, indent=1)
    cats = collections.Counter(v[0]["cat"] for v in rows.values())
    print("categories:", dict(cats), "total", sum(cats.values()))
    missing = [a for a in expected if a not in rows]
    extra = [a for a in rows if a not in set(expected)]
    twice = [a for a, v in rows.items() if len(v) > 1]
    print("missing:", len(missing), missing[:40])
    print("classified but not in the text (amended articles of another book?):", extra[:20])
    print("classified twice:", twice[:20])
    blocs = collections.Counter(v[0]["bloc"] for v in rows.values() if v[0]["cat"] == "REGLE")
    print("\nrule blocks:")
    for b, n in blocs.most_common():
        print(f"  {n:4} {b}")
    return 1 if missing or twice else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
